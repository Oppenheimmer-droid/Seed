"""
Solana Memecoin Bot - Trading Bot for Solana memecoins.

A high-risk trading bot that implements a bullish martingale strategy
with security filters for trading memecoins on Solana DEXes.
"""

__version__ = "1.1.0"
__author__ = "OpenHands Agent"
__compatibility__ = "Python 3.13, ARM64, Termux/Android"

from solana_bot.config.bot_config import BotConfig, config, init_config
from solana_bot.clients.dexscreener import DexScreenerClient
from solana_bot.menu.interactive import main as run_menu

__all__ = [
    "BotConfig",
    "config",
    "init_config",
    "DexScreenerClient",
    "run_menu",
]