#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    VERIFICACIÓN DEXSCREENER                              ║
║          Script para verificar integración con DexScreener API           ║
╚══════════════════════════════════════════════════════════════════════════╝

Este script:
1. Hace una llamada real a get_token_info() para SOL
2. Imprime la respuesta formateada en consola
3. Valida que los campos requeridos existen
4. Prueba búsqueda de tokens
5. Genera reporte de verificación

Uso:
    python check_dexscreener.py
"""

import asyncio
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent))

from solana_bot.clients.dexscreener import (
    DexScreenerClient,
    get_token_info_sync,
    search_tokens_sync,
)


# ============================================
# CONFIGURACIÓN
# ============================================

# Tokens de prueba
TEST_TOKENS = [
    "So11111111111111111111111111111111111111112",  # SOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
    "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",  # MEME (ejemplo)
]

# Campos requeridos para validación
REQUIRED_FIELDS = [
    "chain_id",
    "dex_id",
    "base_token_address",
    "base_token_symbol",
    "price_usd",
    "liquidity_usd",
    "volume_m5",
]


# ============================================
# UTILIDADES DE FORMATEO
# ============================================

def print_header(text: str, width: int = 70) -> None:
    """Imprime header con borde."""
    print()
    print("=" * width)
    print(f"  {text}")
    print("=" * width)


def print_success(text: str) -> None:
    print(f"  ✅ {text}")


def print_error(text: str) -> None:
    print(f"  ❌ {text}")


def print_info(text: str) -> None:
    print(f"  ℹ️  {text}")


def print_warning(text: str) -> None:
    print(f"  ⚠️  {text}")


def validate_pair_fields(pair: Dict) -> tuple[bool, List[str]]:
    """
    Valida que el par tenga todos los campos requeridos.
    
    Returns:
        (es_valido, lista_errores)
    """
    errors = []
    
    for field in REQUIRED_FIELDS:
        if field not in pair:
            errors.append(f"Campo faltante: {field}")
    
    return len(errors) == 0, errors


# ============================================
# TESTS
# ============================================

async def test_get_token_info(client: DexScreenerClient) -> bool:
    """Test de obtención de info de token."""
    print_header("TEST: get_token_info()")
    
    all_passed = True
    
    for token_addr in TEST_TOKENS[:2]:  # Solo los primeros 2 para no saturar
        print(f"\n  🔍 Token: {token_addr[:16]}...")
        
        try:
            pair = await client.get_token_info(token_addr)
            
            if pair is None:
                print_error(f"  Token no encontrado: {token_addr[:16]}...")
                all_passed = False
                continue
            
            # Convertir a dict para validar
            pair_dict = asdict(pair)
            
            # Validar campos
            is_valid, errors = validate_pair_fields(pair_dict)
            
            if is_valid:
                print_success(f"  Campos válidos")
            else:
                print_error(f"  Errores: {', '.join(errors)}")
                all_passed = False
            
            # Mostrar info
            print(f"\n  📋 Información del token:")
            print(f"     Símbolo:     {pair.base_token_symbol}")
            print(f"     Nombre:      {pair.base_token_name or 'N/A'}")
            print(f"     Precio USD:  ${pair.price_usd:.10f}")
            print(f"     Liquidez:    ${pair.liquidity_usd:,.2f}")
            print(f"     Volumen 24h: ${pair.volume_h24:,.2f}")
            print(f"     Volumen 5m:  ${pair.volume_m5:,.2f}")
            print(f"     DEX:         {pair.dex_id}")
            print(f"     Age (min):   {pair.age_minutes}")
            print(f"     Change 5m:   {pair.price_change_m5:+.2f}%")
            print(f"     Change 24h: {pair.price_change_h24:+.2f}%")
            
        except Exception as e:
            print_error(f"  Error: {e}")
            all_passed = False
    
    return all_passed


async def test_search_tokens(client: DexScreenerClient) -> bool:
    """Test de búsqueda de tokens."""
    print_header("TEST: search_tokens()")
    
    search_queries = ["SOL", "DOGE", "meme"]
    
    all_passed = True
    
    for query in search_queries:
        print(f"\n  🔍 Buscando: '{query}'")
        
        try:
            pairs = await client.search_tokens(query, limit=5)
            
            if not pairs:
                print_warning(f"  No se encontraron resultados")
                continue
            
            print_success(f"  Encontrados: {len(pairs)} tokens")
            
            for i, pair in enumerate(pairs[:3], 1):
                print(f"\n     {i}. {pair.base_token_symbol or '?'}")
                print(f"        Precio: ${pair.price_usd:.10f}" if pair.price_usd > 0 else f"        Precio: N/A")
                print(f"        Liquidez: ${pair.liquidity_usd:,.0f}" if pair.liquidity_usd > 0 else f"        Liquidez: N/A")
                print(f"        DEX: {pair.dex_id}")
        
        except Exception as e:
            print_error(f"  Error: {e}")
            all_passed = False
    
    return all_passed


async def test_trending(client: DexScreenerClient) -> bool:
    """Test de tokens trending."""
    print_header("TEST: get_solana_trending()")
    
    print("\n  🔍 Obteniendo tokens trending...")
    
    try:
        pairs = await client.get_solana_trending(limit=10)
        
        if not pairs:
            print_warning("  No se pudieron obtener trending")
            return False
        
        print_success(f"  Obtenidos: {len(pairs)} tokens")
        
        print(f"\n  📊 Top 10 Tokens Trending:")
        print(f"  {'#':<3} {'Símbolo':<12} {'Precio':<20} {'Liquidez':<15} {'DEX':<10}")
        print(f"  {'-'*3} {'-'*12} {'-'*20} {'-'*15} {'-'*10}")
        
        for i, pair in enumerate(pairs[:10], 1):
            symbol = (pair.base_token_symbol or "?")[:12]
            price = f"${pair.price_usd:.8f}" if pair.price_usd > 0 else "N/A"
            liq = f"${pair.liquidity_usd:,.0f}" if pair.liquidity_usd > 0 else "N/A"
            dex = pair.dex_id[:10] if pair.dex_id else "?"
            
            print(f"  {i:<3} {symbol:<12} {price:<20} {liq:<15} {dex:<10}")
        
        return True
    
    except Exception as e:
        print_error(f"  Error: {e}")
        return False


async def test_token_data_conversion(client: DexScreenerClient) -> bool:
    """Test de conversión al formato TokenData del bot."""
    print_header("TEST: Conversión a TokenData")
    
    print("\n  🔍 Convirtiendo respuesta al formato TokenData...")
    
    try:
        pair = await client.get_token_info(TEST_TOKENS[0])
        
        if pair is None:
            print_error("  No se pudo obtener token para conversión")
            return False
        
        token_data = pair.to_token_data_dict()
        
        print_success("  Conversión exitosa")
        print(f"\n  📋 TokenData formateado:")
        
        for key, value in token_data.items():
            if isinstance(value, float):
                print(f"     {key}: {value:.8f}" if value < 1 else f"     {key}: {value}")
            else:
                print(f"     {key}: {value}")
        
        # Validar que tiene los campos necesarios
        required = ["mint", "symbol", "price_current", "liquidity_sol", "dex_id"]
        missing = [f for f in required if f not in token_data]
        
        if missing:
            print_error(f"  Campos faltantes: {', '.join(missing)}")
            return False
        
        print_success("  Todos los campos requeridos presentes")
        return True
    
    except Exception as e:
        print_error(f"  Error: {e}")
        return False


# ============================================
# REPORTE FINAL
# ============================================

def print_report(results: Dict[str, bool], duration: float) -> None:
    """Imprime reporte final de verificación."""
    print_header("REPORTE DE VERIFICACIÓN")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\n  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duración: {duration:.2f}s")
    print()
    
    print(f"  RESULTADOS:")
    print(f"  {'='*50}")
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"  {status:<10} {test_name}")
    
    print(f"  {'='*50}")
    print()
    print(f"  Total:      {total}")
    print(f"  Pasados:    {passed} ✅")
    print(f"  Fallidos:   {failed} ❌")
    print(f"  Éxito:      {passed/total*100:.1f}%")
    print()
    
    if failed == 0:
        print_success("🎉 TODOS LOS TESTS PASARON")
    else:
        print_error(f"⚠️  {failed} TEST(S) FALLARON")
    
    print()


# ============================================
# MAIN
# ============================================

async def main() -> int:
    """Función principal."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🔍 VERIFICACIÓN DE INTEGRACIÓN DEXSCREENER".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("║" + "  Compatible con ARM64 / Termux / Python 3.13".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    
    print_info("Iniciando verificación de API DexScreener...")
    print_info("Los tests hacen llamadas reales a internet")
    
    import time
    start_time = time.time()
    
    results = {}
    
    async with DexScreenerClient(timeout=15.0, max_retries=3) as client:
        # Test 1: get_token_info
        results["get_token_info"] = await test_get_token_info(client)
        
        # Test 2: search_tokens
        results["search_tokens"] = await test_search_tokens(client)
        
        # Test 3: trending
        results["get_solana_trending"] = await test_trending(client)
        
        # Test 4: conversión TokenData
        results["token_data_conversion"] = await test_token_data_conversion(client)
    
    duration = time.time() - start_time
    
    # Reporte final
    print_report(results, duration)
    
    # Exit code basado en resultados
    failed = sum(1 for v in results.values() if not v)
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verificación cancelada por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
