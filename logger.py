#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║          LOGGER v0.2 - Optimizado para Termux/Android                   ║
║          Formato compacto, colores ANSI, logs en pantalla y archivo     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


# ============================================
# FORMATTER PARA TERMINAL MÓVIL
# ============================================

class TermuxFormatter(logging.Formatter):
    """Formatter optimizado para pantalla pequeña de móvil"""
    
    ICONS = {
        'DEBUG':    '·',
        'INFO':     '→',
        'WARNING':  '⚠️ ',
        'ERROR':    '❌',
        'CRITICAL': '🚨',
    }
    
    COLORS = {
        'DEBUG':    '\033[36m',      # Cyan
        'INFO':     '\033[32m',      # Green
        'WARNING':  '\033[33m',      # Yellow
        'ERROR':    '\033[31m',      # Red
        'CRITICAL': '\033[35m',      # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        icon  = self.ICONS.get(record.levelname, '·')
        color = self.COLORS.get(record.levelname, '')
        hora  = datetime.now().strftime('%H:%M:%S')
        msg   = record.getMessage()
        
        # Línea compacta para móvil
        return f"{color}{hora} {icon} {msg}{self.RESET}"


class FileFormatter(logging.Formatter):
    """Formatter para archivo de logs"""
    
    def format(self, record):
        hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        msg = record.getMessage()
        return f"{hora} [{level:8}] {msg}"


# ============================================
# FACTORY DE LOGGER
# ============================================

def make_logger(
    name: str = "SolanaBot",
    log_file: str = None,
    log_dir: str = "logs",
    level: int = logging.DEBUG
) -> logging.Logger:
    """
    Crea logger optimizado para Termux.
    - Consola: solo INFO y superior (formato compacto)
    - Archivo: DEBUG y superior (historial completo)
    """
    
    # Crear directorio de logs
    if log_file is None:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "bot.log")
    else:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Limpiar handlers existentes
    logger.handlers.clear()
    
    # Handler consola — INFO y superior (formato compacto)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(TermuxFormatter())
    
    # Handler archivo — DEBUG y superior
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(FileFormatter())
    
    logger.addHandler(console)
    logger.addHandler(file_handler)
    
    return logger


# ============================================
# LOGGING DE EVENTOS ESPECÍFICOS
# ============================================

EVENTOS_COLORES = {
    "PUMP":     ("🚀", "\033[32m"),   # Verde
    "COMPRA":   ("💰", "\033[32m"),   # Verde
    "VENTA":    ("💸", "\033[33m"),   # Yellow
    "GANANCIA": ("✅", "\033[32m"),   # Verde
    "PERDIDA":  ("❌", "\033[31m"),   # Rojo
    "FILTRO":   ("🛡️ ", "\033[36m"), # Cyan
    "ESTADO":   ("📊", "\033[37m"),   # Blanco
    "TOKEN":    ("🪙", "\033[35m"),   # Magenta
    "ERROR":    ("⚠️ ", "\033[31m"),  # Rojo
    "INFO":     ("ℹ️ ", "\033[36m"),  # Cyan
}
RESET = "\033[0m"


def log_evento(logger: logging.Logger, tipo: str, token: str, precio: float = None, detalle: str = ""):
    """
    Log de evento con icono y color.
    Formato: HH:MM:SS ICONO [TIPO] token... @ precio detalle
    """
    icon, color = EVENTOS_COLORES.get(tipo, ("·", ""))
    token_short = token[:8] if token and len(token) > 8 else (token or "------")
    
    msg = f"[{tipo}] {token_short}"
    if precio is not None:
        msg += f" @ {precio:.8f}"
    if detalle:
        msg += f" {detalle}"
    
    logger.info(f"{color}{icon} {msg}{RESET}")


def log_trade(logger: logging.Logger, trade: dict):
    """Log simplificado de trade"""
    tipo = "GANANCIA" if trade.get("ganancia", 0) > 0 else "PERDIDA"
    log_evento(
        logger, tipo,
        trade.get("token_mint", "N/A")[:8],
        trade.get("precio_salida", 0),
        f"ROI: {trade.get('roi_percent', 0):+.1f}%"
    )


def log_status(logger: logging.Logger, capital: float, posiciones: int, trades: int, ganancia: float):
    """Log de estado del bot"""
    emoji = "📈" if ganancia >= 0 else "📉"
    logger.info(
        f"{emoji} Capital: {capital:.2f} SOL | "
        f"Posiciones: {posiciones} | "
        f"Trades: {trades} | "
        f"Ganancia: {ganancia:+.2f} SOL"
    )


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 LOGGER TEST")
    print("=" * 60)
    
    # Crear logger de test
    logger = make_logger("TestBot")
    
    print("\n📱 Logs en consola (solo INFO+):")
    logger.debug("Este mensaje NO debe aparecer")
    logger.info("Este mensaje SÍ debe aparecer")
    logger.warning("⚠️  Warning test")
    logger.error("❌ Error test")
    
    print("\n🪙 Log de eventos:")
    log_evento(logger, "PUMP", "TokenXYZ123456", 0.00001, "Pump 150%")
    log_evento(logger, "COMPRA", "AnotherToken999", 0.00005, "50 SOL")
    log_evento(logger, "VENTA", "SoldToken777", 0.00008, "ROI +60%")
    log_evento(logger, "FILTRO", "RugToken111", None, "Liquidez muy baja")
    
    print("\n📊 Status:")
    log_status(logger, 523.45, 2, 15, 23.45)
    
    print("\n📁 Logs guardados en:", os.path.abspath("logs/bot.log"))
    
    print("\n" + "=" * 60)
    print("✅ LOGGER TEST COMPLETADO")
    print("=" * 60)