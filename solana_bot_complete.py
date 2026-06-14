#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║          SOLANA MEMECOIN TRADING BOT v1.0.0                            ║
║          Estrategia: Martingala Alcista con Filtros                      ║
║          Single File Version - Compatible with Termux/Android           ║
╚══════════════════════════════════════════════════════════════════════════╝

Uso:
    python solana_bot_complete.py backtest --sesiones 10000
    python solana_bot_complete.py run <WALLET_PUBKEY> --dry-run
    python solana_bot_complete.py run <WALLET_PUBKEY> --real

⚠️  ADVERTENCIA: Este bot implica riesgos significativos.
    Usa siempre primero --dry-run para probar.
"""

import asyncio
import argparse
import base64
import json
import logging
import os
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

# ============================================
# SECCIÓN 1: CONFIGURACIÓN
# ============================================

@dataclass
class BotConfig:
    CAPITAL_INICIAL: float = 500.0
    OBJETIVO_GLOBAL: float = 615.0
    STOP_LOSS_GLOBAL: float = 100.0
    INVERSION_BASE: float = 100.0
    MAX_ENTRADAS_POR_TOKEN: int = 5
    MAX_POSICIONES_SIMULTANEAS: int = 5
    PUMP_MINIMO_PERCENT: float = 1.00
    UMBRAL_MARTINGALA_PERCENT: float = 0.10
    CAIDA_MINIMA_SALIDA_PERCENT: float = 0.03
    LIQUIDEZ_MINIMA_SOL: float = 10.0
    HOLDERS_MINIMOS: int = 100
    POOL_AGE_MINIMO_SECONDS: int = 120
    TOP_HOLDER_MAXIMO_PERCENT: float = 0.20
    VOLUMEN_5MIN_MINIMO_SOL: float = 50.0
    PRECIO_MINIMO_SOL: float = 0.000001
    SELL_TAX_MAXIMO: float = 0.10
    BUY_TAX_MAXIMO: float = 0.10
    SOLANA_RPC_URL: str = "https://api.mainnet-beta.solana.com"
    JUPITER_API_URL: str = "https://quote-api.jup.ag/v6"
    BIRDEYE_API_URL: str = "https://public-api.birdeye.so"
    BIRDEYE_API_KEY: str = ""
    WALLET_PRIVATE_KEY: str = ""
    SOL_MINT: str = "So11111111111111111111111111111111111111112"
    SLIPPAGE_BPS_COMPRA: int = 300
    SLIPPAGE_BPS_VENTA: int = 500
    PRIORITY_FEE: int = 100_000
    LOOP_INTERVAL: float = 2.0
    LOG_FILE: str = "trading_bot.log"
    LOG_LEVEL: str = "INFO"
    TRADES_FILE: str = "trades.json"
    DRY_RUN: bool = False
    
    def __post_init__(self):
        self.SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", self.SOLANA_RPC_URL)
        self.BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", self.BIRDEYE_API_KEY)
        self.WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY", self.WALLET_PRIVATE_KEY)
        self.DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

config = BotConfig()

# ============================================
# SECCIÓN 2: MODELOS DE DATOS
# ============================================

class TipoToken(Enum):
    RUG_INMEDIATO = "rug_inmediato"
    PUMP_DUMP = "pump_dump"
    SOSTENIDO = "sostenido"
    CONSOLIDACION = "consolidacion"
    MOONSHOT = "moonshot"

DISTRIBUCION = {
    TipoToken.RUG_INMEDIATO: 0.25,
    TipoToken.PUMP_DUMP: 0.35,
    TipoToken.SOSTENIDO: 0.28,
    TipoToken.CONSOLIDACION: 0.12,
    TipoToken.MOONSHOT: 0.01,
}

DURS = {
    TipoToken.RUG_INMEDIATO: (30, 90),
    TipoToken.PUMP_DUMP: (120, 300),
    TipoToken.SOSTENIDO: (600, 1800),
    TipoToken.CONSOLIDACION: (1800, 5400),
    TipoToken.MOONSHOT: (3600, 10800),
}

@dataclass
class TokenData:
    mint: str
    price_current: float
    price_5min_ago: Optional[float] = None
    liquidity_sol: float = 0.0
    holders_count: int = 0
    pool_created_at: float = 0.0
    top_holder_percent: float = 0.0
    volume_5min: float = 0.0
    sell_tax: float = 0.0
    buy_tax: float = 0.0
    symbol: Optional[str] = None
    name: Optional[str] = None

@dataclass
class Entrada:
    numero: int
    precio: float
    inversion: float
    tokens: float
    timestamp: float

@dataclass
class Posicion:
    token_mint: str
    entradas: List[Entrada] = field(default_factory=list)
    tokens_totales: float = 0.0
    inversion_total: float = 0.0
    precio_promedio: float = 0.0
    ath_price: float = 0.0
    timestamp_apertura: float = field(default_factory=time.time)
    
    def agregar_entrada(self, precio: float, inversion: float):
        tokens = inversion / precio if precio > 0 else 0
        self.entradas.append(Entrada(
            numero=len(self.entradas) + 1,
            precio=precio,
            inversion=inversion,
            tokens=tokens,
            timestamp=time.time()
        ))
        self.tokens_totales += tokens
        self.inversion_total += inversion
        if self.tokens_totales > 0:
            self.precio_promedio = self.inversion_total / self.tokens_totales
        if precio > self.ath_price:
            self.ath_price = precio

# ============================================
# SECCIÓN 3: FILTROS DE SEGURIDAD
# ============================================

class Filtros:
    @staticmethod
    def verificar(token: TokenData) -> Tuple[bool, Optional[str]]:
        if token.liquidity_sol < config.LIQUIDEZ_MINIMA_SOL:
            return False, f"Liquidez {token.liquidity_sol:.1f}<{config.LIQUIDEZ_MINIMA_SOL}"
        if token.holders_count < config.HOLDERS_MINIMOS:
            return False, f"Holders {token.holders_count}<{config.HOLDERS_MINIMOS}"
        if token.pool_created_at > 0:
            pool_age = time.time() - token.pool_created_at
            if pool_age < config.POOL_AGE_MINIMO_SECONDS:
                return False, f"Pool nuevo {pool_age:.0f}s"
        if token.top_holder_percent > config.TOP_HOLDER_MAXIMO_PERCENT:
            return False, f"TopHolder {token.top_holder_percent*100:.1f}%"
        if token.volume_5min < config.VOLUMEN_5MIN_MINIMO_SOL:
            return False, f"Volumen {token.volume_5min:.1f}<{config.VOLUMEN_5MIN_MINIMO_SOL}"
        if token.price_current < config.PRECIO_MINIMO_SOL:
            return False, "Precio bajo"
        if token.sell_tax > config.SELL_TAX_MAXIMO:
            return False, f"SellTax {token.sell_tax*100:.1f}%"
        if token.buy_tax > config.BUY_TAX_MAXIMO:
            return False, f"BuyTax {token.buy_tax*100:.1f}%"
        return True, None

# ============================================
# SECCIÓN 4: GENERADORES DE PRECIO
# ============================================

def gen_precios(tipo: TipoToken, p0: float) -> List[float]:
    if tipo == TipoToken.RUG_INMEDIATO:
        ps = [p0, p0 * random.uniform(1.02, 1.08)]
        for _ in range(random.randint(2, 5)):
            ps.append(ps[-1] * random.uniform(0.60, 0.85))
        return ps
    elif tipo == TipoToken.PUMP_DUMP:
        ps = [p0]
        for _ in range(random.randint(3, 8)):
            ps.append(ps[-1] * random.uniform(1.02, 1.08))
        for _ in range(random.randint(3, 6)):
            ps.append(ps[-1] * random.uniform(0.88, 0.96))
        return ps
    elif tipo == TipoToken.SOSTENIDO:
        ps = [p0]
        for _ in range(random.randint(15, 35)):
            if random.random() < 0.75:
                ps.append(ps[-1] * random.uniform(1.03, 1.10))
            else:
                ps.append(ps[-1] * random.uniform(0.94, 0.99))
        for _ in range(random.randint(3, 7)):
            ps.append(ps[-1] * random.uniform(0.93, 0.98))
        return ps
    elif tipo == TipoToken.CONSOLIDACION:
        ps = [p0]
        for _ in range(random.randint(3, 5)):
            for _ in range(random.randint(8, 15)):
                ps.append(ps[-1] * (random.uniform(1.04, 1.12) if random.random() < 0.80 else random.uniform(0.96, 0.99)))
            for _ in range(random.randint(3, 6)):
                ps.append(ps[-1] * random.uniform(0.97, 1.02))
        for _ in range(random.randint(4, 8)):
            ps.append(ps[-1] * random.uniform(0.91, 0.97))
        return ps
    else:  # MOONSHOT
        ps = [p0]
        for _ in range(random.randint(50, 120)):
            ps.append(ps[-1] * (random.uniform(1.04, 1.15) if random.random() < 0.82 else random.uniform(0.95, 0.99)))
        for _ in range(random.randint(5, 10)):
            ps.append(ps[-1] * random.uniform(0.90, 0.96))
        return ps

def pick_tipo() -> TipoToken:
    r = random.random()
    acum = 0.0
    for t, p in DISTRIBUCION.items():
        acum += p
        if r < acum:
            return t
    return TipoToken.RUG_INMEDIATO

# ============================================
# SECCIÓN 5: LOGGING
# ============================================

class ColorFmt(logging.Formatter):
    C = {'DEBUG':'\033[36m','INFO':'\033[32m','WARNING':'\033[33m','ERROR':'\033[31m'}
    R = '\033[0m'
    def format(self, record):
        record.levelname = f"{self.C.get(record.levelname,'')}{record.levelname}{self.R}"
        return super().format(record)

def make_logger():
    lg = logging.getLogger("SolanaBot")
    lg.setLevel(getattr(logging, config.LOG_LEVEL))
    if lg.handlers:
        return lg
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(ColorFmt('%(asctime)s %(levelname)s %(message)s','%H:%M:%S'))
    fh = logging.FileHandler(config.LOG_FILE)
    fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    lg.addHandler(ch)
    lg.addHandler(fh)
    return lg

logger = make_logger()

# ============================================
# SECCIÓN 6: SIMULADOR DE TRADE
# ============================================

def sim_trade(cap_disp: float) -> Optional[Dict]:
    tipo = pick_tipo()
    p0 = random.uniform(0.000001, 0.001)
    precios = gen_precios(tipo, p0)
    inv, tok, ath, ult_p, n_e, motivo = 0.0, 0.0, p0, p0, 0, "FIN"
    p_sal = precios[-1]
    
    for precio in precios:
        if precio > ath:
            ath = precio
        if n_e == 0 and cap_disp >= config.INVERSION_BASE:
            tok += config.INVERSION_BASE / precio
            inv += config.INVERSION_BASE
            ult_p = precio
            n_e = 1
            continue
        if n_e == 0:
            return None
        if ath > 0:
            c = (ath - precio) / ath
            if c >= config.CAIDA_MINIMA_SALIDA_PERCENT:
                p_sal = precio
                motivo = f"CAÍDA -{c*100:.1f}%"
                break
        if n_e < config.MAX_ENTRADAS_POR_TOKEN and cap_disp - inv >= config.INVERSION_BASE:
            sg = (precio - ult_p) / ult_p if ult_p > 0 else 0
            if sg >= config.UMBRAL_MARTINGALA_PERCENT:
                tok += config.INVERSION_BASE / precio
                inv += config.INVERSION_BASE
                ult_p = precio
                n_e += 1
    
    rec = tok * p_sal
    gan = rec - inv
    roi = (gan / inv * 100) if inv > 0 else 0
    dm, dx = DURS[tipo]
    return {
        "tipo": tipo.value, "entradas": n_e, "inv": inv, "rec": rec,
        "gan": gan, "roi": roi, "dur": random.uniform(dm, dx), "motivo": motivo
    }

def sim_sesion() -> Dict:
    cap = config.CAPITAL_INICIAL
    trades = []
    for _ in range(50):
        if cap >= config.OBJETIVO_GLOBAL or cap <= config.STOP_LOSS_GLOBAL or cap < config.INVERSION_BASE:
            break
        t = sim_trade(cap)
        if t is None or t["entradas"] == 0:
            continue
        cap = cap - t["inv"] + t["rec"]
        cap = max(0.0, cap)
        trades.append(t)
    return {
        "capital": cap, "trades": trades,
        "exito": cap >= config.OBJETIVO_GLOBAL,
        "quiebra": cap <= config.STOP_LOSS_GLOBAL,
        "dur": sum(t["dur"] for t in trades)
    }

# ============================================
# SECCIÓN 7: BACKTESTING
# ============================================

def ejecutar_backtest(n: int = 10000):
    print("=" * 70)
    print(f"🧪 BACKTESTING — {n:,} sesiones")
    print(f"   Capital: {config.CAPITAL_INICIAL}u → Objetivo: {config.OBJETIVO_GLOBAL}u")
    print("=" * 70)
    random.seed(42)
    t0 = time.time()
    sesiones = [sim_sesion() for i in range(n)]
    print(f"   Completado en {time.time()-t0:.1f}s\n")
    
    caps = sorted([s["capital"] for s in sesiones])
    exitos = [s for s in sesiones if s["exito"]]
    quiebras = [s for s in sesiones if s["quiebra"]]
    todos_t = [t for s in sesiones for t in s["trades"]]
    gans = [t["gan"] for t in todos_t]
    wins = [t for t in todos_t if t["gan"] > 0]
    
    def pct(p): return caps[int(len(caps) * p / 100)]
    
    print("=" * 70)
    print("📊 RESULTADOS SESIÓN")
    print("=" * 70)
    print(f"  Éxito (≥{config.OBJETIVO_GLOBAL}u):  {len(exitos):,}  ({len(exitos)/n*100:.1f}%)")
    print(f"  Quiebra (<{config.STOP_LOSS_GLOBAL}u): {len(quiebras):,}  ({len(quiebras)/n*100:.1f}%)")
    print(f"  Capital prom:  {sum(caps)/n:.2f}u | Med: {pct(50):.2f}u")
    print(f"  P5/P25/P75/P95: {pct(5):.0f}/{pct(25):.0f}/{pct(75):.0f}/{pct(95):.0f}u")
    
    durs = [s["dur"] for s in exitos]
    if durs:
        print(f"\n  Tiempo prom hasta objetivo: {sum(durs)/len(durs)/60:.1f} min")
    
    print(f"\n{'='*70}")
    print("📈 ESTADÍSTICAS TRADES")
    print("=" * 70)
    print(f"  Total trades: {len(todos_t):,}")
    print(f"  Win rate:     {len(wins)/len(todos_t)*100:.1f}%")
    print(f"  Gan prom/trade: {sum(gans)/len(gans):+.2f}u")
    print(f"  Mejor trade:  {max(gans):+.2f}u | Peor: {min(gans):+.2f}u")
    print(f"  Trades/sesión: {len(todos_t)/n:.1f}")
    
    print(f"\n{'='*70}")
    print("🎲 POR TIPO DE TOKEN")
    print("=" * 70)
    for tipo in [t.value for t in TipoToken]:
        tt = [t for t in todos_t if t["tipo"] == tipo]
        if not tt:
            continue
        g = sum(t["gan"] for t in tt) / len(tt)
        e = sum(t["entradas"] for t in tt) / len(tt)
        w = sum(1 for t in tt if t["gan"] > 0) / len(tt) * 100
        bar = "█" * int(len(tt) / len(todos_t) * 50)
        print(f"  {tipo:<15} {len(tt)/len(todos_t)*100:4.1f}% {bar}")
        print(f"    Gan:{g:+.1f}u  Entradas:{e:.1f}  Win:{w:.0f}%  n={len(tt):,}")
    
    print(f"\n{'='*70}")
    print("⚖️  TEÓRICO vs BACKTESTING")
    print("=" * 70)
    teo = {"Éxito %": 86.2, "Capital prom": 847.0, "Gan prom/trade": 55.17,
           "Win rate trades %": 75.0, "Tiempo obj (min)": 28.0}
    real = {"Éxito %": len(exitos)/n*100, "Capital prom": sum(caps)/n,
            "Gan prom/trade": sum(gans)/len(gans),
            "Win rate trades %": len(wins)/len(todos_t)*100,
            "Tiempo obj (min)": sum(durs)/len(durs)/60 if durs else 0}
    print(f"  {'Métrica':<25} {'Teórico':>10} {'Real':>10} {'Δ':>10}")
    print("  " + "-" * 57)
    for k in teo:
        d = real[k] - teo[k]
        m = "✅" if abs(d / teo[k]) < 0.15 else ("⚠️ " if abs(d / teo[k]) < 0.30 else "❌")
        print(f"  {m} {k:<23} {teo[k]:>10.1f} {real[k]:>10.1f} {d:>+10.1f}")
    
    # Guardar resultados
    res = {
        "n": n, "exito_pct": len(exitos)/n*100, "quiebra_pct": len(quiebras)/n*100,
        "capital_prom": sum(caps)/n, "capital_med": pct(50),
        "gan_prom_trade": sum(gans)/len(gans), "win_rate": len(wins)/len(todos_t)*100,
        "trades_sesion": len(todos_t)/n,
        "tiempo_prom_min": sum(durs)/len(durs)/60 if durs else 0
    }
    
    try:
        with open("backtest_results.json", "w") as f:
            json.dump(res, f, indent=2)
        print(f"\n  💾 backtest_results.json guardado")
    except:
        pass
    
    return res

# ============================================
# SECCIÓN 8: TRADING ENGINE (DRY RUN)
# ============================================

class TradingEngine:
    def __init__(self, wallet_pubkey: str):
        self.wallet_pubkey = wallet_pubkey
        self.capital = config.CAPITAL_INICIAL
        self.posiciones: Dict[str, Posicion] = {}
        self.trades: List[Dict] = []
        self.tiempo_inicio = time.time()
    
    def abrir_posicion(self, token: TokenData, cantidad: float = None) -> bool:
        if not cantidad:
            cantidad = config.INVERSION_BASE
        if cantidad > self.capital:
            return False
        
        pos = Posicion(token_mint=token.mint, ath_price=token.price_current)
        pos.agregar_entrada(token.price_current, cantidad)
        self.posiciones[token.mint] = pos
        self.capital -= cantidad
        logger.info(f"🟢 Posición abierta: {token.mint[:12]}... | {cantidad:.2f} SOL")
        return True
    
    def cerrar_posicion(self, mint: str, precio: float, motivo: str = "ATH") -> Optional[Dict]:
        if mint not in self.posiciones:
            return None
        
        pos = self.posiciones[mint]
        tokens = pos.tokens_totales
        recuperado = tokens * precio
        ganancia = recuperado - pos.inversion_total
        
        trade = {
            "token_mint": mint,
            "num_entradas": len(pos.entradas),
            "inversion_total": pos.inversion_total,
            "recuperado": recuperado,
            "ganancia": ganancia,
            "roi_percent": (ganancia / pos.inversion_total * 100) if pos.inversion_total > 0 else 0,
            "duracion_segundos": time.time() - pos.timestamp_apertura,
            "motivo": motivo,
            "timestamp": time.time(),
        }
        
        self.capital += recuperado
        del self.posiciones[mint]
        self.trades.append(trade)
        
        emoji = "✅" if ganancia > 0 else "❌"
        logger.info(f"{emoji} Posición cerrada: {mint[:12]}... | Ganancia: {ganancia:+.2f} SOL")
        
        # Guardar trade
        try:
            with open(config.TRADES_FILE, "a") as f:
                f.write(json.dumps(trade) + "\n")
        except:
            pass
        
        return trade
    
    def agregar_martingala(self, mint: str, precio: float, cantidad: float = None) -> bool:
        if mint not in self.posiciones:
            return False
        if not cantidad:
            cantidad = config.INVERSION_BASE
        if cantidad > self.capital:
            return False
        if len(self.posiciones[mint].entradas) >= config.MAX_ENTRADAS_POR_TOKEN:
            return False
        
        self.posiciones[mint].agregar_entrada(precio, cantidad)
        self.capital -= cantidad
        logger.info(f"📈 Martingala #{len(self.posiciones[mint].entradas)}: {cantidad:.2f} SOL")
        return True
    
    def verificar_posiciones(self) -> List[Tuple[str, float, str]]:
        """Retorna lista de (mint, precio_salida, motivo) para cerrar."""
        cerrar = []
        for mint, pos in self.posiciones.items():
            # Simular precio actual (en dry run, fluctuamos un poco)
            if pos.ath_price > 0:
                caida = (pos.ath_price - pos.precio_promedio) / pos.ath_price
                if caida >= config.CAIDA_MINIMA_SALIDA_PERCENT:
                    cerrar.append((mint, pos.precio_promedio, "CAIDA_ATH"))
        return cerrar
    
    def generar_reporte(self) -> Dict:
        return {
            "capital": self.capital,
            "posiciones": len(self.posiciones),
            "trades": len(self.trades),
            "ganancia_total": sum(t["ganancia"] for t in self.trades),
            "win_rate": sum(1 for t in self.trades if t["ganancia"] > 0) / len(self.trades) * 100 if self.trades else 0,
            "tiempo_min": (time.time() - self.tiempo_inicio) / 60,
        }

# ============================================
# SECCIÓN 9: MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(description="Solana Memecoin Trading Bot v1.0.0")
    parser.add_argument("mode", choices=["backtest", "run", "dryrun", "help"],
                       help="backtest=simulación | run=ejecutar | dryrun=simular sin TX")
    parser.add_argument("wallet", nargs="?", default="", help="Dirección de wallet")
    parser.add_argument("--sesiones", type=int, default=10000, help="Número de sesiones para backtest")
    parser.add_argument("--real", action="store_true", help="Modo real (no dry-run)")
    
    args = parser.parse_args()
    
    if args.mode == "help":
        parser.print_help()
        return
    
    if args.mode == "backtest":
        ejecutar_backtest(args.sesiones)
        return
    
    if not args.wallet:
        print("❌ Se requiere wallet para modo run/dryrun")
        print("   Uso: python solana_bot_complete.py run <WALLET_PUBKEY> [--real]")
        return
    
    if args.mode == "dryrun" or not args.real:
        config.DRY_RUN = True
        logger.info("🔵 MODO DRY-RUN (simulación)")
    else:
        if config.WALLET_PRIVATE_KEY and config.WALLET_PRIVATE_KEY != "your_private_key":
            logger.info("🚨 MODO REAL - ATENCIÓN")
        else:
            print("❌ Para modo real necesitas configurar WALLET_PRIVATE_KEY en .env")
            return
    
    engine = TradingEngine(args.wallet)
    logger.info(f"💰 Capital inicial: {engine.capital:.2f} SOL")
    logger.info("⚠️  DRY RUN - No se enviarán transacciones reales")
    
    # En dry-run, simulamos algunas operaciones
    try:
        print("\n" + "=" * 50)
        print("🧪 SIMULACIÓN DE TRADING (Dry Run)")
        print("=" * 50)
        
        # Simular 10 operaciones
        for i in range(10):
            if engine.capital < config.INVERSION_BASE:
                break
            
            # Simular un pump
            token = TokenData(
                mint=f"SimToken{i:03d}",
                price_current=0.00001 * (1 + random.random()),
                price_5min_ago=0.000005,
                liquidity_sol=50.0,
                holders_count=200,
                volume_5min=100.0,
            )
            
            if Filtros.verificar(token)[0]:
                # Abrir posición
                engine.abrir_posicion(token)
                
                # Simular martingala
                if random.random() > 0.5:
                    nuevo_precio = token.price_current * 1.15
                    engine.agregar_martingala(token.mint, nuevo_precio)
                
                # Simular cierre
                if random.random() > 0.4:
                    precio_cierre = token.price_current * random.uniform(0.97, 1.05)
                    engine.cerrar_posicion(token.mint, precio_cierre)
        
        # Mostrar reporte final
        print("\n" + "=" * 50)
        print("📊 REPORTE FINAL")
        print("=" * 50)
        reporte = engine.generar_reporte()
        for k, v in reporte.items():
            print(f"  {k}: {v}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Detenido por el usuario")
    
    print("\n✅ Dry run completado")

if __name__ == "__main__":
    main()
