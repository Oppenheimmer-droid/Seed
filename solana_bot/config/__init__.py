"""
Config package for Solana Memecoin Bot.
"""

from solana_bot.config.bot_config import (
    BotConfig,
    CapitalConfig,
    DexScreenerConfig,
    FiltersConfig,
    LoopConfig,
    NetworkConfig,
    config,
    init_config,
    legacy_to_new_config,
    DEFAULT_CONFIG_DIR,
    DEFAULT_DEX_CONFIG_FILE,
    DEFAULT_WATCHLIST_FILE,
    DEFAULT_TRADES_FILE,
)

__all__ = [
    "BotConfig",
    "CapitalConfig", 
    "DexScreenerConfig",
    "FiltersConfig",
    "LoopConfig",
    "NetworkConfig",
    "config",
    "init_config",
    "legacy_to_new_config",
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_DEX_CONFIG_FILE",
    "DEFAULT_WATCHLIST_FILE",
    "DEFAULT_TRADES_FILE",
]