"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    CONFIGURACIÓN DEL BOT                                ║
║          Configuración unificada para Solana Memecoin Bot               ║
║          Compatible con ARM64 / Termux / Python 3.13                   ║
╚══════════════════════════════════════════════════════════════════════════╝

Este módulo contiene la configuración central del bot, incluyendo:
- Parámetros de trading
- Filtros de seguridad
- Configuración de DexScreener
- Configuración de Birdeye
- Parámetros del loop de trading

La configuración puede cargarse desde variables de entorno o archivos JSON.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ============================================
# RUTAS POR DEFECTO
# ============================================

DEFAULT_CONFIG_DIR = Path.home() / ".solana_memebot"
DEFAULT_DEX_CONFIG_FILE = DEFAULT_CONFIG_DIR / "dex_config.json"
DEFAULT_WATCHLIST_FILE = DEFAULT_CONFIG_DIR / "watchlist.json"
DEFAULT_TRADES_FILE = DEFAULT_CONFIG_DIR / "trades.json"


# ============================================
# CONFIGURACIÓN DE CAPITAL Y TRADING
# ============================================

@dataclass
class CapitalConfig:
    """Configuración de capital y límites de trading."""
    capital_inicial: float = 500.0
    objetivo_global: float = 615.0  # +23% profit objetivo
    stop_loss_global: float = 100.0  # -80% pérdida máxima
    inversion_base: float = 100.0
    max_entradas_por_token: int = 5
    max_posiciones_simultaneas: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "CapitalConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============================================
# CONFIGURACIÓN DE FILTROS
# ============================================

@dataclass
class FiltersConfig:
    """Configuración de filtros de seguridad para entrada de tokens."""
    # Filtros de mercado
    pump_minimo_percent: float = 1.00
    umbral_martingala_percent: float = 0.10
    caida_minima_salida_percent: float = 0.03

    # Filtros de calidad del token
    liquidez_minima_sol: float = 10.0
    holders_minimos: int = 100
    pool_age_minimo_seconds: int = 120
    top_holder_maximo_percent: float = 0.20
    volumen_5min_minimo_sol: float = 50.0
    precio_minimo_sol: float = 0.000001

    # Filtros de tax
    sell_tax_maximo: float = 0.10
    buy_tax_maximo: float = 0.10

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "FiltersConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============================================
# CONFIGURACIÓN DEXSCREENER
# ============================================

@dataclass
class DexScreenerConfig:
    """Configuración específica para DexScreener."""
    enabled: bool = True
    priority: str = "hybrid"  # "birdeye" | "dexscreener" | "hybrid"
    
    # Filtros cuantitativos
    min_liquidity_usd: float = 50000
    min_volume_5m_usd: float = 10000
    max_age_minutes: int = 60
    min_holders: int = 100
    max_top_holder_pct: float = 0.20
    
    # DEXs permitidos (whitelist)
    dex_whitelist: List[str] = field(default_factory=lambda: [
        "raydium", "meteora", "pump.fun", "orca", "fluxbeam"
    ])
    
    # Watchlist de tokens
    watchlist: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "DexScreenerConfig":
        # Filtrar campos desconocidos
        valid_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# ============================================
# CONFIGURACIÓN DE RED / APIs
# ============================================

@dataclass
class NetworkConfig:
    """Configuración de red y APIs externas."""
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    jupiter_api_url: str = "https://quote-api.jup.ag/v6"
    birdeye_api_url: str = "https://public-api.birdeye.so"
    birdeye_api_key: str = ""
    wallet_private_key: str = ""
    sol_mint: str = "So11111111111111111111111111111111111111112"
    slippage_bps_compra: int = 300
    slippage_bps_venta: int = 500
    priority_fee: int = 100_000
    loop_interval: float = 2.0
    log_file: str = "trading_bot.log"
    log_level: str = "INFO"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "NetworkConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def __post_init__(self):
        # Sobrescribir con variables de entorno si existen
        self.solana_rpc_url = os.getenv("SOLANA_RPC_URL", self.solana_rpc_url)
        self.birdeye_api_key = os.getenv("BIRDEYE_API_KEY", self.birdeye_api_key)
        self.wallet_private_key = os.getenv("WALLET_PRIVATE_KEY", self.wallet_private_key)


# ============================================
# CONFIGURACIÓN DEL LOOP DE TRADING
# ============================================

@dataclass
class LoopConfig:
    """Configuración del loop perpetuo de trading."""
    capital_operativo_base: float = 100.0
    extraccion_por_ciclo: float = 15.0
    stop_ciclo: float = -50.0
    max_ciclos_sin_profit: int = 5
    tiempo_espera_entre_ciclos: int = 60  # segundos

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "LoopConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============================================
# CONFIGURACIÓN COMPLETA DEL BOT
# ============================================

@dataclass
class BotConfig:
    """
    Configuración unificada del bot.
    
    Combina todas las secciones de configuración en un solo lugar.
    Puede cargarse desde/guardarse a archivos JSON.
    """
    capital: CapitalConfig = field(default_factory=CapitalConfig)
    filters: FiltersConfig = field(default_factory=FiltersConfig)
    dex_screener: DexScreenerConfig = field(default_factory=DexScreenerConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    loop: LoopConfig = field(default_factory=LoopConfig)
    dry_run: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la config a diccionario anidado."""
        return {
            "capital": self.capital.to_dict(),
            "filters": self.filters.to_dict(),
            "dex_screener": self.dex_screener.to_dict(),
            "network": self.network.to_dict(),
            "loop": self.loop.to_dict(),
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "BotConfig":
        """Crea BotConfig desde diccionario."""
        return cls(
            capital=CapitalConfig.from_dict(data.get("capital", {})),
            filters=FiltersConfig.from_dict(data.get("filters", {})),
            dex_screener=DexScreenerConfig.from_dict(data.get("dex_screener", {})),
            network=NetworkConfig.from_dict(data.get("network", {})),
            loop=LoopConfig.from_dict(data.get("loop", {})),
            dry_run=data.get("dry_run", True),
        )

    def save(self, filepath: Optional[Path] = None) -> None:
        """Guarda la configuración a archivo JSON."""
        if filepath is None:
            filepath = DEFAULT_DEX_CONFIG_FILE
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Configuración guardada en {filepath}")

    @classmethod
    def load(cls, filepath: Optional[Path] = None) -> "BotConfig":
        """Carga la configuración desde archivo JSON."""
        if filepath is None:
            filepath = DEFAULT_DEX_CONFIG_FILE
        
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"⚠️ Archivo de config no existe: {filepath}")
            logger.info("Usando configuración por defecto")
            return cls()
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"✅ Configuración cargada desde {filepath}")
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando config JSON: {e}")
            return cls()
        except Exception as e:
            logger.error(f"❌ Error cargando config: {e}")
            return cls()

    def update_from_env(self) -> None:
        """Actualiza valores desde variables de entorno."""
        self.network.solana_rpc_url = os.getenv(
            "SOLANA_RPC_URL", self.network.solana_rpc_url
        )
        self.network.birdeye_api_key = os.getenv(
            "BIRDEYE_API_KEY", self.network.birdeye_api_key
        )
        self.network.wallet_private_key = os.getenv(
            "WALLET_PRIVATE_KEY", self.network.wallet_private_key
        )
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"


# ============================================
# CONFIGURACIÓN LEGACY (compatibilidad)
# ============================================

# Mantener compatibilidad con el archivo original solana_bot_complete.py
LEGACY_CONFIG_MAPPING = {
    "CAPITAL_INICIAL": ("capital", "capital_inicial"),
    "OBJETIVO_GLOBAL": ("capital", "objetivo_global"),
    "STOP_LOSS_GLOBAL": ("capital", "stop_loss_global"),
    "INVERSION_BASE": ("capital", "inversion_base"),
    "MAX_ENTRADAS_POR_TOKEN": ("capital", "max_entradas_por_token"),
    "MAX_POSICIONES_SIMULTANEAS": ("capital", "max_posiciones_simultaneas"),
    "LIQUIDEZ_MINIMA_SOL": ("filters", "liquidez_minima_sol"),
    "HOLDERS_MINIMOS": ("filters", "holders_minimos"),
    "POOL_AGE_MINIMO_SECONDS": ("filters", "pool_age_minimo_seconds"),
    "TOP_HOLDER_MAXIMO_PERCENT": ("filters", "top_holder_maximo_percent"),
    "VOLUMEN_5MIN_MINIMO_SOL": ("filters", "volumen_5min_minimo_sol"),
    "PRECIO_MINIMO_SOL": ("filters", "precio_minimo_sol"),
    "SELL_TAX_MAXIMO": ("filters", "sell_tax_maximo"),
    "BUY_TAX_MAXIMO": ("filters", "buy_tax_maximo"),
    "SOLANA_RPC_URL": ("network", "solana_rpc_url"),
    "BIRDEYE_API_KEY": ("network", "birdeye_api_key"),
    "WALLET_PRIVATE_KEY": ("network", "wallet_private_key"),
    "SLIPPAGE_BPS_COMPRA": ("network", "slippage_bps_compra"),
    "SLIPPAGE_BPS_VENTA": ("network", "slippage_bps_venta"),
    "PRIORITY_FEE": ("network", "priority_fee"),
    "LOOP_INTERVAL": ("network", "loop_interval"),
}


def legacy_to_new_config(legacy_dict: Dict[str, Any]) -> BotConfig:
    """Convierte configuración legacy (del archivo original) al nuevo formato."""
    new_config = BotConfig()
    
    for legacy_key, (section, new_key) in LEGACY_CONFIG_MAPPING.items():
        if legacy_key in legacy_dict:
            value = legacy_dict[legacy_key]
            section_obj = getattr(new_config, section)
            if hasattr(section_obj, new_key):
                setattr(section_obj, new_key, value)
    
    return new_config


# ============================================
# INSTANCIA GLOBAL
# ============================================

# Configuración global del bot
config = BotConfig()


def init_config() -> BotConfig:
    """Inicializa la configuración desde archivo o variables de entorno."""
    global config
    
    # Intentar cargar desde archivo
    if DEFAULT_DEX_CONFIG_FILE.exists():
        config = BotConfig.load(DEFAULT_DEX_CONFIG_FILE)
    else:
        config = BotConfig()
    
    # Actualizar desde entorno
    config.update_from_env()
    
    return config


# ============================================
# EJEMPLO DE USO
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("  BOT CONFIG - TEST")
    print("=" * 60)

    # Crear config de ejemplo
    cfg = BotConfig()
    
    # Modificar algunos valores
    cfg.dex_screener.enabled = True
    cfg.dex_screener.priority = "hybrid"
    cfg.dex_screener.min_liquidity_usd = 50000
    cfg.dex_screener.watchlist = [
        "So11111111111111111111111111111111111111112",
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    ]
    
    # Guardar
    cfg.save()
    print(f"✅ Config guardada en {DEFAULT_DEX_CONFIG_FILE}")
    
    # Recargar
    loaded = BotConfig.load()
    print(f"\n📋 Configuración cargada:")
    print(f"   Prioridad DexScreener: {loaded.dex_screener.priority}")
    print(f"   Min liquidez USD: ${loaded.dex_screener.min_liquidity_usd:,.0f}")
    print(f"   Tokens en watchlist: {len(loaded.dex_screener.watchlist)}")

    print("\n" + "=" * 60)
