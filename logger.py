# logger.py
# Logger optimizado para Termux con colores y archivos

import logging
import sys
import os
from datetime import datetime


class TermuxFormatter(logging.Formatter):
    ICONS = {
        'DEBUG': '·',
        'INFO': '→',
        'WARNING': '⚠️ ',
        'ERROR': '❌',
        'CRITICAL': '🚨',
    }
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
    }
    RESET = '\033[0m'

    def format(self, record):
        icon = self.ICONS.get(record.levelname, '·')
        color = self.COLORS.get(record.levelname, '')
        hora = datetime.now().strftime('%H:%M:%S')
        return f"{color}{hora} {icon}  {record.getMessage()}{self.RESET}"


def make_logger(name="SolanaBot"):
    os.makedirs("logs", exist_ok=True)
    lg = logging.getLogger(name)
    lg.setLevel(logging.DEBUG)
    if lg.handlers:
        return lg

    # Consola: INFO+ con colores
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(TermuxFormatter())

    # Archivo: DEBUG+ sin colores
    fh = logging.FileHandler("logs/bot.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        '%Y-%m-%d %H:%M:%S'
    ))

    lg.addHandler(ch)
    lg.addHandler(fh)
    return lg


def log_accion(lg, tipo: str, token: str, precio: float, extra: str = ""):
    """Log de eventos de trading — visible en pantalla Termux"""
    ESTILOS = {
        "PUMP": ("🚀", "\033[92m"),
        "COMPRA": ("💰", "\033[92m"),
        "VENTA": ("💸", "\033[93m"),
        "WIN": ("✅", "\033[92m"),
        "LOSS": ("❌", "\033[91m"),
        "FILTRO": ("🛡️ ", "\033[96m"),
        "ESTADO": ("📊", "\033[97m"),
        "ALERTA": ("⚠️ ", "\033[93m"),
    }
    icon, color = ESTILOS.get(tipo, ("·", ""))
    tk = token[:8] if token else "--------"
    rst = "\033[0m"
    msg = f"{icon} {tipo:7s} | {tk}... | {precio:.8f} SOL"
    if extra:
        msg += f" | {extra}"
    lg.info(f"{color}{msg}{rst}")
