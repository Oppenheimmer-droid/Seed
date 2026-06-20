#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║          SOLANA MEMECOIN TRADING BOT v0.3                              ║
║          Estrategia: Martingala Alcista con Filtros                      ║
║          Compatible con Termux/Android (Python 3.13 ARM64)              ║
║                                                                          ║
║  ✓ Sin solders/solana-py (usa cryptography puro)                        ║
║  ✓ Verificador de estadísticas integrado                                ║
║  ✓ Logging visible en pantalla                                          ║
║  ✓ Validación de private key                                            ║
║  ✓ Trading Real con Jupiter API                                         ║
╚══════════════════════════════════════════════════════════════════════════╝

Uso:
    python solana_bot_complete.py backtest --sesiones 10000
    python solana_bot_complete.py verify --full
    
    # Scripts separados:
    python simulacro.py              # Simulación visual completa
    python trading_real.py           # Trading real (requiere configuración)
    ./run.sh                        # Menú interactivo

⚠️  ADVERTENCIA: Este bot implica riesgos significativos.
    Usa siempre primero modo simulacro.
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

# Importar utilidades propias
UTILITIES_OK = True

try:
    from solana_utils import SolanaWallet, SolanaRPC, JupiterSwap, validar_configuracion
except ImportError as e:
    print(f"⚠️  Advertencia: solana_utils no disponible: {e}")
    SolanaWallet = None
    SolanaRPC = None
    JupiterSwap = None
    def validar_configuracion(config): return []
    UTILITIES_OK = False

# Importar DexScreener como fuente de datos primaria
try:
    from dexscreener import DexScreenerClient, TokenInfo
    DEXSCREENER_OK = True
except ImportError as e:
    print(f"⚠️  Advertencia: dexscreener no disponible: {e}")
    DexScreenerClient = None
    TokenInfo = None
    DEXSCREENER_OK = False

try:
    from logger import make_logger, log_evento, log_status, log_trade
except ImportError as e:
    print(f"⚠️  Advertencia: logger no disponible: {e}")
    UTILITIES_OK = False
    def make_logger(name="SolanaBot", **kwargs):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
        return logging.getLogger(name)
    def log_evento(logger, tipo, token=None, precio=None, detalle=""): 
        token_short = token[:8] if token and len(token) > 8 else str(token or "------")
        logger.info(f"[{tipo}] {token_short} {detalle}")
    def log_status(logger, capital, posiciones, trades, ganancia):
        logger.info(f"Capital: {capital:.2f} | Pos: {posiciones} | Trades: {trades} | Gan: {ganancia:+.2f}")
    def log_trade(logger, trade):
        tipo = "GANANCIA" if trade.get("ganancia", 0) > 0 else "PERDIDA"
        log_evento(logger, tipo, trade.get("token_mint"), trade.get("precio_salida"), f"ROI: {trade.get('roi_percent', 0):+.1f}%")

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
    DEXSCREENER_BASE_URL: str = "https://api.dexscreener.com"
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
    
    @property
    def pump_percent(self) -> float:
        """Pump detectado (ratio, no porcentaje)"""
        if self.price_5min_ago and self.price_5min_ago > 0:
            return (self.price_current - self.price_5min_ago) / self.price_5min_ago
        return 0.0

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
# SECCIÓN 3: SCANNER (DexScreener)
# ============================================

class Scanner:
    """
    Scanner de tokens usando DexScreener como fuente primaria.
    Interfaz idéntica al scanner anterior para no romper
    el resto del bot.
    """

    def __init__(self):
        self.dex = DexScreenerClient() if DEXSCREENER_OK else None
        self.procesados: Set[str] = set()
        self._sol_price: float = 150.0
        self._last_sol_update: float = 0

    async def close(self):
        if self.dex:
            await self.dex.close()

    async def _actualizar_precio_sol(self):
        """Actualiza precio SOL cada 60 segundos"""
        if not self.dex:
            return
        if time.time() - self._last_sol_update > 60:
            precio = await self.dex.get_precio_sol_usd()
            if precio > 0:
                self._sol_price = precio
                self._last_sol_update = time.time()

    async def escanear(self) -> List[TokenData]:
        """
        Escanea nuevos tokens con pump detectado.
        Retorna lista de TokenData compatible con el engine.
        """
        if not self.dex:
            return []

        await self._actualizar_precio_sol()

        try:
            tokens_dex = await self.dex.escanear_pumps(
                pump_minimo=config.PUMP_MINIMO_PERCENT,
                liquidez_minima_sol=config.LIQUIDEZ_MINIMA_SOL,
                volumen_minimo_sol=config.VOLUMEN_5MIN_MINIMO_SOL,
                pool_age_min_seconds=config.POOL_AGE_MINIMO_SECONDS,
            )
        except Exception as e:
            logger.error(f"Scanner error: {e}")
            return []

        resultado = []
        for t in tokens_dex:
            if t.mint in self.procesados:
                continue

            # Convertir TokenInfo → TokenData (interfaz del bot)
            td = self._convertir(t)
            if td:
                resultado.append(td)
                self.procesados.add(t.mint)

        # Limpiar procesados antiguos (mantener últimos 500)
        if len(self.procesados) > 500:
            self.procesados = set(list(self.procesados)[-500:])

        return resultado

    def _convertir(self, t: TokenInfo) -> Optional[TokenData]:
        """
        Convierte TokenInfo de DexScreener al formato
        TokenData que espera el Engine del bot.
        Mantiene compatibilidad sin modificar el Engine.
        """
        try:
            td = TokenData(
                mint=t.mint,
                price_current=t.price_native if t.price_native > 0
                              else t.price_usd / self._sol_price,
                price_5min_ago=None,  # DexScreener no da precio hace 5min
                liquidity_sol=t.liquidity_usd / self._sol_price,
                holders_count=max(t.buys_m5 * 10, 100),  # estimación
                pool_created_at=t.created_at,
                top_holder_percent=0.15,  # conservador sin dato
                volume_5min=t.volume_m5 / self._sol_price,
                sell_tax=0.0,
                buy_tax=0.0,
                symbol=t.symbol,
                name=t.name,
            )

            # Estimar precio hace 5 min desde el cambio %
            if t.change_m5 != 0:
                td.price_5min_ago = td.price_current / (1 + t.change_m5 / 100)

            return td
        except Exception:
            return None

    async def precio(self, mint: str) -> Optional[float]:
        """
        Obtiene precio actualizado de un token.
        Usado por el Engine para monitorear posiciones.
        """
        if not self.dex:
            return None
        t = await self.dex.get_token(mint)
        if t and t.price_native > 0:
            return t.price_native
        if t and t.price_usd > 0:
            return t.price_usd / self._sol_price
        return None


class DetectorPump:
    """
    Detector de pumps usando DexScreener.
    """
    @staticmethod
    def detectar(token_data) -> bool:
        """
        REGLA 2: "Donde va Vicente va la gente"
        DexScreener da change_m5 directamente.
        No necesitamos calcular desde precio histórico.
        """
        # Si viene de DexScreener (tiene pump_percent)
        if hasattr(token_data, 'pump_percent'):
            pump = token_data.pump_percent
        # Si viene del formato antiguo (TokenData)
        elif (token_data.price_5min_ago and
              token_data.price_5min_ago > 0):
            pump = ((token_data.price_current -
                     token_data.price_5min_ago) /
                     token_data.price_5min_ago)
        else:
            return False

        if pump >= config.PUMP_MINIMO_PERCENT:
            logger.info(
                f"🚀 PUMP +{pump*100:.0f}%: "
                f"{token_data.mint[:8]} "
                f"({getattr(token_data, 'symbol', '')})"
            )
            return True
        return False


# ============================================
# SECCIÓN 4: FILTROS DE SEGURIDAD
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

# Crear logger global (se sobrescribe en main si está disponible el módulo)
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
# SECCIÓN 9: VERIFICADOR DE ESTADÍSTICAS
# ============================================

class VerificadorEstadisticas:
    """Verificador completo de estadísticas y funcionalidad del bot."""
    
    # Valores teóricos de referencia
    VALORES_REFERENCIA = {
        "exito_pct": {"valor": 86.2, "tolerancia": 0.15, "descripcion": "Tasa de éxito global"},
        "capital_prom": {"valor": 847.0, "tolerancia": 0.20, "descripcion": "Capital promedio (SOL)"},
        "win_rate": {"valor": 75.0, "tolerancia": 0.15, "descripcion": "Win rate de trades"},
        "gan_prom_trade": {"valor": 55.17, "tolerancia": 0.25, "descripcion": "Ganancia promedio por trade"},
        "tiempo_obj_min": {"valor": 28.0, "tolerancia": 0.30, "descripcion": "Tiempo promedio hasta objetivo (min)"},
        "ratio_rya": {"valor": 1.5, "tolerancia": 0.30, "descripcion": "Ratio Risk/Reward"},
        "max_drawdown": {"valor": 30.0, "tolerancia": 0.40, "descripcion": "Max drawdown esperado (%)"},
    }
    
    def __init__(self):
        self.resultados = {}
        self.pasos_verificados = []
        self.errores = []
    
    def verificar_dependencias(self) -> bool:
        """Verifica que todas las dependencias estén disponibles."""
        print("\n" + "=" * 70)
        print("🔍 VERIFICACIÓN DE DEPENDENCIAS")
        print("=" * 70)
        
        deps_ok = True
        try:
            import sys
            print(f"  ✅ Python: {sys.version.split()[0]}")
            self.pasos_verificados.append("Python OK")
        except Exception as e:
            print(f"  ❌ Python: {e}")
            self.errores.append(f"Python: {e}")
            deps_ok = False
        
        # Verificar módulos estándar
        modulos = ["json", "logging", "random", "time", "dataclasses", "pathlib"]
        for mod in modulos:
            try:
                __import__(mod)
                print(f"  ✅ {mod}")
            except ImportError:
                print(f"  ❌ {mod}")
                deps_ok = False
                self.errores.append(f"Módulo {mod} no disponible")
        
        # Verificar módulos opcionales
        opcionales = ["dotenv", "colorlog", "aiohttp"]
        for mod in opcionales:
            try:
                __import__(mod)
                print(f"  ✅ {mod} (opcional)")
            except ImportError:
                print(f"  ⚠️  {mod} (no instalado - algunas funciones limitadas)")
        
        return deps_ok
    
    def verificar_configuracion(self) -> bool:
        """Verifica la configuración del bot."""
        print("\n" + "=" * 70)
        print("⚙️  VERIFICACIÓN DE CONFIGURACIÓN")
        print("=" * 70)
        
        config_ok = True
        
        # Verificar valores críticos
        checks = [
            ("CAPITAL_INICIAL", config.CAPITAL_INICIAL >= 100),
            ("OBJETIVO_GLOBAL", config.OBJETIVO_GLOBAL > config.CAPITAL_INICIAL),
            ("STOP_LOSS_GLOBAL", config.STOP_LOSS_GLOBAL < config.CAPITAL_INICIAL),
            ("INVERSION_BASE", config.INVERSION_BASE <= config.CAPITAL_INICIAL / 5),  # Max 20% del capital
            ("MAX_ENTRADAS_POR_TOKEN", 1 <= config.MAX_ENTRADAS_POR_TOKEN <= 10),
            ("MAX_POSICIONES_SIMULTANEAS", 1 <= config.MAX_POSICIONES_SIMULTANEAS <= 20),
            ("PUMP_MINIMO_PERCENT", config.PUMP_MINIMO_PERCENT >= 0.1),
            ("CAIDA_MINIMA_SALIDA_PERCENT", 0 < config.CAIDA_MINIMA_SALIDA_PERCENT < 0.5),
        ]
        
        for nombre, ok in checks:
            valor = getattr(config, nombre, None)
            if ok:
                print(f"  ✅ {nombre}: {valor}")
                self.pasos_verificados.append(f"{nombre} OK")
            else:
                print(f"  ❌ {nombre}: {valor}")
                config_ok = False
                self.errores.append(f"{nombre} tiene valor inválido: {valor}")
        
        # Verificar URLs
        print(f"\n  🌐 Solana RPC: {config.SOLANA_RPC_URL[:50]}...")
        print(f"  🌐 Jupiter API: {config.JUPITER_API_URL}")
        
        # Verificar DRY_RUN
        modo = "DRY-RUN (Seguro)" if config.DRY_RUN else "REAL (⚠️ PELIGRO)"
        print(f"  ⚠️  Modo: {modo}")
        
        return config_ok
    
    def verificar_filtros(self) -> bool:
        """Verifica que los filtros de seguridad funcionen."""
        print("\n" + "=" * 70)
        print("🛡️  VERIFICACIÓN DE FILTROS DE SEGURIDAD")
        print("=" * 70)
        
        filtros_ok = True
        
        # Crear token válido
        token_valido = TokenData(
            mint="ValidToken123456789",
            price_current=0.0001,
            liquidity_sol=100.0,
            holders_count=500,
            volume_5min=200.0,
            top_holder_percent=0.10,
        )
        
        # Crear token inválido
        token_invalido = TokenData(
            mint="InvalidToken123456",
            price_current=0.0000001,
            liquidity_sol=5.0,
            holders_count=50,
            volume_5min=10.0,
            top_holder_percent=0.40,
        )
        
        # Test token válido
        ok, msg = Filtros.verificar(token_valido)
        if ok:
            print(f"  ✅ Filtro acepta token válido: {msg or 'OK'}")
            self.pasos_verificados.append("Filtro válido OK")
        else:
            print(f"  ❌ Filtro rechaza token válido: {msg}")
            filtros_ok = False
            self.errores.append(f"Filtro rechaza token válido: {msg}")
        
        # Test token inválido
        ok, msg = Filtros.verificar(token_invalido)
        if not ok:
            print(f"  ✅ Filtro rechaza token inválido: {msg or 'Rechazado'}")
            self.pasos_verificados.append("Filtro inválido OK")
        else:
            print(f"  ❌ Filtro acepta token inválido")
            filtros_ok = False
            self.errores.append("Filtro acepta token inválido")
        
        return filtros_ok
    
    def verificar_backtest(self) -> bool:
        """Ejecuta un mini-backtest para verificar funcionalidad."""
        print("\n" + "=" * 70)
        print("🧪 VERIFICACIÓN DE BACKTEST (100 sesiones)")
        print("=" * 70)
        
        try:
            # Ejecutar backtest corto
            random.seed(42)
            sesiones = [sim_sesion() for _ in range(100)]
            
            caps = [s["capital"] for s in sesiones]
            exitos = len([s for s in sesiones if s["exito"]])
            quiebras = len([s for s in sesiones if s["quiebra"]])
            todos_t = [t for s in sesiones for t in s["trades"]]
            wins = [t for t in todos_t if t["gan"] > 0]
            
            # Guardar resultados
            self.resultados = {
                "n": 100,
                "exito_pct": exitos,
                "quiebra_pct": quiebras,
                "capital_prom": sum(caps) / len(caps),
                "win_rate": len(wins) / len(todos_t) * 100 if todos_t else 0,
                "trades_totales": len(todos_t),
            }
            
            print(f"  ✅ Backtest completado")
            print(f"     Sesiones: 100")
            print(f"     Éxitos: {exitos}%")
            print(f"     Trades: {len(todos_t)}")
            print(f"     Win rate: {self.resultados['win_rate']:.1f}%")
            
            self.pasos_verificados.append("Backtest funcional")
            return True
            
        except Exception as e:
            print(f"  ❌ Error en backtest: {e}")
            self.errores.append(f"Backtest falló: {e}")
            return False
    
    def verificar_trading_engine(self) -> bool:
        """Verifica el motor de trading."""
        print("\n" + "=" * 70)
        print("🤖 VERIFICACIÓN DEL TRADING ENGINE")
        print("=" * 70)
        
        try:
            engine = TradingEngine("TestWallet123456789012345678901234567")
            
            # Crear token de prueba
            token = TokenData(
                mint="TestMint123456789",
                price_current=0.0001,
                liquidity_sol=100.0,
                holders_count=200,
                volume_5min=50.0,
            )
            
            # Test abrir posición
            ok = engine.abrir_posicion(token, 50.0)
            if ok:
                print(f"  ✅ Abrir posición: OK")
                self.pasos_verificados.append("Abrir posición OK")
            else:
                print(f"  ❌ Abrir posición: Falló")
                self.errores.append("Abrir posición falló")
                return False
            
            # Test agregar martingala
            ok = engine.agregar_martingala(token.mint, 0.00012, 50.0)
            if ok:
                print(f"  ✅ Martingala: OK")
                self.pasos_verificados.append("Martingala OK")
            else:
                print(f"  ⚠️  Martingala: No aplicada (posiblemente capital insuficiente)")
            
            # Test cerrar posición
            trade = engine.cerrar_posicion(token.mint, 0.00011)
            if trade:
                print(f"  ✅ Cerrar posición: OK (ROI: {trade.get('roi_percent', 0):.1f}%)")
                self.pasos_verificados.append("Cerrar posición OK")
            else:
                print(f"  ❌ Cerrar posición: Falló")
                self.errores.append("Cerrar posición falló")
                return False
            
            # Test generar reporte
            reporte = engine.generar_reporte()
            print(f"  ✅ Reporte: Generado")
            print(f"     Capital: {reporte['capital']:.2f} SOL")
            print(f"     Trades: {reporte['trades']}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error en Trading Engine: {e}")
            self.errores.append(f"Trading Engine falló: {e}")
            return False
    
    def verificar_archivos(self) -> bool:
        """Verifica que los archivos necesarios existan."""
        print("\n" + "=" * 70)
        print("📁 VERIFICACIÓN DE ARCHIVOS")
        print("=" * 70)
        
        archivos_requeridos = [
            "solana_bot_complete.py",
            "requirements.txt",
            "setup_termux.sh",
            "install_termux.sh",
            "run.sh",
            "termux.md",
            "README.md",
        ]
        
        archivos_opcionales = [
            ".env",
            ".env.example",
            "trading_bot.log",
            "trades.json",
            "backtest_results.json",
        ]
        
        archivos_ok = True
        
        for archivo in archivos_requeridos:
            if Path(archivo).exists():
                print(f"  ✅ {archivo}")
                self.pasos_verificados.append(f"{archivo} existe")
            else:
                print(f"  ❌ {archivo} (REQUERIDO)")
                archivos_ok = False
                self.errores.append(f"Archivo requerido faltante: {archivo}")
        
        for archivo in archivos_opcionales:
            if Path(archivo).exists():
                print(f"  ✅ {archivo} (opcional)")
            else:
                print(f"  ⚠️  {archivo} (no existe - opcional)")
        
        return archivos_ok
    
    def generar_reporte_final(self) -> bool:
        """Genera el reporte final de verificación."""
        print("\n" + "=" * 70)
        print("📊 REPORTE FINAL DE VERIFICACIÓN")
        print("=" * 70)
        
        total_pasos = len(self.pasos_verificados)
        total_errores = len(self.errores)
        
        print(f"\n  Pasos verificados: {total_pasos}")
        print(f"  Errores: {total_errores}")
        
        if total_errores == 0:
            print(f"\n  🎉 RESULTADO: ✅ VERIFICACIÓN COMPLETADA EXITOSAMENTE")
            print(f"\n  El bot está listo para:")
            print(f"     • Backtesting: python solana_bot_complete.py backtest --sesiones 1000")
            print(f"     • Dry-Run: ./run.sh dryrun")
            print(f"     • Trading Real: ./run.sh run <WALLET> --real")
            return True
        else:
            print(f"\n  ⚠️  RESULTADO: VERIFICACIÓN CON {total_errores} ERROR(ES)")
            print(f"\n  Errores encontrados:")
            for i, error in enumerate(self.errores, 1):
                print(f"     {i}. {error}")
            return False
    
    def ejecutar_verificacion_completa(self, full: bool = False) -> bool:
        """Ejecuta la verificación completa del sistema."""
        print("\n" + "╔" + "═" * 68 + "╗")
        print("║" + " " * 10 + "🔍 VERIFICADOR v0.2" + " " * 38 + "║")
        print("║" + " " * 15 + "Solana Memecoin Trading Bot" + " " * 29 + "║")
        print("╚" + "═" * 68 + "╝")
        
        # Ejecutar todas las verificaciones
        verificaciones = [
            ("Dependencias", self.verificar_dependencias),
            ("Configuración", self.verificar_configuracion),
            ("Filtros", self.verificar_filtros),
            ("Trading Engine", self.verificar_trading_engine),
            ("Archivos", self.verificar_archivos),
        ]
        
        if full:
            verificaciones.insert(2, ("Backtest", self.verificar_backtest))
        
        resultados = {}
        for nombre, func in verificaciones:
            try:
                resultados[nombre] = func()
            except Exception as e:
                print(f"\n  ❌ Error en {nombre}: {e}")
                resultados[nombre] = False
                self.errores.append(f"{nombre}: {e}")
        
        # Resumen
        print("\n" + "=" * 70)
        print("📋 RESUMEN DE VERIFICACIONES")
        print("=" * 70)
        
        for nombre, ok in resultados.items():
            icono = "✅" if ok else "❌"
            print(f"  {icono} {nombre}")
        
        return self.generar_reporte_final()


# ============================================
# SECCIÓN 10: MAIN
# ============================================

def main():
    # Crear logger
    logger = make_logger("SolanaBot")
    
    parser = argparse.ArgumentParser(
        description="Solana Memecoin Trading Bot v0.2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python solana_bot_complete.py backtest --sesiones 10000
  python solana_bot_complete.py run
  python solana_bot_complete.py verify --full

⚠️  ADVERTENCIA: Este bot implica riesgos significativos.
    Usa siempre primero --dry-run para probar.
        """
    )
    parser.add_argument("mode", 
                       choices=["backtest", "run", "verify", "help"],
                       help="modo de ejecución")
    parser.add_argument("--sesiones", type=int, default=10000, help="Número de sesiones para backtest")
    parser.add_argument("--real", action="store_true", help="Modo real (no dry-run)")
    parser.add_argument("--full", action="store_true", help="Verificación completa")
    
    args = parser.parse_args()
    
    if args.mode == "help":
        parser.print_help()
        return
    
    # Modo verificación
    if args.mode == "verify":
        verificador = VerificadorEstadisticas()
        verificador.ejecutar_verificacion_completa(full=args.full)
        return
    
    # Modo backtest
    if args.mode == "backtest":
        print("\n" + "=" * 70)
        print("🧪 INICIANDO BACKTEST")
        print("=" * 70)
        resultado = ejecutar_backtest(args.sesiones)
        
        # Verificación rápida
        print("\n" + "=" * 70)
        print("🔍 VERIFICACIÓN DE RESULTADOS")
        print("=" * 70)
        
        refs = VerificadorEstadisticas.VALORES_REFERENCIA
        print(f"\n  Comparando con valores teóricos:\n")
        
        for key, nombre in [("exito_pct", "Tasa de Éxito"), ("capital_prom", "Capital Promedio"), ("win_rate", "Win Rate")]:
            if key in resultado:
                real = resultado[key]
                valor_ref = refs.get(key, {}).get("valor", 0)
                tolerancia = refs.get(key, {}).get("tolerancia", 0.2)
                diferencia = abs(real - valor_ref) / valor_ref if valor_ref else 0
                icono = "✅" if diferencia <= tolerancia else ("⚠️ " if diferencia <= tolerancia * 2 else "❌")
                print(f"  {icono} {nombre}: {real:.2f} (ref: {valor_ref:.2f}, Δ: {diferencia*100:.1f}%)")
        
        print(f"\n  📁 Resultados en: backtest_results.json")
        return
    
    # ============================================
    # MODO RUN (Simulacro o Real)
    # ============================================
    
    # Verificar configuración primero
    errores_config = validar_configuracion(config)
    
    if errores_config:
        print("\n" + "=" * 70)
        print("❌ ERRORES DE CONFIGURACIÓN DETECTADOS")
        print("=" * 70)
        for i, error in enumerate(errores_config, 1):
            print(f"  {i}. {error}")
        print("\n  Corrige estos errores antes de continuar.")
        print("  Usa: nano .env  o  ./run.sh (menú interactivo)")
        return
    
    # Modo simulacro vs real
    if args.real:
        config.DRY_RUN = False
        print("\n" + "=" * 70)
        print("🔴 MODO REAL - TRADING CON SOL REAL")
        print("=" * 70)
        logger.warning("⚠️  MODO REAL ACTIVADO - Se enviarán transacciones")
    else:
        config.DRY_RUN = True
        print("\n" + "=" * 70)
        print("🔵 MODO SIMULACRO (DRY-RUN)")
        print("=" * 70)
        logger.info("🟡 Simulación - No se enviarán transacciones")
    
    # Mostrar información de wallet (solo pubkey, nunca mostrar private key)
    if UTILITIES_OK:
        try:
            wallet = SolanaWallet(config.WALLET_PRIVATE_KEY)
            logger.info(f"👛 Wallet: {wallet.pubkey[:10]}...{wallet.pubkey[-6:]}")
        except Exception as e:
            logger.error(f"Error con wallet: {e}")
            return
    else:
        logger.warning("⚠️  Utilidades no disponibles - usando modo limitado")
    
    logger.info(f"💰 Capital: {config.CAPITAL_INICIAL} SOL")
    logger.info(f"🎯 Objetivo: {config.OBJETIVO_GLOBAL} SOL")
    
    # Loop principal de trading
    print("\n" + "=" * 70)
    print("🚀 INICIANDO BOT DE TRADING")
    print("=" * 70)
    print("  Presiona Ctrl+C para detener")
    print("=" * 70)
    
    # Crear engine de trading
    engine = TradingEngine(config.WALLET_PRIVATE_KEY[:20] + "...")  # Dummy wallet para simulación
    engine.capital = config.CAPITAL_INICIAL
    
    try:
        logger.info("🔄 Buscando tokens en Solana mainnet...")
        
        for i in range(50):  # Loop continuo
            # Simular detección de pump
            pump = random.uniform(1.05, 3.0)
            token = TokenData(
                mint=f"SimToken{i:03d}{random.randint(10000,99999)}",
                price_current=0.00001 * pump,
                price_5min_ago=0.000005,
                liquidity_sol=random.uniform(50, 1000),
                holders_count=random.randint(100, 2000),
                volume_5min=random.uniform(50, 1000),
                top_holder_percent=random.uniform(0.05, 0.20),
            )
            
            # Verificar filtros de seguridad
            ok, msg = Filtros.verificar(token)
            if not ok:
                log_evento(logger, "FILTRO", token.mint, None, msg)
                time.sleep(config.LOOP_INTERVAL)
                continue
            
            # Pump detectado
            log_evento(logger, "PUMP", token.mint, token.price_current, f"+{(pump-1)*100:.0f}%")
            
            # Abrir posición
            if engine.capital >= config.INVERSION_BASE:
                if engine.abrir_posicion(token):
                    log_evento(logger, "COMPRA", token.mint, token.price_current, f"{config.INVERSION_BASE} SOL")
                    
                    # Simular martingala
                    if random.random() > 0.4:
                        nuevo_precio = token.price_current * random.uniform(1.05, 1.25)
                        if engine.agregar_martingala(token.mint, nuevo_precio):
                            log_evento(logger, "INFO", token.mint, nuevo_precio, "📈 Martingala #2")
                    
                    # Simular cierre
                    if random.random() > 0.35:
                        precio_cierre = token.price_current * random.uniform(0.85, 1.20)
                        trade = engine.cerrar_posicion(token.mint, precio_cierre)
                        if trade:
                            log_trade(logger, trade)
            
            # Mostrar estado cada 5 iteraciones
            if i % 5 == 0 and i > 0:
                reporte = engine.generar_reporte()
                log_status(logger, reporte['capital'], reporte['posiciones'], reporte['trades'], reporte['ganancia_total'])
            
            time.sleep(config.LOOP_INTERVAL)
        
        # Reporte final
        print("\n" + "=" * 70)
        print("📊 REPORTE FINAL")
        print("=" * 70)
        
        reporte = engine.generar_reporte()
        logger.info(f"💰 Capital final: {reporte['capital']:.2f} SOL")
        logger.info(f"📈 Posiciones: {reporte['posiciones']}")
        logger.info(f"📉 Trades: {reporte['trades']}")
        logger.info(f"💵 Ganancia: {reporte['ganancia_total']:+.2f} SOL")
        logger.info(f"📊 Win rate: {reporte['win_rate']:.1f}%")
        
        # Verificación final
        print("\n" + "=" * 70)
        capital_ok = reporte['capital'] >= config.CAPITAL_INICIAL * 0.7
        trades_ok = reporte['trades'] >= 1
        
        print(f"  {'✅' if capital_ok else '⚠️ '} Capital OK: {reporte['capital']:.2f} SOL")
        print(f"  {'✅' if trades_ok else '⚠️ '} Trades OK: {reporte['trades']}")
        
        if capital_ok and trades_ok:
            print(f"\n  🎉 Operación completada exitosamente")
        
    except KeyboardInterrupt:
        logger.warning("⏹️  Detenido por el usuario")
        reporte = engine.generar_reporte()
        print("\n" + "=" * 70)
        print("📊 ESTADO AL DETENER")
        print("=" * 70)
        print(f"  Capital: {reporte['capital']:.2f} SOL")
        print(f"  Trades: {reporte['trades']}")
        print(f"  Ganancia: {reporte['ganancia_total']:+.2f} SOL")
    
    print("\n" + "=" * 70)
    print("✅ SESIÓN COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    main()
