"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    PERSISTENCIA Y STORAGE                               ║
║          Módulo para guardar/cargar configuración y watchlist           ║
║          Compatible con ARM64 / Termux / Python 3.13                   ║
╚══════════════════════════════════════════════════════════════════════════╝

Funciones de persistencia:
- guardar_config_dex(): Guarda configuración DexScreener a JSON
- cargar_config_dex(): Carga configuración desde JSON
- guardar_watchlist(): Guarda lista de tokens a seguir
- cargar_watchlist(): Carga watchlist desde JSON
- guardar_trade(): Registra un trade completado
- cargar_historial(): Carga historial de trades

Los archivos se guardan en ~/.solana_memebot/
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from solana_bot.config.bot_config import (
    BotConfig,
    DEFAULT_CONFIG_DIR,
    DEFAULT_DEX_CONFIG_FILE,
    DEFAULT_WATCHLIST_FILE,
    DEFAULT_TRADES_FILE,
)

logger = logging.getLogger(__name__)

# ============================================
# RUTAS Y CONSTANTES
# ============================================

APP_DIR = Path.home() / ".solana_memebot"
APP_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DIR / "dex_config.json"
WATCHLIST_FILE = APP_DIR / "watchlist.json"
TRADES_FILE = APP_DIR / "trades.json"
LOGS_FILE = APP_DIR / "bot.log"


# ============================================
# CONFIGURACIÓN DEXSCREENER
# ============================================

def guardar_config_dex(config: Dict[str, Any]) -> bool:
    """
    Guarda la configuración de DexScreener a archivo JSON.
    
    Args:
        config: Diccionario con la configuración
        
    Returns:
        True si se guardó correctamente, False si falló
    """
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Config DexScreener guardada en {CONFIG_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error guardando config: {e}")
        return False


def cargar_config_dex() -> Dict[str, Any]:
    """
    Carga la configuración de DexScreener desde archivo JSON.
    
    Returns:
        Diccionario con la configuración o config por defecto si no existe
    """
    if not CONFIG_FILE.exists():
        logger.info("⚠️ Archivo de config no existe, usando valores por defecto")
        return get_default_dex_config()
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        logger.info(f"✅ Config DexScreener cargada desde {CONFIG_FILE}")
        return config
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parseando config JSON: {e}")
        return get_default_dex_config()
    except Exception as e:
        logger.error(f"❌ Error cargando config: {e}")
        return get_default_dex_config()


def get_default_dex_config() -> Dict[str, Any]:
    """
    Retorna la configuración por defecto de DexScreener.
    
    Esta configuración se usa cuando no existe archivo de configuración.
    """
    return {
        "dex_screener": {
            "enabled": True,
            "priority": "birdeye",
            "min_liquidity_usd": 50000,
            "min_volume_5m_usd": 10000,
            "max_age_minutes": 60,
            "min_holders": 100,
            "max_top_holder_pct": 0.20,
            "dex_whitelist": ["raydium", "meteora", "pump.fun", "orca", "fluxbeam"],
            "watchlist": []
        },
        "loop": {
            "capital_operativo_base": 100.0,
            "extraccion_por_ciclo": 15.0,
            "stop_ciclo": -50.0
        }
    }


# ============================================
# WATCHLIST
# ============================================

def guardar_watchlist(tokens: List[str]) -> bool:
    """
    Guarda la watchlist de tokens a seguir.
    
    Args:
        tokens: Lista de direcciones de tokens (base58)
        
    Returns:
        True si se guardó correctamente
    """
    try:
        WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "tokens": [t.strip() for t in tokens if _is_valid_solana_address(t.strip())]
        }
        
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Watchlist guardada ({len(data['tokens'])} tokens)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error guardando watchlist: {e}")
        return False


def cargar_watchlist() -> List[str]:
    """
    Carga la watchlist de tokens desde archivo JSON.
    
    Returns:
        Lista de direcciones de tokens o lista vacía si no existe
    """
    if not WATCHLIST_FILE.exists():
        logger.info("⚠️ Archivo de watchlist no existe")
        return []
    
    try:
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        tokens = data.get("tokens", [])
        logger.info(f"✅ Watchlist cargada ({len(tokens)} tokens)")
        return tokens
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parseando watchlist JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Error cargando watchlist: {e}")
        return []


def agregar_a_watchlist(token_address: str) -> bool:
    """
    Agrega un token a la watchlist existente.
    
    Args:
        token_address: Dirección del token a agregar
        
    Returns:
        True si se agregó, False si ya existía o falló
    """
    if not _is_valid_solana_address(token_address):
        logger.warning(f"⚠️ Dirección inválida: {token_address}")
        return False
    
    tokens = cargar_watchlist()
    
    if token_address in tokens:
        logger.info(f"ℹ️ Token ya está en watchlist: {token_address[:12]}...")
        return False
    
    tokens.append(token_address)
    return guardar_watchlist(tokens)


def eliminar_de_watchlist(token_address: str) -> bool:
    """
    Elimina un token de la watchlist.
    
    Args:
        token_address: Dirección del token a eliminar
        
    Returns:
        True si se eliminó, False si no existía
    """
    tokens = cargar_watchlist()
    
    if token_address not in tokens:
        logger.info(f"ℹ️ Token no está en watchlist: {token_address[:12]}...")
        return False
    
    tokens.remove(token_address)
    return guardar_watchlist(tokens)


# ============================================
# HISTORIAL DE TRADES
# ============================================

def guardar_trade(trade: Dict[str, Any]) -> bool:
    """
    Guarda un trade completado al historial.
    
    Args:
        trade: Diccionario con datos del trade
        
    Returns:
        True si se guardó correctamente
    """
    try:
        TRADES_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Asegurar que existe el archivo con array vacío
        if not TRADES_FILE.exists():
            with open(TRADES_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
        
        # Leer trades existentes
        with open(TRADES_FILE, "r", encoding="utf-8") as f:
            trades = json.load(f)
        
        # Agregar nuevo trade con timestamp
        trade["recorded_at"] = datetime.now().isoformat()
        trades.append(trade)
        
        # Guardar (sobrescribir con todos los trades)
        with open(TRADES_FILE, "w", encoding="utf-8") as f:
            json.dump(trades, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Trade registrado: {trade.get('token_mint', '?')[:12]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error guardando trade: {e}")
        return False


def cargar_historial(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Carga el historial de trades.
    
    Args:
        limit: Máximo número de trades a retornar (0 = todos)
        
    Returns:
        Lista de trades ordenados por fecha (más reciente primero)
    """
    if not TRADES_FILE.exists():
        return []
    
    try:
        with open(TRADES_FILE, "r", encoding="utf-8") as f:
            trades = json.load(f)
        
        # Ordenar por fecha (más reciente primero)
        trades.sort(
            key=lambda x: x.get("recorded_at", ""),
            reverse=True
        )
        
        if limit > 0:
            trades = trades[:limit]
        
        logger.info(f"✅ Historial cargado: {len(trades)} trades")
        return trades
        
    except Exception as e:
        logger.error(f"❌ Error cargando historial: {e}")
        return []


def get_estadisticas_trades() -> Dict[str, Any]:
    """
    Calcula estadísticas del historial de trades.
    
    Returns:
        Diccionario con estadísticas:
        - total_trades: número total
        - trades_exitosos: trades con ganancia > 0
        - trades_perdidos: trades con ganancia < 0
        - ganancia_total: suma de ganancias
        - win_rate: porcentaje de trades exitosos
        - roi_promedio: ROI promedio en %
    """
    trades = cargar_historial()
    
    if not trades:
        return {
            "total_trades": 0,
            "trades_exitosos": 0,
            "trades_perdidos": 0,
            "ganancia_total": 0.0,
            "win_rate": 0.0,
            "roi_promedio": 0.0,
        }
    
    total = len(trades)
    exitosos = sum(1 for t in trades if t.get("ganancia", 0) > 0)
    perdidos = sum(1 for t in trades if t.get("ganancia", 0) < 0)
    ganancia_total = sum(t.get("ganancia", 0) for t in trades)
    
    win_rate = (exitosos / total * 100) if total > 0 else 0
    roi_promedio = (
        sum(t.get("roi_percent", 0) for t in trades) / total
    ) if total > 0 else 0
    
    return {
        "total_trades": total,
        "trades_exitosos": exitosos,
        "trades_perdidos": perdidos,
        "ganancia_total": ganancia_total,
        "win_rate": win_rate,
        "roi_promedio": roi_promedio,
    }


# ============================================
# UTILIDADES
# ============================================

def _is_valid_solana_address(address: str) -> bool:
    """
    Valida que una dirección sea un address válido de Solana.
    
    Args:
        address: String a validar
        
    Returns:
        True si es válido (base58, 32-44 caracteres)
    """
    if not address:
        return False
    
    address = address.strip()
    
    # Longitud válida para direcciones de Solana
    if len(address) < 32 or len(address) > 44:
        return False
    
    # Caracteres base58 válidos
    # 123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz
    base58_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    
    return all(c in base58_chars for c in address)


def limpiar_archivos() -> Dict[str, bool]:
    """
    Limpia todos los archivos de datos del bot.
    
    ⚠️ CUIDADO: Esta función elimina datos.
    
    Returns:
        Diccionario con resultado de cada limpieza
    """
    results = {}
    
    files_to_clean = [
        CONFIG_FILE,
        WATCHLIST_FILE,
        TRADES_FILE,
    ]
    
    for filepath in files_to_clean:
        try:
            if filepath.exists():
                filepath.unlink()
                results[str(filepath)] = True
                logger.info(f"🗑️ Eliminado: {filepath}")
            else:
                results[str(filepath)] = True  # No existía, OK
        except Exception as e:
            results[str(filepath)] = False
            logger.error(f"❌ Error eliminando {filepath}: {e}")
    
    return results


def get_espacio_usado() -> Dict[str, Any]:
    """
    Calcula el espacio en disco usado por los archivos del bot.
    
    Returns:
        Diccionario con info de espacio
    """
    total_size = 0
    file_info = {}
    
    for filepath in [CONFIG_FILE, WATCHLIST_FILE, TRADES_FILE, LOGS_FILE]:
        if filepath.exists():
            size = filepath.stat().st_size
            total_size += size
            file_info[str(filepath)] = {
                "size_bytes": size,
                "size_kb": round(size / 1024, 2),
            }
    
    return {
        "total_bytes": total_size,
        "total_kb": round(total_size / 1024, 2),
        "files": file_info,
    }


# ============================================
# SYNC CON BOTCONFIG
# ============================================

def sync_from_botconfig(config: BotConfig) -> bool:
    """
    Sincroniza la configuración desde BotConfig a archivos JSON.
    
    Args:
        config: Instancia de BotConfig a sincronizar
        
    Returns:
        True si toda la sincronización fue exitosa
    """
    results = []
    
    # Guardar config principal
    results.append(guardar_config_dex(config.to_dict()))
    
    # Guardar watchlist
    results.append(guardar_watchlist(config.dex_screener.watchlist))
    
    return all(results)


def sync_to_botconfig() -> BotConfig:
    """
    Carga configuración desde archivos JSON a BotConfig.
    
    Returns:
        Nueva instancia de BotConfig con datos cargados
    """
    config = BotConfig()
    
    # Cargar config DexScreener
    dex_config = cargar_config_dex()
    if "dex_screener" in dex_config:
        for key, value in dex_config["dex_screener"].items():
            if hasattr(config.dex_screener, key):
                setattr(config.dex_screener, key, value)
    
    if "loop" in dex_config:
        for key, value in dex_config["loop"].items():
            if hasattr(config.loop, key):
                setattr(config.loop, key, value)
    
    # Cargar watchlist
    config.dex_screener.watchlist = cargar_watchlist()
    
    return config


# ============================================
# EJEMPLO DE USO
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("  STORAGE MODULE - TEST")
    print("=" * 60)
    
    # Test guardar config
    print("\n📝 Guardando configuración...")
    test_config = get_default_dex_config()
    test_config["dex_screener"]["min_liquidity_usd"] = 75000
    result = guardar_config_dex(test_config)
    print(f"  Resultado: {'✅' if result else '❌'}")
    
    # Test cargar config
    print("\n📖 Cargando configuración...")
    loaded = cargar_config_dex()
    print(f"  Min liquidez: ${loaded['dex_screener']['min_liquidity_usd']:,.0f}")
    
    # Test watchlist
    print("\n📋 Guardando watchlist...")
    test_tokens = [
        "So11111111111111111111111111111111111111112",
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    ]
    guardar_watchlist(test_tokens)
    
    print("\n📋 Cargando watchlist...")
    tokens = cargar_watchlist()
    print(f"  Tokens: {tokens}")
    
    # Test validar dirección
    print("\n🔍 Validando direcciones...")
    test_addresses = [
        "So11111111111111111111111111111111111111112",
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "invalid_address_too_short",
        "",
    ]
    for addr in test_addresses:
        valid = _is_valid_solana_address(addr)
        print(f"  {addr[:20] if addr else '(vacío)':<25} -> {'✅' if valid else '❌'}")
    
    # Test espacio usado
    print("\n💾 Espacio usado:")
    espacio = get_espacio_usado()
    print(f"  Total: {espacio['total_kb']} KB")
    for path, info in espacio["files"].items():
        print(f"    {Path(path).name}: {info['size_kb']} KB")
    
    print("\n" + "=" * 60)
