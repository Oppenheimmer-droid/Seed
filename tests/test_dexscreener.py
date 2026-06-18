"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    PRUEBAS UNITARIAS                                     ║
║          Tests para el cliente DexScreener y menú interactivo            ║
║          Compatible con ARM64 / Termux / Python 3.13                   ║
╚══════════════════════════════════════════════════════════════════════════╝

Tests incluidos:
- Test del cliente DexScreener (con mocks)
- Test del menú interactivo (simulación offline)
- Test de validación de direcciones Solana

Ejecución:
    python -m pytest tests/test_dexscreener.py -v
    python -m unittest tests.test_dexscreener -v
"""

import asyncio
import json
import os
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from typing import Dict
from unittest.mock import AsyncMock, MagicMock, patch

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from solana_bot.clients.dexscreener import (
    BASE_URL,
    DexPair,
    DexScreenerClient,
    get_token_info_sync,
    search_tokens_sync,
)


# ============================================
# DATOS MOCK PARA TESTS
# ============================================

MOCK_TOKEN_RESPONSE = {
    "pairs": [
        {
            "chainId": "solana",
            "dexId": "raydium",
            "pairAddress": "RswpKmFoMXrAT5qS2ujz5VFYKz4FnRJqJjcToNmeW5B",
            "baseToken": {
                "address": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",
                "symbol": "MEME",
                "name": "Memecoin Test"
            },
            "quoteToken": {
                "address": "So11111111111111111111111111111111111111112",
                "symbol": "SOL"
            },
            "priceUsd": "0.00012345",
            "liquidity": {"usd": 150000.50},
            "volume": {"h24": 2500000, "m5": 50000},
            "fdv": 1234567890,
            "pairCreatedAt": 1700000000,
            "info": {"ageMin": 30},
            "priceChange": {
                "m5": 2.5,
                "h1": 5.2,
                "h6": -1.5,
                "h24": 10.3
            }
        }
    ]
}

MOCK_SEARCH_RESPONSE = {
    "pairs": [
        {
            "chainId": "solana",
            "dexId": "raydium",
            "pairAddress": "Pair1",
            "baseToken": {"address": "Addr1", "symbol": "DOGE", "name": "Dogecoin"},
            "quoteToken": {"address": "So111...", "symbol": "SOL"},
            "priceUsd": "0.0001",
            "liquidity": {"usd": 100000},
            "volume": {"h24": 500000, "m5": 10000},
            "pairCreatedAt": 1700000000,
        },
        {
            "chainId": "solana",
            "dexId": "orca",
            "pairAddress": "Pair2",
            "baseToken": {"address": "Addr2", "symbol": "PEPE", "name": "Pepe"},
            "quoteToken": {"address": "So111...", "symbol": "SOL"},
            "priceUsd": "0.00002",
            "liquidity": {"usd": 50000},
            "volume": {"h24": 200000, "m5": 5000},
            "pairCreatedAt": 1700000500,
        }
    ]
}


# ============================================
# TESTS DEL CLIENTE DEXSCREENER
# ============================================

class TestDexScreenerClient(unittest.TestCase):
    """Tests para DexScreenerClient."""

    def setUp(self):
        """Set up del test."""
        self.client = DexScreenerClient(timeout=5.0, max_retries=2)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up del test."""
        self.loop.close()

    def test_client_init(self):
        """Test de inicialización del cliente."""
        self.assertEqual(self.client.timeout, 5.0)
        self.assertEqual(self.client.max_retries, 2)
        self.assertIsNone(self.client._session)

    def test_dexpair_from_dict_valid(self):
        """Test de creación de DexPair desde dict válido."""
        pair = DexPair.from_dict(MOCK_TOKEN_RESPONSE["pairs"][0])
        
        self.assertIsNotNone(pair)
        self.assertEqual(pair.chain_id, "solana")
        self.assertEqual(pair.dex_id, "raydium")
        self.assertEqual(pair.base_token_symbol, "MEME")
        self.assertEqual(pair.base_token_address, "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr")
        self.assertAlmostEqual(pair.price_usd, 0.00012345, places=6)
        self.assertEqual(pair.liquidity_usd, 150000.50)
        self.assertEqual(pair.volume_m5, 50000)
        self.assertEqual(pair.pair_created_at, 1700000000)
        self.assertEqual(pair.price_change_m5, 2.5)

    def test_dexpair_from_dict_invalid(self):
        """Test de DexPair con datos inválidos."""
        invalid_data = {"invalid": "data"}
        pair = DexPair.from_dict(invalid_data)
        # Con datos mínimos retorna un DexPair con valores por defecto
        self.assertIsNotNone(pair)
        self.assertEqual(pair.base_token_address, "")

    def test_dexpair_to_token_data_dict(self):
        """Test de conversión al formato TokenData del bot."""
        pair = DexPair.from_dict(MOCK_TOKEN_RESPONSE["pairs"][0])
        token_data = pair.to_token_data_dict()
        
        self.assertEqual(token_data["mint"], "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr")
        self.assertEqual(token_data["symbol"], "MEME")
        self.assertEqual(token_data["price_current"], 0.00012345)
        self.assertEqual(token_data["dex_id"], "raydium")

    @patch("solana_bot.clients.dexscreener.httpx.AsyncClient")
    def test_get_token_info_success(self, mock_client_class):
        """Test de get_token_info con respuesta exitosa."""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_TOKEN_RESPONSE
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Ejecutar
        result = self.loop.run_until_complete(
            self.client.get_token_info("7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr")
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.base_token_symbol, "MEME")
        mock_client.get.assert_called_once()

    @patch("solana_bot.clients.dexscreener.httpx.AsyncClient")
    def test_get_token_info_not_found(self, mock_client_class):
        """Test de get_token_info con token no encontrado."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client
        
        result = self.loop.run_until_complete(
            self.client.get_token_info("invalid_address")
        )
        
        self.assertIsNone(result)

    @patch("solana_bot.clients.dexscreener.httpx.AsyncClient")
    def test_search_tokens_success(self, mock_client_class):
        """Test de search_tokens con respuesta exitosa."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SEARCH_RESPONSE
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client
        
        result = self.loop.run_until_complete(
            self.client.search_tokens("DOGE", limit=10)
        )
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].base_token_symbol, "DOGE")
        self.assertEqual(result[1].base_token_symbol, "PEPE")

    def test_get_token_info_empty_address(self):
        """Test de get_token_info con dirección vacía."""
        result = self.loop.run_until_complete(
            self.client.get_token_info("")
        )
        self.assertIsNone(result)

    def test_search_tokens_empty_query(self):
        """Test de search_tokens con query vacía."""
        result = self.loop.run_until_complete(
            self.client.search_tokens("")
        )
        self.assertEqual(result, [])


class TestDexPairFactory(unittest.TestCase):
    """Tests adicionales para DexPair factory."""

    def test_from_dict_with_missing_fields(self):
        """Test con campos opcionales faltantes."""
        minimal_data = {
            "chainId": "solana",
            "baseToken": {"address": "test", "symbol": "TST"},
        }
        pair = DexPair.from_dict(minimal_data)
        
        self.assertIsNotNone(pair)
        self.assertEqual(pair.chain_id, "solana")
        self.assertEqual(pair.price_usd, 0.0)
        self.assertEqual(pair.liquidity_usd, 0.0)

    def test_from_dict_with_none_values(self):
        """Test con valores None en campos numéricos."""
        data = {
            "chainId": "solana",
            "priceUsd": None,
            "liquidity": None,
            "baseToken": {"address": "test", "symbol": "TST"},
        }
        pair = DexPair.from_dict(data)
        
        self.assertIsNotNone(pair)
        self.assertEqual(pair.price_usd, 0.0)


class TestSyncWrappers(unittest.TestCase):
    """Tests para wrappers sincrónicos."""

    def setUp(self):
        """Set up del test."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up del test."""
        self.loop.close()

    @patch("solana_bot.clients.dexscreener.DexScreenerClient.get_token_info")
    def test_get_token_info_sync(self, mock_get_info):
        """Test del wrapper sincrónico."""
        mock_pair = DexPair(
            chain_id="solana",
            dex_id="raydium",
            pair_address="test",
            base_token_address="test",
            base_token_symbol="TEST",
        )
        mock_get_info.return_value = mock_pair
        
        result = get_token_info_sync("test_address")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["base_token_symbol"], "TEST")

    @patch("solana_bot.clients.dexscreener.DexScreenerClient.search_tokens")
    def test_search_tokens_sync(self, mock_search):
        """Test del wrapper sincrónico de búsqueda."""
        mock_pairs = [
            DexPair(
                chain_id="solana",
                dex_id="raydium",
                pair_address="test",
                base_token_address="test",
                base_token_symbol="TEST",
            )
        ]
        mock_search.return_value = mock_pairs
        
        result = search_tokens_sync("TEST")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["base_token_symbol"], "TEST")


# ============================================
# TESTS DE VALIDACIÓN DE DIRECCIONES
# ============================================

class TestAddressValidation(unittest.TestCase):
    """Tests para validación de direcciones Solana."""

    def test_valid_addresses(self):
        """Test con direcciones válidas."""
        valid_addresses = [
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",  # Ejemplo
            "A" * 44,  # Longitud máxima
            "1" * 32,  # Longitud mínima
        ]
        
        from solana_bot.storage import _is_valid_solana_address
        
        for addr in valid_addresses:
            self.assertTrue(
                _is_valid_solana_address(addr),
                f"Dirección debería ser válida: {addr}"
            )

    def test_invalid_addresses(self):
        """Test con direcciones inválidas."""
        invalid_addresses = [
            "",  # Vacía
            "x" * 31,  # Muy corta
            "x" * 45,  # Muy larga
            "0" * 35,  # Caracteres inválidos (0, O, I, l)
            " abc",  # Con espacios
        ]
        
        from solana_bot.storage import _is_valid_solana_address
        
        for addr in invalid_addresses:
            self.assertFalse(
                _is_valid_solana_address(addr),
                f"Dirección debería ser inválida: {addr}"
            )


# ============================================
# TESTS DE STORAGE
# ============================================

class TestStorage(unittest.TestCase):
    """Tests para el módulo de almacenamiento."""

    def setUp(self):
        """Set up con directorio temporal."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_home = os.environ.get("HOME", "")
        os.environ["HOME"] = self.temp_dir

    def tearDown(self):
        """Clean up."""
        os.environ["HOME"] = self.original_home
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_config_structure(self):
        """Test de estructura de configuración por defecto."""
        from solana_bot.storage import get_default_dex_config
        
        config = get_default_dex_config()
        
        self.assertIn("dex_screener", config)
        self.assertIn("loop", config)
        self.assertEqual(config["dex_screener"]["priority"], "birdeye")
        self.assertEqual(config["dex_screener"]["min_liquidity_usd"], 50000)

    def test_save_and_load_config(self):
        """Test de guardar y cargar configuración."""
        from solana_bot.storage import (
            guardar_config_dex,
            cargar_config_dex,
            get_default_dex_config,
        )
        
        test_config = get_default_dex_config()
        test_config["dex_screener"]["min_liquidity_usd"] = 99999
        
        # Guardar
        result = guardar_config_dex(test_config)
        self.assertTrue(result)
        
        # Cargar
        loaded = cargar_config_dex()
        self.assertEqual(loaded["dex_screener"]["min_liquidity_usd"], 99999)

    def test_watchlist_operations(self):
        """Test de operaciones de watchlist."""
        from solana_bot.storage import (
            guardar_watchlist,
            cargar_watchlist,
            agregar_a_watchlist,
            eliminar_de_watchlist,
            APP_DIR,
        )
        
        # Ensure directory exists
        APP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Guardar watchlist inicial (with valid addresses)
        tokens = [
            "7nE5GbJ7uM8xM4KVNrWqVDEsKRqYXeJFHYPGrZLf2m9",
            "4nHFZGNPWT7XGwR7NPVkKD3F36kBvr2dVbPv3F8Rpwp",
            "8nHFZGNPWT7XGwR7NPVkKD3F36kBvr2dVbPv3F8Rpwp"
        ]
        guardar_watchlist(tokens)
        
        # Cargar
        loaded = cargar_watchlist()
        self.assertEqual(len(loaded), 3)
        
        # Agregar
        agregar_a_watchlist("9nHFZGNPWT7XGwR7NPVkKD3F36kBvr2dVbPv3F8Rpwp")
        loaded = cargar_watchlist()
        self.assertEqual(len(loaded), 4)
        
        # Eliminar
        eliminar_de_watchlist(tokens[1])
        loaded = cargar_watchlist()
        self.assertEqual(len(loaded), 3)
        self.assertNotIn(tokens[1], loaded)


# ============================================
# TESTS DE CONFIG
# ============================================

class TestBotConfig(unittest.TestCase):
    """Tests para BotConfig."""

    def test_config_to_dict(self):
        """Test de conversión a diccionario."""
        from solana_bot.config.bot_config import BotConfig
        
        config = BotConfig()
        config_dict = config.to_dict()
        
        self.assertIn("capital", config_dict)
        self.assertIn("filters", config_dict)
        self.assertIn("dex_screener", config_dict)
        self.assertIn("network", config_dict)
        self.assertIn("loop", config_dict)

    def test_config_from_dict(self):
        """Test de creación desde diccionario."""
        from solana_bot.config.bot_config import BotConfig
        
        data = {
            "capital": {"capital_inicial": 1000.0},
            "filters": {"liquidez_minima_sol": 50.0},
            "dex_screener": {"enabled": True, "priority": "dexscreener"},
            "network": {},
            "loop": {},
            "dry_run": False,
        }
        
        config = BotConfig.from_dict(data)
        
        self.assertEqual(config.capital.capital_inicial, 1000.0)
        self.assertEqual(config.filters.liquidez_minima_sol, 50.0)
        self.assertEqual(config.dex_screener.priority, "dexscreener")
        self.assertFalse(config.dry_run)


# ============================================
# EJECUTOR DE TESTS
# ============================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
