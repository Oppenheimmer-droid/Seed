#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║          SOLANA MEMECOIN TRADING BOT v0.3                              ║
║          SIMULACRO - Trading Simulator                                 ║
║          Modo: DRY-RUN (Sin transacciones reales)                     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import os
import random
import sys
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict

# Intentar importar utilidades
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from solana_utils import SolanaRPC, SolanaWallet
    from logger import make_logger, log_evento
    UTILITIES = True
except ImportError:
    UTILITIES = False
    log_evento = lambda *args, **kwargs: None

# ============================================
# CONFIGURACIÓN
# ============================================

@dataclass
class Config:
    CAPITAL_INICIAL: float = 500.0
    OBJETIVO_GLOBAL: float = 615.0
    STOP_LOSS_GLOBAL: float = 100.0
    INVERSION_BASE: float = 100.0
    MAX_ENTRADAS_POR_TOKEN: int = 5
    MAX_POSICIONES_SIMULTANEAS: int = 5
    UMBRAL_MARTINGALA_PERCENT: float = 0.10
    CAIDA_MINIMA_SALIDA_PERCENT: float = 0.03
    LIQUIDEZ_MINIMA_SOL: float = 10.0
    HOLDERS_MINIMOS: int = 100
    TOP_HOLDER_MAXIMO_PERCENT: float = 0.20
    PUMP_MINIMO_PERCENT: float = 1.00
    LOOP_INTERVAL: float = 2.0
    RPC_URL: str = "https://api.mainnet-beta.solana.com"
    SOL_MINT: str = "So11111111111111111111111111111111111111112"

config = Config()

# Cargar de .env si existe
if os.path.exists(".env"):
    for line in open(".env"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            if key == "CAPITAL_INICIAL":
                config.CAPITAL_INICIAL = float(value)
            elif key == "OBJETIVO_GLOBAL":
                config.OBJETIVO_GLOBAL = float(value)
            elif key == "STOP_LOSS_GLOBAL":
                config.STOP_LOSS_GLOBAL = float(value)
            elif key == "INVERSION_BASE":
                config.INVERSION_BASE = float(value)
            elif key == "SOLANA_RPC_URL":
                config.RPC_URL = value

# ============================================
# ESTILOS Y COLORES
# ============================================

C = {
    'negro': '\033[30m', 'rojo': '\033[31m', 'verde': '\033[32m',
    'amarillo': '\033[33m', 'azul': '\033[34m', 'magenta': '\033[35m',
    'cyan': '\033[36m', 'blanco': '\033[37m',
    'reset': '\033[0m', 'negrita': '\033[1m', 'subrayado': '\033[4m'
}

# ============================================
# FUNCIONES DE DISPLAY
# ============================================

def clear_screen():
    print("\033[2J\033[H", end="")

def header():
    print(f"""
{C['cyan']}╔══════════════════════════════════════════════════════════╗
║        🤖 SOLANA MEMECOIN BOT — ARRANCANDO              ║
╚══════════════════════════════════════════════════════════╝{C['reset']}
""")

def print_banner():
    hora = datetime.now().strftime('%H:%M:%S')
    print(f"{hora} {C['verde']}→{C['reset']} Cargando configuración .env")
    
    if UTILITIES:
        print(f"{hora} {C['verde']}→{C['reset']} Wallet: {C['amarillo']}SIMULATION MODE{C['reset']} (dry-run)")
        print(f"{hora} {C['verde']}→{C['reset']} RPC: api.mainnet-beta.solana.com")
    else:
        print(f"{hora} {C['amarillo']}⚠️ {C['reset']} Modo offline - simulando localmente")

def print_config():
    hora = datetime.now().strftime('%H:%M:%S')
    print(f"""
{hora} {C['cyan']}📋 Capital: {config.CAPITAL_INICIAL}u → Objetivo: {config.OBJETIVO_GLOBAL}u (+{(config.OBJETIVO_GLOBAL/config.CAPITAL_INICIAL-1)*100:.0f}%)
{hora}    Inv/entrada: {config.INVERSION_BASE}u | MaxPos: {config.MAX_POSICIONES_SIMULTANEAS} | Pump≥{config.PUMP_MINIMO_PERCENT*100:.0f}%
{hora}    Martingala: +{config.UMBRAL_MARTINGALA_PERCENT*100:.0f}% | Salida: -{config.CAIDA_MINIMA_SALIDA_PERCENT*100:.0f}% desde ATH
""")

def print_separator():
    print(f"{C['cyan']}{'─' * 64}{C['reset']}")

def print_trade_header(num):
    hora = datetime.now().strftime('%H:%M:%S')
    print(f"""
{C['negro']}{'─' * 64}
  TRADE #{num} — Escaneando mercado...
{'─' * 64}{C['reset']}
{hora} {C['cyan']}·{C['reset']} Escaneando Raydium... ({random.randint(8,20)} tokens nuevos)""")

def print_filtro(token, razon):
    hora = datetime.now().strftime('%H:%M:%S')
    short = token[:12] + "..." if len(token) > 12 else token
    print(f"{hora} {C['rojo']}❌{C['reset']} {short} — {C['amarillo']}{razon}{C['reset']}")

def print_pump(token, symbol, pump_pct, precio, filtros_ok=True):
    hora = datetime.now().strftime('%H:%M:%S')
    estado = f"{C['verde']}✅ todos superados{C['reset']}" if filtros_ok else f"{C['rojo']}❌ filtros fallidos{C['reset']}"
    print(f"""
{C['negro']}{'═' * 64}
{hora} {C['verde']}🚀 PUMP DETECTADO{C['reset']}
{hora}    Token:    {C['cyan']}{symbol}{C['reset']} ({token[:12]}...)
{hora}    Pump:     {C['verde']}+{pump_pct:.0f}%{C['reset']} en 5 minutos
{hora}    Precio:   {C['amarillo']}{precio:.10f}{C['reset']} SOL
{hora}    Filtros:  {estado}
{'═' * 64}{C['reset']}""")

def print_compra(num_entrada, precio, inversion, tokens, total_inv, precio_prom):
    hora = datetime.now().strftime('%H:%M:%S')
    if num_entrada == 1:
        titulo = "COMPRA INICIAL"
        borde = "═"
    else:
        titulo = f"MARTINGALA #{num_entrada}"
        borde = "—"

    print(f"""
{hora} {C['verde']}╔══════════════════════════════════════════╗{C['reset']}
{hora} {C['verde']}║  💰 {titulo:^36}║{C['reset']}
{hora} {C['verde']}╠══════════════════════════════════════════╣{C['reset']}
{hora} {C['verde']}║  Entrada #{num_entrada}   Precio: {precio:.10f}   ║{C['reset']}
{hora} {C['verde']}║  Inversión: {inversion}u   Tokens: {tokens:,.0f}      ║{C['reset']}
{hora} {C['verde']}║  Total inv: {total_inv}u  P.prom: {precio_prom:.10f}║{C['reset']}
{hora} {C['verde']}╚══════════════════════════════════════════╝{C['reset']}""")

def print_martingala(pump_pct, precio):
    hora = datetime.now().strftime('%H:%M:%S')
    print(f"""
{hora} {C['verde']}─{C['reset']}{C['verde']}────────────────────────────────{C['reset']}
{hora} {C['verde']}✅ MARTINGALA ACTIVADA — +{pump_pct:.1f}% desde entrada anterior{C['reset']}
{hora} {C['verde']}   Precio actual: {C['amarillo']}{precio:.10f}{C['reset']} SOL
{hora} {C['verde']}─{C['reset']}{C['verde']}────────────────────────────────{C['reset']}""")

def print_precio(actual, valor, roi, ath_diff, entradas, max_entradas):
    barra_len = 50
    barra_actual = int((roi / 100) * barra_len) if roi > 0 else 0
    barra = "█" * barra_actual + "░" * (barra_len - barra_actual)
    
    ath_pct = abs(ath_diff) * 100
    ATH_emoji = "ATH" if ath_diff == 0 else f"-{ath_pct:.1f}%"
    
    hora = datetime.now().strftime('%H:%M:%S')
    roi_color = C['verde'] if roi >= 0 else C['rojo']
    print(f"{hora} {C['cyan']}📊{C['reset']} {actual:.10f} | Val:{valor:.1f}u | ROI:{roi_color}{roi:+.1f}%{C['reset']} [{barra}] | {ATH_emoji} | E:{entradas}/{max_entradas}")

def print_caida():
    hora = datetime.now().strftime('%H:%M:%S')
    print(f"{hora} {C['amarillo']}⚠️  CAÍDA DETECTADA — precio bajando desde ATH{C['reset']}")

def print_salida(token, symbol, motivo, entradas, invertido, recuperado, ganancia, roi):
    hora = datetime.now().strftime('%H:%M:%S')
    es_ganancia = ganancia >= 0
    emoji = "✅" if es_ganancia else "❌"
    color_gan = C['verde'] if es_ganancia else C['rojo']
    
    print(f"""
{hora} {C['negro']}╔══════════════════════════════════════════╗{C['reset']}
{hora} {color_gan}{emoji} SALIDA — {symbol:^30}║{C['reset']}
{hora} {C['cyan']}╠══════════════════════════════════════════╣{C['reset']}
{hora} {C['cyan']}║  Motivo:    {motivo:^30}║{C['reset']}
{hora} {C['cyan']}║  Entradas:  {entradas:^30}║{C['reset']}
{hora} {C['cyan']}║  Invertido: {invertido:.1f}u{'':>21}║{C['reset']}
{hora} {C['cyan']}║  Recuperado: {recuperado:.2f}u{'':>20}║{C['reset']}
{hora} {C['cyan']}║  Ganancia:  {color_gan}{ganancia:+.2f}u{'':>19}{C['reset']} ({roi:+.1f}%){C['reset']}
{hora} {C['cyan']}╚══════════════════════════════════════════╝{C['reset']}""")

def print_estado(capital, objetivo, trades, ganancia_total, trades_ejecutados):
    hora = datetime.now().strftime('%H:%M:%S')
    progreso = (capital / objetivo) * 100
    barra_len = 64
    barra_actual = int((progreso / 100) * barra_len)
    barra = "█" * barra_actual + "░" * (barra_len - barra_actual)
    
    emoji = "📈" if ganancia_total >= 0 else "📉"
    gan_color = C['verde'] if ganancia_total >= 0 else C['rojo']
    
    print(f"""
{hora} {C['negro']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C['reset']}
{hora} {C['cyan']}💰 Capital: {capital:.1f}u / {objetivo:.1f}u{C['reset']}
{hora} {C['cyan']}🎯 Progreso [{barra}] {progreso:.1f}%{C['reset']}
{hora} {C['cyan']}📈 Trades ejecutados: {trades_ejecutados}{C['reset']}
{hora} {gan_color}{emoji} Ganancia total: {ganancia_total:+.1f}u{C['reset']}
{hora} {C['negro']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C['reset']}""")

def print_reporte_final(capital_inicial, capital_final, trades, winners, losers, win_rate, mejor_trade, peor_trade, objetivo_alcanzado):
    print(f"""
{C['negro']}╔══════════════════════════════════════════════════╗{C['reset']}
{C['cyan']}║          📊 REPORTE FINAL DE SESIÓN              ║{C['reset']}
{C['cyan']}╠══════════════════════════════════════════════════╣{C['reset']}
{C['cyan']}║  Capital inicial:   {capital_inicial:.1f}u{'':>17}║{C['reset']}
{C['cyan']}║  Capital final:     {capital_final:.2f}u{'':>17}║{C['reset']}
{C['green'] if capital_final > capital_inicial else C['red']}║  Ganancia total:    {(capital_final-capital_inicial):+.2f}u  ({((capital_final/capital_inicial)-1)*100:+.1f}%){'':>5}║{C['reset']}
{C['cyan']}╠══════════════════════════════════════════════════╣{C['reset']}
{C['cyan']}║  Trades ejecutados: {trades:^20}║{C['reset']}
{C['cyan']}║  Ganadores:        {winners:^20}║{C['reset']}
{C['cyan']}║  Perdedores:       {losers:^20}║{C['reset']}
{C['cyan']}║  Win rate:         {win_rate:.1f}%{'':>15}║{C['reset']}
{C['green']}║  Mejor trade:      {mejor_trade['simbolo']} {mejor_trade['ganancia']:+.1f}u{'':>8}║{C['reset']}
{C['red']}║  Peor trade:       {peor_trade['simbolo']} {peor_trade['ganancia']:+.1f}u{'':>8}║{C['reset']}
{C['green'] if objetivo_alcanzado else C['red']}║  Objetivo ({objetivo:.0f}u):   {'✅ ALCANZADO' if objetivo_alcanzado else '❌ NO ALCANZADO'}{'':>5}║{C['reset']}
{C['negro']}╚══════════════════════════════════════════════════╝{C['reset']}""")

# ============================================
# CLASES DE SIMULACIÓN
# ============================================

@dataclass
class Token:
    mint: str
    symbol: str
    precio: float
    precio_inicial: float
    liquidez: float
    holders: int
    top_holder_pct: float
    ATH: float = 0.0

@dataclass
class Posicion:
    token: Token
    entradas: List[Dict]
    tokens_totales: float
    inversion_total: float
    precio_promedio: float

class Simulador:
    def __init__(self):
        self.capital = config.CAPITAL_INICIAL
        self.posiciones: Dict[str, Posicion] = {}
        self.trades: List[Dict] = []
        self.num_trade = 0
        self.running = True
        
        # Tokens simulados recientes (para variety)
        self.tokens_recientes = []
    
    def generar_token(self) -> Optional[Token]:
        """Genera un token aleatorio con propiedades."""
        symbols = ["DOGWIF", "PEPE", "WOJAK", "BONK", "SHIB", "FLOKI", "MEME", "ELON", "SATS", "NORK"]
        pump = random.uniform(1.5, 4.0)
        
        token = Token(
            mint=f"{random.randint(100000, 999999)}{random.randint(100000, 999999)}{random.randint(100, 999)}",
            symbol=random.choice(symbols) + str(random.randint(1, 99)),
            precio=random.uniform(0.000001, 0.00005) * pump,
            precio_inicial=random.uniform(0.000001, 0.00002),
            liquidez=random.uniform(10, 500),
            holders=random.randint(80, 2000),
            top_holder_pct=random.uniform(0.05, 0.35),
        )
        token.precio_inicial = token.precio / pump
        token.ATH = token.precio
        return token
    
    def verificar_filtros(self, token: Token) -> tuple[bool, str]:
        """Verifica si el token pasa los filtros."""
        if token.liquidez < config.LIQUIDEZ_MINIMA_SOL:
            return False, f"Liquidez {token.liquidez:.1f} < {config.LIQUIDEZ_MINIMA_SOL} SOL"
        if token.holders < config.HOLDERS_MINIMOS:
            return False, f"Holders {token.holders} < {config.HOLDERS_MINIMOS}"
        if token.top_holder_pct > config.TOP_HOLDER_MAXIMO_PERCENT:
            return False, f"Top holder {token.top_holder_pct*100:.1f}% > {config.TOP_HOLDER_MAXIMO_PERCENT*100:.0f}%"
        
        pump = (token.precio / token.precio_inicial - 1) * 100
        if pump < config.PUMP_MINIMO_PERCENT * 100:
            return False, f"Pump {pump:.0f}% < {config.PUMP_MINIMO_PERCENT*100:.0f}%"
        
        return True, ""
    
    def abrir_posicion(self, token: Token) -> bool:
        """Abre una posición en el token."""
        if len(self.posiciones) >= config.MAX_POSICIONES_SIMULTANEAS:
            return False
        if self.capital < config.INVERSION_BASE:
            return False
        
        entrada = {
            'precio': token.precio,
            'cantidad': config.INVERSION_BASE,
            'tokens': config.INVERSION_BASE / token.precio,
        }
        
        pos = Posicion(
            token=token,
            entradas=[entrada],
            tokens_totales=entrada['tokens'],
            inversion_total=entrada['cantidad'],
            precio_promedio=token.precio,
        )
        
        self.posiciones[token.mint] = pos
        self.capital -= config.INVERSION_BASE
        return True
    
    def agregar_martingala(self, mint: str) -> bool:
        """Agrega una entrada de martingala."""
        if mint not in self.posiciones:
            return False
        if len(self.posiciones[mint].entradas) >= config.MAX_ENTRADAS_POR_TOKEN:
            return False
        if self.capital < config.INVERSION_BASE:
            return False
        
        pos = self.posiciones[mint]
        
        # Pump del precio para martingala
        pump = random.uniform(0.05, 0.25)
        pos.token.precio *= (1 + pump)
        if pos.token.precio > pos.token.ATH:
            pos.token.ATH = pos.token.precio
        
        entrada = {
            'precio': pos.token.precio,
            'cantidad': config.INVERSION_BASE,
            'tokens': config.INVERSION_BASE / pos.token.precio,
        }
        
        pos.entradas.append(entrada)
        pos.tokens_totales += entrada['tokens']
        pos.inversion_total += entrada['cantidad']
        pos.precio_promedio = pos.inversion_total / pos.tokens_totales
        
        self.capital -= config.INVERSION_BASE
        return True
    
    def verificar_y_cerrar(self, mint: str) -> Optional[Dict]:
        """Verifica si debe cerrar la posición y la cierra."""
        if mint not in self.posiciones:
            return None
        
        pos = self.posiciones[mint]
        
        # Verificar si el precio está por debajo del umbral desde ATH
        if pos.token.ATH > 0:
            caida = (pos.token.ATH - pos.token.precio) / pos.token.ATH
            if caida >= config.CAIDA_MINIMA_SALIDA_PERCENT:
                return self.cerrar_posicion(mint, "CAIDA -3% DESDE ATH")
        
        return None
    
    def cerrar_posicion(self, mint: str, motivo: str) -> Optional[Dict]:
        """Cierra una posición."""
        if mint not in self.posiciones:
            return None
        
        pos = self.posiciones[mint]
        recuperado = pos.tokens_totales * pos.token.precio
        ganancia = recuperado - pos.inversion_total
        roi = (ganancia / pos.inversion_total) * 100 if pos.inversion_total > 0 else 0
        
        trade = {
            'symbol': pos.token.symbol,
            'mint': mint,
            'entradas': len(pos.entradas),
            'inversion': pos.inversion_total,
            'recuperado': recuperado,
            'ganancia': ganancia,
            'roi': roi,
            'motivo': motivo,
        }
        
        self.trades.append(trade)
        self.capital += recuperado
        
        # Limpiar posición
        del self.posiciones[mint]
        
        return trade
    
    def simular_precio(self, token: Token):
        """Simula el movimiento del precio."""
        # Movimiento aleatorio
        cambio = random.uniform(-0.02, 0.05)
        token.precio *= (1 + cambio)
        
        # Actualizar ATH
        if token.precio > token.ATH:
            token.ATH = token.precio
        
        # Valor actual de la posición
        if hasattr(self, 'posiciones') and token.mint in self.posiciones:
            pos = self.posiciones[token.mint]
            return pos.tokens_totales * token.precio
        
        return token.tokens_totales * token.precio if hasattr(token, 'tokens_totales') else 0

# ============================================
# MAIN
# ============================================

def main():
    clear_screen()
    header()
    print_banner()
    
    # Modo simulacro
    print(f"\n{datetime.now().strftime('%H:%M:%S')} {C['amarillo']}⚠️  MODO SIMULACRO — Sin transacciones reales{C['reset']}\n")
    
    print_config()
    print_separator()
    
    simulador = Simulador()
    trade_num = 0
    max_trades = 20
    
    try:
        while simulador.running and trade_num < max_trades:
            trade_num += 1
            print_trade_header(trade_num)
            
            # Generar y filtrar tokens
            tokens_filtrados = 0
            while tokens_filtrados < 3:
                token = simulador.generar_token()
                ok, razon = simulador.verificar_filtros(token)
                
                if not ok:
                    print_filtro(token.mint, razon)
                else:
                    tokens_filtrados += 1
            
            # Seleccionar el mejor token (el último que pasó filtros)
            if tokens_filtrados > 0:
                pump_pct = (token.precio / token.precio_inicial - 1) * 100
                print_pump(token.mint, token.symbol, pump_pct, token.precio)
                
                # Abrir posición inicial
                if simulador.abrir_posicion(token):
                    print_compra(1, token.precio, config.INVERSION_BASE, 
                               config.INVERSION_BASE / token.precio,
                               config.INVERSION_BASE, token.precio)
                    
                    # Loop de monitoreo del trade
                    for _ in range(20):
                        if not simulador.running:
                            break
                        
                        # Simular precio
                        valor = simulador.simular_precio(token)
                        roi = (valor / simulador.posiciones[token.mint].inversion_total - 1) * 100
                        
                        # Verificar martingala
                        pos = simulador.posiciones.get(token.mint)
                        if pos and len(pos.entradas) < config.MAX_ENTRADAS_POR_TOKEN:
                            pump_desde_entrada = (token.precio / pos.entradas[-1]['precio'] - 1) * 100
                            if pump_desde_entrada >= config.UMBRAL_MARTINGALA_PERCENT * 100:
                                if simulador.agregar_martingala(token.mint):
                                    print_martingala(pump_desde_entrada, token.precio)
                                    print_compra(
                                        len(pos.entradas), 
                                        token.precio, 
                                        config.INVERSION_BASE,
                                        config.INVERSION_BASE / token.precio,
                                        pos.inversion_total,
                                        pos.precio_promedio
                                    )
                        
                        # Mostrar estado del precio
                        if pos:
                            ath_diff = (token.ATH - token.precio) / token.ATH if token.ATH > 0 else 0
                            print_precio(
                                token.precio, valor, roi, ath_diff,
                                len(pos.entradas), config.MAX_ENTRADAS_POR_TOKEN
                            )
                            
                            # Verificar si hay caída
                            if ath_diff >= config.CAIDA_MINIMA_SALIDA_PERCENT:
                                print_caida()
                                # Mostrar 3 ticks más de caída
                                for _ in range(3):
                                    simulador.simular_precio(token)
                                    valor = pos.tokens_totales * token.precio
                                    roi = (valor / pos.inversion_total - 1) * 100
                                    ath_diff = (token.ATH - token.precio) / token.ATH
                                    print_precio(
                                        token.precio, valor, roi, ath_diff,
                                        len(pos.entradas), config.MAX_ENTRADAS_POR_TOKEN
                                    )
                                    time.sleep(0.5)
                                
                                # Ejecutar salida
                                print(f"{datetime.now().strftime('%H:%M:%S')} {C['rojo']}🚨 UMBRAL -3% ALCANZADO — ejecutando salida{C['reset']}")
                                trade = simulador.cerrar_posicion(token.mint, "CAIDA -3% DESDE ATH")
                                
                                if trade:
                                    print_salida(
                                        token.mint, trade['symbol'], trade['motivo'],
                                        trade['entradas'], trade['inversion'],
                                        trade['recuperado'], trade['ganancia'], trade['roi']
                                    )
                                    
                                    # Mostrar estado
                                    ganancia_total = sum(t['ganancia'] for t in simulador.trades)
                                    print_estado(
                                        simulador.capital, config.OBJETIVO_GLOBAL,
                                        len(simulador.trades), ganancia_total, trade_num
                                    )
                                    
                                    # Verificar objetivo o stop loss
                                    if simulador.capital >= config.OBJETIVO_GLOBAL:
                                        print(f"\n{datetime.now().strftime('%H:%M:%S')} {C['verde']}🎉 OBJETIVO ALCANZADO — Bot deteniéndose{C['reset']}\n")
                                        simulador.running = False
                                        break
                                    elif simulador.capital <= config.STOP_LOSS_GLOBAL:
                                        print(f"\n{datetime.now().strftime('%H:%M:%S')} {C['rojo']}🚨 STOP LOSS ALCANZADO — Bot deteniéndose{C['reset']}\n")
                                        simulador.running = False
                                        break
                                break
                        
                        time.sleep(config.LOOP_INTERVAL)
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print(f"\n\n{datetime.now().strftime('%H:%M:%S')} {C['amarillo']}⏹️  Bot detenido por usuario{C['reset']}\n")
    
    # Reporte final
    winners = [t for t in simulador.trades if t['ganancia'] > 0]
    losers = [t for t in simulador.trades if t['ganancia'] <= 0]
    win_rate = len(winners) / len(simulador.trades) * 100 if simulador.trades else 0
    
    mejor = max(simulador.trades, key=lambda x: x['ganancia']) if simulador.trades else {'symbol': 'N/A', 'ganancia': 0}
    peor = min(simulador.trades, key=lambda x: x['ganancia']) if simulador.trades else {'symbol': 'N/A', 'ganancia': 0}
    
    print_reporte_final(
        config.CAPITAL_INICIAL, simulador.capital,
        len(simulador.trades), len(winners), len(losers), win_rate,
        {'symbol': mejor['symbol'], 'ganancia': mejor['ganancia']},
        {'symbol': peor['symbol'], 'ganancia': peor['ganancia']},
        simulador.capital >= config.OBJETIVO_GLOBAL
    )

if __name__ == "__main__":
    main()
