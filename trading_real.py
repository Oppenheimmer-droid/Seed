#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║          SOLANA MEMECOIN TRADING BOT v0.3                              ║
║          TRADING REAL - Ejecución en Solana Mainnet                    ║
║          ⚠️  USA SOL REAL - EXTREMO CUIDADO                           ║
╚══════════════════════════════════════════════════════════════════════════╝

⚠️  ADVERTENCIAS CRÍTICAS:
- Este bot USA SOL REAL de tu wallet
- Puedes perder TODA tu inversión
- Usaamount_in_smallest_unit siempre modo simulacro primero
- Nunca inviertas más de lo que puedas perder
- Este código es DEMOSTRATIVO - Revisa antes de ejecutar

Uso:
    python trading_real.py                  # Con menú interactivo
    python trading_real.py --verify         # Verificar configuración
    python trading_real.py --test-rpc      # Probar conexión RPC
    python trading_real.py --dry-run       # Simular sinTX (RECOMENDADO)
"""

import asyncio
import base64
import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from base58 import b58decode, b58encode

# ============================================
# IMPORTS LOCALES
# ============================================

try:
    from solana_utils import SolanaWallet, SolanaRPC, JupiterSwap, validar_configuracion
    UTILITIES_OK = True
except ImportError as e:
    print(f"⚠️  Error importando utilidades: {e}")
    UTILITIES_OK = False

# ============================================
# CONSTANTES
# ============================================

VERSION = "0.3"
SOL_MINT = "So11111111111111111111111111111111111111112"

# ============================================
# ESTILOS Y COLORES
# ============================================

C = {
    'reset': '\033[0m', 'negro': '\033[30m', 'rojo': '\033[31m',
    'verde': '\033[32m', 'amarillo': '\033[33m', 'azul': '\033[34m',
    'magenta': '\033[35m', 'cyan': '\033[36m', 'blanco': '\033[37m',
    'negrita': '\033[1m', 'subrayado': '\033[4m',
    'bg_rojo': '\033[41m', 'bg_verde': '\033[42m',
}

# ============================================
# FUNCIONES DE DISPLAY
# ============================================

def cls():
    print("\033[2J\033[H", end="")

def banner():
    print(f"""
{C['negro']}╔══════════════════════════════════════════════════════════╗
║                                                                  ║
║   🤖 SOLANA MEMECOIN TRADING BOT v{VERSION}                          ║
║   🚨 MODO TRADING REAL - CON SOL REAL                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{C['reset']}
""")

def menu_principal():
    cls()
    banner()
    
    print(f"""{C['cyan']}╔══════════════════════════════════════════════════════════╗
║                    MENÚ PRINCIPAL                          ║
╠══════════════════════════════════════════════════════════╣{C['reset']}
""")
    
    # Verificar estado de configuración
    wallet_ok = False
    rpc_ok = False
    balance = 0
    
    if UTILITIES_OK and os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
        
        priv_key = os.getenv("WALLET_PRIVATE_KEY", "")
        rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        
        if priv_key and len(priv_key) > 80:
            try:
                wallet = SolanaWallet(priv_key)
                rpc = SolanaRPC(rpc_url)
                
                async def check():
                    global balance
                    balance = await rpc.get_balance(wallet.pubkey)
                
                asyncio.run(check())
                wallet_ok = True
                rpc_ok = True
                pubkey = wallet.pubkey
            except Exception as e:
                print(f"{C['rojo']}  ⚠️  Error verificando wallet: {e}{C['reset']}")
        else:
            pubkey = "No configurada"
    else:
        pubkey = "No configurada"
    
    # Mostrar estado
    wallet_status = f"{C['verde']}✅ Conectada{C['reset']}" if wallet_ok else f"{C['rojo']}❌ No configurada{C['reset']}"
    rpc_status = f"{C['verde']}✅ {rpc_url[:40]}...{C['reset']}" if rpc_ok else f"{C['rojo']}❌ No disponible{C['reset']}"
    balance_str = f"{balance:.4f} SOL" if wallet_ok else "N/A"
    
    print(f"""║  👛 Wallet:  {wallet_status:<45}║
║  💰 Balance: {balance_str:<45}║
║  🌐 RPC:     {rpc_status:<45}║
╠══════════════════════════════════════════════════════════╣
║                                                              ║
║  1. 🔍 VERIFICAR CONFIGURACIÓN                            ║
║  2. 📡 PROBAR CONEXIÓN RPC                                 ║
║  3. 🎮 MODO SIMULACIÓN (DRY-RUN)                          ║
║  4. 🚀 INICIAR TRADING REAL ⚠️                             ║
║  5. ⚙️  CONFIGURAR                                         ║
║  6. 📋 VER HISTORIAL DE TRADES                             ║
║  7. ❌ SALIR                                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════╝
""")

def print_exito(msg):
    print(f"{C['verde']}✅ {msg}{C['reset']}")

def print_error(msg):
    print(f"{C['rojo']}❌ {msg}{C['reset']}")

def print_warning(msg):
    print(f"{C['amarillo']}⚠️  {msg}{C['reset']}")

def print_info(msg):
    print(f"{C['cyan']}ℹ️  {msg}{C['reset']}")

# ============================================
# CONFIGURACIÓN
# ============================================

@dataclass
class BotConfig:
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
    SLIPPAGE_BPS: int = 300
    PRIORITY_FEE: int = 100_000
    LOOP_INTERVAL: float = 2.0
    RPC_URL: str = "https://api.mainnet-beta.solana.com"
    
    @classmethod
    def from_env(cls):
        config = cls()
        if os.path.exists(".env"):
            for line in open(".env"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if hasattr(config, key):
                        try:
                            setattr(config, key, float(value) if value.replace(".","").replace("-","").isdigit() else value)
                        except:
                            pass
        return config

config = BotConfig.from_env()

# ============================================
# CARGAR VARIABLES DE ENTORNO
# ============================================

def cargar_env():
    """Carga variables de .env"""
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
        return True
    return False

# ============================================
# CLASES DE TRADING
# ============================================

@dataclass
class Token:
    mint: str
    symbol: str
    nombre: str
    decimals: int = 9
    precio_usd: float = 0.0
    liquidez_sol: float = 0.0
    holders: int = 0
    top_holder_pct: float = 0.0
    volume_24h: float = 0.0
    created_at: float = 0.0

@dataclass
class Entrada:
    precio: float
    cantidad_sol: float
    tokens: float
    timestamp: float
    tipo: str  # "COMPRA" o "MARTINGALA"

@dataclass
class Posicion:
    token: Token
    entradas: List[Entrada] = field(default_factory=list)
    precio_promedio: float = 0.0
    ath_precio: float = 0.0
    timestamp_apertura: float = field(default_factory=time.time)
    
    @property
    def inversion_total(self) -> float:
        return sum(e.cantidad_sol for e in self.entradas)
    
    @property
    def tokens_totales(self) -> float:
        return sum(e.tokens for e in self.entradas)

class TradingEngine:
    """
    Motor de trading real - Conecta con Jupiter y RPC de Solana
    """
    
    def __init__(self, wallet: SolanaWallet, rpc: SolanaRPC, jupiter: JupiterSwap = None):
        self.wallet = wallet
        self.rpc = rpc
        self.jupiter = jupiter or JupiterSwap(wallet, rpc)
        self.posiciones: Dict[str, Posicion] = {}
        self.trades_history: List[Dict] = []
        self.capital_actual: float = 0.0
        self.running = False
        
        # Archivo de logs
        self.log_file = "logs/trades_real.log"
        os.makedirs("logs", exist_ok=True)
    
    def log(self, mensaje: str, nivel: str = "INFO"):
        """Log a archivo y consola"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{timestamp}] [{nivel}] {mensaje}"
        print(linea)
        with open(self.log_file, "a") as f:
            f.write(linea + "\n")
    
    async def get_balance(self) -> float:
        """Obtiene balance de SOL"""
        try:
            return await self.rpc.get_balance(self.wallet.pubkey)
        except Exception as e:
            self.log(f"Error obteniendo balance: {e}", "ERROR")
            return 0.0
    
    async def get_token_balance(self, mint: str) -> Tuple[float, int]:
        """Obtiene balance de un token SPL"""
        try:
            return await self.rpc.get_token_balance(self.wallet.pubkey, mint)
        except Exception as e:
            self.log(f"Error obteniendo balance de token: {e}", "ERROR")
            return 0.0, 9
    
    async def get_token_info(self, mint: str) -> Optional[Token]:
        """
        Obtiene información de un token desde Birdeye o RPC
        NOTA: Implementación básica - necesita API key real
        """
        # Aquí iría la lógica para obtener datos reales del token
        # Por ahora, retornamos None (el bot continuará buscando)
        return None
    
    def verificar_filtros(self, token: Token) -> Tuple[bool, str]:
        """
        Verifica si el token cumple los filtros de seguridad
        """
        if token.liquidez_sol < config.LIQUIDEZ_MINIMA_SOL:
            return False, f"Liquidez {token.liquidez_sol:.1f} < {config.LIQUIDEZ_MINIMA_SOL} SOL"
        
        if token.holders < config.HOLDERS_MINIMOS:
            return False, f"Holders {token.holders} < {config.HOLDERS_MINIMOS}"
        
        if token.top_holder_pct > config.TOP_HOLDER_MAXIMO_PERCENT:
            return False, f"Top holder {token.top_holder_pct*100:.1f}% > {config.TOP_HOLDER_MAXIMO_PERCENT*100:.0f}%"
        
        return True, ""
    
    async def comprar(self, token_mint: str, cantidad_sol: float) -> Tuple[bool, str]:
        """
        Ejecuta compra de tokens con SOL
        Retorna (exito, mensaje)
        """
        self.log(f"🔵 COMPRANDO {cantidad_sol} SOL de {token_mint[:12]}...", "INFO")
        
        try:
            # Convertir SOL a lamports
            amount_lamports = int(cantidad_sol * 1e9)
            
            # Obtener quote de Jupiter
            quote = await self.jupiter.get_quote(
                input_mint=SOL_MINT,
                output_mint=token_mint,
                amount=amount_lamports,
                slippage_bps=config.SLIPPAGE_BPS
            )
            
            if not quote:
                return False, "No se pudo obtener quote de Jupiter"
            
            self.log(f"📊 Quote: {quote.get('outAmount', 'N/A')} tokens", "INFO")
            
            # Ejecutar swap
            success, tx_sig = await self.jupiter.execute_swap(quote, dry_run=False)
            
            if success:
                self.log(f"✅ Swap exitoso: {tx_sig[:20]}...", "INFO")
                # Confirmar TX
                confirmed = await self.rpc.confirm_transaction(tx_sig)
                if confirmed:
                    self.log(f"✅ Transacción confirmada", "INFO")
                    return True, tx_sig
                else:
                    self.log(f"⚠️  Transacción puede no haber sido confirmada", "WARNING")
                    return True, tx_sig  # Aún retornamos éxito si se envió
            else:
                return False, "Swap falló"
                
        except Exception as e:
            self.log(f"❌ Error en compra: {e}", "ERROR")
            return False, str(e)
    
    async def vender(self, token_mint: str, porcentaje: float = 1.0) -> Tuple[bool, str]:
        """
        Vende tokens por SOL
        """
        self.log(f"🔴 VENDIENDO {porcentaje*100:.0f}% de {token_mint[:12]}...", "INFO")
        
        try:
            # Obtener balance actual
            balance, decimals = await self.get_token_balance(token_mint)
            
            if balance <= 0:
                return False, "No hay balance para vender"
            
            # Calcular cantidad
            amount = int(balance * porcentaje * (10 ** decimals))
            
            # Obtener quote
            quote = await self.jupiter.get_quote(
                input_mint=token_mint,
                output_mint=SOL_MINT,
                amount=amount,
                slippage_bps=config.SLIPPAGE_BPS + 100  # Más slippage para venta
            )
            
            if not quote:
                return False, "No se pudo obtener quote"
            
            # Ejecutar swap
            success, tx_sig = await self.jupiter.execute_swap(quote, dry_run=False)
            
            if success:
                self.log(f"✅ Venta exitosa: {tx_sig[:20]}...", "INFO")
                return True, tx_sig
            else:
                return False, "Venta falló"
                
        except Exception as e:
            self.log(f"❌ Error en venta: {e}", "ERROR")
            return False, str(e)
    
    def abrir_posicion(self, token: Token, cantidad_sol: float, tokens_recibidos: float):
        """Registra una nueva posición"""
        entrada = Entrada(
            precio=cantidad_sol / tokens_recibidos if tokens_recibidos > 0 else 0,
            cantidad_sol=cantidad_sol,
            tokens=tokens_recibidos,
            timestamp=time.time(),
            tipo="COMPRA"
        )
        
        posicion = Posicion(token=token)
        posicion.entradas.append(entrada)
        posicion.precio_promedio = entrada.precio
        posicion.ath_precio = entrada.precio
        
        self.posiciones[token.mint] = posicion
        self.capital_actual -= cantidad_sol
        
        self.log(f"💰 Posición abierta: {token.symbol} - {cantidad_sol} SOL", "INFO")
    
    def agregar_martingala(self, mint: str, cantidad_sol: float, tokens_recibidos: float):
        """Agrega entrada de martingala a posición existente"""
        if mint not in self.posiciones:
            return False
        
        pos = self.posiciones[mint]
        
        entrada = Entrada(
            precio=cantidad_sol / tokens_recibidos if tokens_recibidos > 0 else 0,
            cantidad_sol=cantidad_sol,
            tokens=tokens_recibidos,
            timestamp=time.time(),
            tipo="MARTINGALA"
        )
        
        pos.entradas.append(entrada)
        
        # Recalcular precio promedio
        total_invertido = sum(e.cantidad_sol for e in pos.entradas)
        total_tokens = sum(e.tokens for e in pos.entradas)
        pos.precio_promedio = total_invertido / total_tokens if total_tokens > 0 else 0
        
        self.capital_actual -= cantidad_sol
        
        self.log(f"📈 Martingala #{len(pos.entradas)}: {cantidad_sol} SOL", "INFO")
        return True
    
    def cerrar_posicion(self, mint: str, motivo: str) -> Optional[Dict]:
        """Cierra una posición y retorna el trade"""
        if mint not in self.posiciones:
            return None
        
        pos = self.posiciones[mint]
        
        # Calcular resultado
        total_invertido = pos.inversion_total
        tokens_totales = pos.tokens_totales
        
        trade = {
            'token_mint': mint,
            'symbol': pos.token.symbol,
            'entradas': len(pos.entradas),
            'inversion_total': total_invertido,
            'tokens_totales': tokens_totales,
            'precio_promedio': pos.precio_promedio,
            'motivo': motivo,
            'timestamp': time.time(),
            # Estos campos se llenan cuando se vende
            'recuperado': 0,
            'ganancia': 0,
            'roi': 0,
            'tx_compra': '',
            'tx_venta': '',
        }
        
        self.trades_history.append(trade)
        del self.posiciones[mint]
        
        self.log(f"💸 Posición cerrada: {pos.token.symbol} - {motivo}", "INFO")
        return trade
    
    async def verificar_y_actuar(self, mint: str) -> Optional[Dict]:
        """
        Verifica el estado de una posición y toma acciones
        - Agrega martingala si hay pump
        - Cierra si hay caída desde ATH
        """
        if mint not in self.posiciones:
            return None
        
        pos = self.posiciones[mint]
        
        # Obtener precio actual (simulado por ahora)
        # En producción, esto vendría de Birdeye o Jupiter
        precio_actual = pos.token.precio_usd  # Placeholder
        
        # Actualizar ATH
        if precio_actual > pos.ath_precio:
            pos.ath_precio = precio_actual
        
        # Verificar si aplicar martingala
        if len(pos.entradas) < config.MAX_ENTRADAS_POR_TOKEN:
            ultima_entrada = pos.entradas[-1]
            pump_desde_entrada = (precio_actual / ultima_entrada.precio - 1) if ultima_entrada.precio > 0 else 0
            
            if pump_desde_entrada >= config.UMBRAL_MARTINGALA_PERCENT:
                # Aplicar martingala
                self.log(f"📈 PUMP detectado - Aplicando martingala", "INFO")
                # En producción: await self.comprar(mint, config.INVERSION_BASE)
        
        # Verificar si cerrar por caída
        if pos.ath_precio > 0:
            caida_desde_ath = (pos.ath_precio - precio_actual) / pos.ath_precio
            
            if caida_desde_ath >= config.CAIDA_MINIMA_SALIDA_PERCENT:
                self.log(f"⚠️  CAÍDA desde ATH - Cerrando posición", "INFO")
                return self.cerrar_posicion(mint, f"CAIDA -{caida_desde_ath*100:.1f}% DESDE ATH")
        
        return None

# ============================================
# FUNCIONES DE COMANDOS
# ============================================

async def verificar_configuracion():
    """Verifica que todo esté configurado correctamente"""
    cls()
    banner()
    
    print(f"{C['cyan']}╔══════════════════════════════════════════════════════════╗
║              VERIFICACIÓN DE CONFIGURACIÓN              ║
╚══════════════════════════════════════════════════════════╝{C['reset']}\n")
    
    errores = []
    
    # 1. Verificar .env
    print(f"{C['cyan']}📄 Verificando archivo .env...{C['reset']}")
    if not os.path.exists(".env"):
        errores.append("Archivo .env no encontrado")
        print_error("Archivo .env no encontrado")
    else:
        print_exito(".env encontrado")
    
    # 2. Verificar variables
    cargar_env()
    
    priv_key = os.getenv("WALLET_PRIVATE_KEY", "")
    rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    birdeye_key = os.getenv("BIRDEYE_API_KEY", "")
    
    # Validar private key
    print(f"\n{C['cyan']}🔑 Verificando Wallet...{C['reset']}")
    if not priv_key:
        errores.append("WALLET_PRIVATE_KEY no configurada")
        print_error("WALLET_PRIVATE_KEY no configurada")
    elif len(priv_key) < 80:
        errores.append(f"WALLET_PRIVATE_KEY parece ser public key ({len(priv_key)} chars)")
        print_error(f"Wallet parece ser public key ({len(priv_key)} chars)")
        print_info("Exporta private key desde Phantom: Settings → Export Private Key")
    else:
        try:
            if UTILITIES_OK:
                wallet = SolanaWallet(priv_key)
                print_exito(f"Wallet válida: {wallet.pubkey[:10]}...{wallet.pubkey[-6:]}")
            else:
                print_warning("SolanaWallet no disponible - solo validación de longitud")
                print_info(f"Wallet (validada por longitud): {priv_key[:10]}...{priv_key[-6:]}")
        except Exception as e:
            errores.append(f"Wallet inválida: {e}")
            print_error(f"Wallet inválida: {e}")
    
    # Validar RPC
    print(f"\n{C['cyan']}🌐 Verificando RPC...{C['reset']}")
    if not rpc_url:
        errores.append("SOLANA_RPC_URL no configurada")
        print_error("RPC URL no configurada")
    else:
        print_info(f"RPC: {rpc_url}")
        if UTILITIES_OK:
            try:
                rpc = SolanaRPC(rpc_url)
                version = await rpc.get_version()
                print_exito(f"RPC conectado: Solana {version}")
                
                # Verificar balance
                if UTILITIES_OK and priv_key and len(priv_key) > 80:
                    wallet = SolanaWallet(priv_key)
                    balance = await rpc.get_balance(wallet.pubkey)
                    print_info(f"Balance: {balance:.4f} SOL")
            except Exception as e:
                errores.append(f"RPC no responde: {e}")
                print_error(f"RPC no responde: {e}")
    
    # Verificar Birdeye
    print(f"\n{C['cyan']}📊 Verificando Birdeye API...{C['reset']}")
    if not birdeye_key or birdeye_key == "your_birdeye_api_key_here":
        print_warning("Birdeye API no configurada (opcional pero recomendado)")
    else:
        print_exito("Birdeye API configurada")
    
    # Resumen
    print(f"\n{C['cyan']}{'═' * 64}{C['reset']}")
    if errores:
        print(f"\n{C['rojo']}❌ SE ENCONTRARON {len(errores)} ERROR(ES):{C['reset']}")
        for i, e in enumerate(errores, 1):
            print(f"  {C['rojo']}{i}.{C['reset']} {e}")
        print(f"\n{C['amarillo']}⚠️  Corrige estos errores antes de operar{C['reset']}")
    else:
        print(f"\n{C['verde']}✅ TODA LA CONFIGURACIÓN ESTÁ CORRECTA{C['reset']}")
        print(f"\n{C['verde']}Puedes iniciar trading con:{C['reset']}")
        print(f"  {C['cyan']}python trading_real.py --dry-run{C['reset']}  # Simulación (recomendado)")
        print(f"  {C['cyan']}python trading_real.py --start{C['reset']}    # Trading real ⚠️")
    
    input(f"\n{C['cyan']}Presiona Enter para volver al menú...{C['reset']}")

async def probar_rpc():
    """Prueba la conexión RPC"""
    cls()
    banner()
    
    print(f"{C['cyan']}╔══════════════════════════════════════════════════════════╗
║                 PROBANDO CONEXIÓN RPC                    ║
╚══════════════════════════════════════════════════════════╝{C['reset']}\n")
    
    cargar_env()
    rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    
    print(f"{C['cyan']}🌐 Conectando a: {rpc_url}{C['reset']}\n")
    
    if not UTILITIES_OK:
        print_error("SolanaRPC no disponible")
        input("\nPresiona Enter...")
        return
    
    try:
        rpc = SolanaRPC(rpc_url)
        
        print(f"{C['cyan']}⏳ Obteniendo información del nodo...{C['reset']}")
        version = await rpc.get_version()
        print_exito(f"Versión Solana: {version}")
        
        print(f"\n{C['cyan']}⏳ Verificando conexión...{C['reset']}")
        
        # Obtener blockhash
        blockhash, height = await rpc.get_latest_blockhash()
        print_exito(f"Blockhash: {blockhash[:20]}... (bloque {height})")
        
        # Intentar obtener balance si hay wallet
        priv_key = os.getenv("WALLET_PRIVATE_KEY", "")
        if priv_key and len(priv_key) > 80:
            wallet = SolanaWallet(priv_key)
            balance = await rpc.get_balance(wallet.pubkey)
            print_exito(f"Balance wallet: {balance:.4f} SOL")
            print_info(f"Wallet: {wallet.pubkey[:15]}...{wallet.pubkey[-6:]}")
        else:
            print_warning("No hay wallet configurada")
        
        print(f"\n{C['verde']}✅ RPC FUNCIONA CORRECTAMENTE{C['reset']}")
        
    except Exception as e:
        print_error(f"Error de conexión: {e}")
        print(f"\n{C['amarillo']}Posibles soluciones:{C['reset']}")
        print("  1. Verifica tu conexión a internet")
        print("  2. Prueba otro RPC (Helius, QuickNode, etc.)")
        print("  3. Espera unos minutos y reintenta")
    
    input(f"\n{C['cyan']}Presiona Enter para volver al menú...{C['reset']}")

async def iniciar_dry_run():
    """Inicia modo simulación (dry-run)"""
    cls()
    banner()
    
    print(f"""
{C['amarillo']}╔══════════════════════════════════════════════════════════════════╗
║                    ⚠️  MODO SIMULACIÓN ⚠️                              ║
║                                                                  ║
║  Este modo simula operaciones SIN enviar transacciones reales.   ║
║  Úsalo para probar tu configuración y entender el bot.          ║
╚══════════════════════════════════════════════════════════════════╝{C['reset']}
""")
    
    confirmar = input(f"{C['cyan']}¿Iniciar simulación? (s/n): {C['reset']}").strip().lower()
    
    if confirmar != 's':
        print("Cancelado")
        return
    
    print(f"\n{C['verde']}🚀 Iniciando simulación...{C['reset']}\n")
    print(f"{C['cyan']}(Presiona Ctrl+C para detener){C['reset']}\n")
    
    # Aquí iría la lógica de simulación
    # Por ahora, solo esperamos y mostramos que está "corriendo"
    try:
        print(f"{C['cyan']}⏳ Buscando pumps en el mercado...{C['reset']}")
        print(f"{C['cyan']}   (Modo dry-run activo - no se enviarán transacciones){C['reset']}")
        
        # Simular que está buscando
        for i in range(10):
            print(f"\r{C['cyan']}   Escaneando... {'.' * (i % 4)}{C['reset']}", end="", flush=True)
            await asyncio.sleep(1)
        
        print(f"\n\n{C['verde']}✅ Simulación completada{C['reset']}")
        print(f"{C['cyan']}(En producción, aquí se ejecutaría el loop de trading simulado){C['reset']}")
        
    except KeyboardInterrupt:
        print(f"\n\n{C['amarillo']}⏹️  Simulación detenida{C['reset']}")
    
    input(f"\n{C['cyan']}Presiona Enter para volver al menú...{C['reset']}")

async def iniciar_trading_real():
    """Inicia trading real con SOL"""
    cls()
    banner()
    
    print(f"""
{C['rojo']}╔══════════════════════════════════════════════════════════════════╗
║              🚨⚠️  ATENCIÓN: TRADING REAL ⚠️🚨                          ║
║                                                                  ║
║  ESTE MODO USA TU SOL REAL.                                      ║
║  PUEDES PERDER TODA TU INVERSIÓN.                                ║
║                                                                  ║
║  Parámetros configurados:                                        ║
║    • Capital: {config.CAPITAL_INICIAL} SOL                                           ║
║    • Objetivo: {config.OBJETIVO_GLOBAL} SOL                                           ║
║    • Stop Loss: {config.STOP_LOSS_GLOBAL} SOL                                          ║
║    • Inversión/Trade: {config.INVERSION_BASE} SOL                                       ║
╚══════════════════════════════════════════════════════════════════╝{C['reset']}
""")
    
    confirmar = input(f"{C['rojo']}Escribe 'CONFIRMO' para continuar (escribe otra cosa para cancelar): {C['reset']}")
    
    if confirmar != 'CONFIRMO':
        print(f"{C['cyan']}Cancelado{C['reset']}")
        return
    
    print(f"\n{C['rojo']}⚠️  ÚLTIMA ADVERTENCIA - Trading real iniciando...{C['reset']}\n")
    await asyncio.sleep(2)
    
    # Aquí iría la lógica de trading real
    print(f"{C['rojo']}⏳ Iniciando motor de trading...{C['reset']}")
    print(f"{C['rojo']}   (Esta función requiere implementación completa de Jupiter API){C['reset']}")
    
    input(f"\n{C['cyan']}Presiona Enter para volver al menú...{C['reset']}")

def configurar():
    """Abre editor para configurar .env"""
    cls()
    banner()
    
    print(f"{C['cyan']}╔══════════════════════════════════════════════════════════╗
║                    CONFIGURAR .ENV                         ║
╚══════════════════════════════════════════════════════════╝{C['reset']}
""")
    
    if not os.path.exists(".env"):
        print(f"{C['amarillo']}Creando nuevo archivo .env...{C['reset']}")
        with open(".env", "w") as f:
            f.write("# Solana Trading Bot Configuration\n")
            f.write("# Copia este archivo y edita con tus valores\n\n")
            f.write("SOLANA_RPC_URL=https://api.mainnet-beta.solana.com\n")
            f.write("BIRDEYE_API_KEY=your_birdeye_api_key_here\n")
            f.write("WALLET_PRIVATE_KEY=your_private_key_base58_here\n")
            f.write("DRY_RUN=true\n")
    
    print(f"{C['cyan']}Editando archivo .env...{C['reset']}\n")
    print(f"   nano .env\n")
    print(f"   o\n")
    print(f"   cat .env\n")
    
    # Intentar abrir con editor si está disponible
    try:
        import subprocess
        subprocess.run(["nano", ".env"], check=False)
    except:
        print(f"{C['amarillo']}Editor no disponible. Usa: nano .env{C['reset']}")
    
    input(f"\n{C['cyan']}Presiona Enter para volver al menú...{C['reset']}")

def ver_historial():
    """Muestra historial de trades"""
    cls()
    banner()
    
    print(f"{C['cyan']}╔══════════════════════════════════════════════════════════╗
║                    HISTORIAL DE TRADES                      ║
╚══════════════════════════════════════════════════════════╝{C['reset']}\n")
    
    log_file = "logs/trades_real.log"
    
    if os.path.exists(log_file):
        print(f"{C['cyan']}📄 Últimas 50 entradas:{C['reset']}\n")
        with open(log_file, "r") as f:
            lines = f.readlines()
            for line in lines[-50:]:
                print(line.strip())
    else:
        print(f"{C['amarillo']}No hay historial todavía.{C['reset']}")
        print(f"{C['cyan']}El historial se guardará en: {log_file}{C['reset']}")
    
    input(f"\n{C['cyan']}Presiona Enter para volver al menú...{C['reset']}")

# ============================================
# MAIN
# ============================================

async def main():
    """Loop principal con menú interactivo"""
    
    if len(sys.argv) > 1:
        # Modo comando
        cmd = sys.argv[1]
        
        if cmd == "--verify":
            await verificar_configuracion()
        elif cmd == "--test-rpc":
            await probar_rpc()
        elif cmd == "--dry-run":
            await iniciar_dry_run()
        elif cmd == "--start":
            await iniciar_trading_real()
        else:
            print(f"Comando desconocido: {cmd}")
            print("Uso: python trading_real.py [--verify|--test-rpc|--dry-run|--start]")
        return
    
    # Menú interactivo
    while True:
        menu_principal()
        opcion = input(f"{C['cyan']}Selecciona opción (1-7): {C['reset']}").strip()
        
        if opcion == "1":
            await verificar_configuracion()
        elif opcion == "2":
            await probar_rpc()
        elif opcion == "3":
            await iniciar_dry_run()
        elif opcion == "4":
            await iniciar_trading_real()
        elif opcion == "5":
            configurar()
        elif opcion == "6":
            ver_historial()
        elif opcion == "7":
            print(f"\n{C['cyan']}👋 Saliendo...{C['reset']}\n")
            break
        else:
            print(f"\n{C['rojo']}Opción inválida{C['reset']}")
            time.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
