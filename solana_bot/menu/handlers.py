"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    HANDLERS DEL MENÚ                                     ║
║          Manejadores de opciones del menú interactivo                   ║
║          Puro Python 3.13 - Sin dependencias externas                   ║
╚══════════════════════════════════════════════════════════════════════════╝

Handlers disponibles:
- handle_watchlist(): Gestionar lista de tokens a seguir
- handle_import_dexscreener(): Importar desde DexScreener
- handle_filters(): Configurar filtros cuantitativos
- handle_priority(): Priorizar fuente de datos
- handle_view_config(): Ver estado actual de configuración
- handle_save_exit(): Guardar y salir
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from solana_bot.clients.dexscreener import DexScreenerClient
from solana_bot.storage import (
    agregar_a_watchlist,
    cargar_config_dex,
    cargar_watchlist,
    eliminar_de_watchlist,
    guardar_config_dex,
    guardar_watchlist,
    get_default_dex_config,
)
from solana_bot.menu.widgets import (
    input_address,
    input_float_range,
    input_list,
    input_menu,
    input_number,
    input_string,
    input_yes_no,
    pause,
    print_divider,
    print_error,
    print_footer,
    print_header,
    print_info,
    print_success,
    print_table,
    print_warning,
)

if TYPE_CHECKING:
    from solana_bot.config.bot_config import DexScreenerConfig

logger = logging.getLogger(__name__)

# ============================================
# HELPER: CARGAR/GUARDAR CONFIGURACIÓN
# ============================================

def _load_config() -> Dict:
    """Carga configuración actual."""
    config = cargar_config_dex()
    if "dex_screener" not in config:
        config["dex_screener"] = get_default_dex_config()["dex_screener"]
    if "loop" not in config:
        config["loop"] = get_default_dex_config()["loop"]
    return config


def _save_config(config: Dict) -> bool:
    """Guarda configuración."""
    return guardar_config_dex(config)


# ============================================
# HANDLER 1: GESTIONAR WATCHLIST
# ============================================

def handle_watchlist() -> bool:
    """
    Gestiona la lista de tokens a seguir.
    
    Permite:
    - Ver watchlist actual
    - Agregar tokens manualmente
    - Eliminar tokens
    - Limpiar toda la lista
    """
    config = _load_config()
    dex_config = config.get("dex_screener", {})
    watchlist = dex_config.get("watchlist", [])
    
    while True:
        print_header("GESTIONAR WATCHLIST")
        
        print(f"\n  Tokens en watchlist: {len(watchlist)}")
        print_divider()
        
        if watchlist:
            # Mostrar en tabla
            rows = []
            for i, addr in enumerate(watchlist[:15], 1):
                rows.append([str(i), addr[:12] + "...", addr])
            print_table(["#", "Dirección (corta)", "Dirección completa"], rows)
            
            if len(watchlist) > 15:
                print_warning(f"  ... y {len(watchlist) - 15} más")
        else:
            print_info("  La watchlist está vacía")
        
        print_divider()
        print("  1. Agregar token manualmente")
        print("  2. Eliminar token por número")
        print("  3. Limpiar toda la watchlist")
        print("  0. Volver al menú principal")
        print()
        
        choice = input_menu(
            ["Agregar token", "Eliminar token", "Limpiar watchlist"],
            allow_cancel=True
        )
        
        if choice is None:
            # Guardar y salir
            _save_config(config)
            return True
        
        if choice == 0:
            # Agregar token
            print_header("AGREGAR TOKEN")
            address = input_address("Dirección del token Solana")
            
            if address:
                if address in watchlist:
                    print_warning(f"El token {address[:12]}... ya está en la watchlist")
                else:
                    watchlist.append(address)
                    dex_config["watchlist"] = watchlist
                    config["dex_screener"] = dex_config
                    print_success(f"Token agregado: {address[:12]}...")
                    _save_config(config)
        
        elif choice == 1:
            # Eliminar token
            if not watchlist:
                print_warning("La watchlist está vacía")
                pause()
                continue
            
            try:
                num = input_number(
                    "Número del token a eliminar",
                    num_type=int,
                    min_val=1,
                    max_val=len(watchlist)
                )
                if num is not None:
                    removed = watchlist.pop(num - 1)
                    dex_config["watchlist"] = watchlist
                    config["dex_screener"] = dex_config
                    print_success(f"Token eliminado: {removed[:12]}...")
                    _save_config(config)
            except (ValueError, TypeError):
                print_error("Número inválido")
        
        elif choice == 2:
            # Limpiar
            print_header("LIMPIAR WATCHLIST")
            confirm = input_yes_no(
                f"¿Está seguro de eliminar los {len(watchlist)} tokens?",
                default=False
            )
            
            if confirm:
                watchlist = []
                dex_config["watchlist"] = []
                config["dex_screener"] = dex_config
                print_success("Watchlist limpiada")
                _save_config(config)
        
        pause()


# ============================================
# HANDLER 2: IMPORTAR DESDE DEXSCREENER
# ============================================

async def handle_import_dexscreener_async() -> bool:
    """
    Importa tokens desde DexScreener.
    
    Permite:
    - Buscar por query
    - Obtener trending
    - Seleccionar tokens para agregar a watchlist
    """
    config = _load_config()
    dex_config = config.get("dex_screener", {})
    current_watchlist = set(dex_config.get("watchlist", []))
    
    print_header("IMPORTAR DESDE DEXSCREENER")
    print_info("Conectando con DexScreener...")
    
    async with DexScreenerClient() as client:
        while True:
            print_header("IMPORTAR DESDE DEXSCREENER")
            print_divider()
            print("  1. Buscar por nombre/símbolo")
            print("  2. Ver tokens trending en Solana")
            print("  3. Obtener info de un token específico")
            print("  0. Volver al menú principal")
            print()
            
            choice = input_menu(
                ["Buscar por nombre", "Tokens trending", "Info de token"],
                allow_cancel=True
            )
            
            if choice is None:
                # Guardar cambios
                dex_config["watchlist"] = list(current_watchlist)
                config["dex_screener"] = dex_config
                _save_config(config)
                return True
            
            if choice == 0:
                # Buscar por query
                print_header("BUSCAR TOKENS")
                query = input_string("Término de búsqueda", required=True)
                
                if query:
                    print_info(f"Buscando '{query}'...")
                    pairs = await client.search_tokens(query, limit=20)
                    
                    if not pairs:
                        print_warning("No se encontraron tokens")
                        pause()
                        continue
                    
                    _show_and_select_pairs(pairs, current_watchlist)
            
            elif choice == 1:
                # Trending
                print_info("Obteniendo tokens trending...")
                pairs = await client.get_solana_trending(limit=20)
                
                if not pairs:
                    print_warning("No se pudieron obtener trending")
                    pause()
                    continue
                
                _show_and_select_pairs(pairs, current_watchlist)
            
            elif choice == 2:
                # Info de token
                print_header("INFO DE TOKEN")
                address = input_address("Dirección del token")
                
                if address:
                    print_info("Consultando DexScreener...")
                    pair = await client.get_token_info(address)
                    
                    if pair:
                        _show_pair_detail(pair)
                        
                        # Preguntar si agregar a watchlist
                        if address not in current_watchlist:
                            add = input_yes_no("¿Agregar a watchlist?", default=False)
                            if add:
                                current_watchlist.add(address)
                                print_success(f"Agregado a watchlist: {address[:12]}...")
                        else:
                            print_info("Ya está en watchlist")
                    else:
                        print_error("Token no encontrado")
                
                pause()
    
    return True


def handle_import_dexscreener() -> bool:
    """Wrapper sincrónico para handle_import_dexscreener_async."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si ya hay un loop corriendo, crear nueva tarea
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    handle_import_dexscreener_async()
                )
                return future.result()
        else:
            return loop.run_until_complete(handle_import_dexscreener_async())
    except RuntimeError:
        return asyncio.run(handle_import_dexscreener_async())


def _show_and_select_pairs(pairs: List, current_watchlist: set) -> None:
    """Muestra pares y permite seleccionar."""
    print_header(f"RESULTADOS ({len(pairs)} tokens)")
    
    rows = []
    for i, pair in enumerate(pairs[:15], 1):
        in_watch = "✓" if pair.base_token_address in current_watchlist else " "
        symbol = pair.base_token_symbol or "?"
        price = f"${pair.price_usd:.8f}" if pair.price_usd > 0 else "N/A"
        liq = f"${pair.liquidity_usd:,.0f}" if pair.liquidity_usd > 0 else "N/A"
        rows.append([str(i), in_watch, symbol, price, liq, pair.dex_id])
    
    print_table(["#", "W", "Símbolo", "Precio", "Liquidez", "DEX"], rows)
    
    if len(pairs) > 15:
        print_warning(f"  ... y {len(pairs) - 15} más")
    
    print()
    print_info("Seleccione números separados por coma para agregar a watchlist")
    print_info("Ejemplo: 1,3,5")
    
    selected = input_string("Tokens a agregar (ENTER para skip)", default="")
    
    if selected:
        try:
            indices = [int(x.strip()) for x in selected.split(",")]
            added = 0
            for idx in indices:
                if 1 <= idx <= len(pairs):
                    addr = pairs[idx - 1].base_token_address
                    if addr not in current_watchlist:
                        current_watchlist.add(addr)
                        added += 1
            print_success(f"Agregados {added} tokens a watchlist")
        except ValueError:
            print_error("Formato inválido")


def _show_pair_detail(pair) -> None:
    """Muestra detalle de un par."""
    print()
    print_divider()
    print(f"  {pair.base_token_symbol or 'Unknown'}")
    print(f"  Dirección: {pair.base_token_address}")
    print_divider()
    print(f"  DEX:        {pair.dex_id}")
    print(f"  Precio USD: ${pair.price_usd:.10f}")
    print(f"  Liquidez:   ${pair.liquidity_usd:,.2f}")
    print(f"  Volumen 24h: ${pair.volume_h24:,.2f}")
    print(f"  Volumen 5m:  ${pair.volume_m5:,.2f}")
    print(f"  Age:         {pair.age_minutes} min")
    print(f"  Change 5m:   {pair.price_change_m5:+.2f}%")
    print(f"  Change 1h:   {pair.price_change_h1:+.2f}%")
    print(f"  Change 24h:  {pair.price_change_h24:+.2f}%")
    print_divider()


# ============================================
# HANDLER 3: CONFIGURAR FILTROS
# ============================================

def handle_filters() -> bool:
    """
    Configura los filtros cuantitativos.
    
    Filtros disponibles:
    - Liquidez mínima (USD)
    - Volumen mínimo 5m (USD)
    - Edad máxima del token (minutos)
    - Mínimo de holders
    - Máximo % top holder
    - Lista de DEXs permitidos
    """
    config = _load_config()
    dex_config = config.get("dex_screener", {})
    
    # Mapeo de opciones de menú a campos
    filter_options = [
        ("min_liquidity_usd", "Liquidez mínima (USD)", 1000, 10000000, 50000),
        ("min_volume_5m_usd", "Volumen mínimo 5m (USD)", 100, 1000000, 10000),
        ("max_age_minutes", "Edad máxima del token (min)", 1, 10080, 60),  # 1 semana máx
        ("min_holders", "Mínimo de holders", 10, 100000, 100),
        ("max_top_holder_pct", "Máximo % top holder (%)", 0.01, 0.99, 0.20),
    ]
    
    while True:
        print_header("CONFIGURAR FILTROS")
        
        # Mostrar filtros actuales
        print("\n  FILTROS ACTUALES:")
        print_divider()
        
        rows = []
        for field, label, min_v, max_v, default in filter_options:
            value = dex_config.get(field, default)
            if field == "max_top_holder_pct":
                display = f"{value * 100:.1f}%"
            elif field == "min_liquidity_usd" or field == "min_volume_5m_usd":
                display = f"${value:,.0f}"
            else:
                display = str(value)
            rows.append([label, display])
        
        # DEX whitelist
        dex_list = dex_config.get("dex_whitelist", ["raydium"])
        rows.append(["DEXs permitidos", ", ".join(dex_list[:3]) + ("..." if len(dex_list) > 3 else "")])
        
        print_table(["Filtro", "Valor actual"], rows)
        
        print_divider()
        print("  Seleccione filtro a modificar:")
        print()
        
        menu_options = [label for _, label, _, _, _ in filter_options]
        menu_options.append("Editar lista de DEXs")
        menu_options.append("Restaurar valores por defecto")
        menu_options.append("Volver al menú principal")
        
        choice = input_menu(menu_options, allow_cancel=True)
        
        if choice is None:
            _save_config(config)
            return True
        
        if choice < len(filter_options):
            field, label, min_v, max_v, default = filter_options[choice]
            
            print_header(f"MODIFICAR: {label}")
            
            current = dex_config.get(field, default)
            
            if field == "max_top_holder_pct":
                # Es porcentaje
                value = input_float_range(
                    f"Nuevo valor ({min_v*100:.0f}% - {max_v*100:.0f}%)",
                    default=current * 100,
                    min_val=min_v * 100,
                    max_val=max_v * 100,
                )
                if value is not None:
                    dex_config[field] = value / 100
            else:
                value = input_number(
                    f"Nuevo valor ({min_v:,.0f} - {max_v:,.0f})",
                    default=current,
                    num_type=float,
                    min_val=min_v,
                    max_val=max_v,
                )
                if value is not None:
                    dex_config[field] = value
            
            config["dex_screener"] = dex_config
            print_success(f"Filtro actualizado: {label}")
        
        elif choice == len(filter_options):
            # Editar DEX whitelist
            handle_dex_whitelist(dex_config)
        
        elif choice == len(filter_options) + 1:
            # Restaurar defaults
            confirm = input_yes_no("¿Restaurar filtros por defecto?", default=False)
            if confirm:
                defaults = get_default_dex_config()["dex_screener"]
                for key in ["min_liquidity_usd", "min_volume_5m_usd", "max_age_minutes",
                            "min_holders", "max_top_holder_pct", "dex_whitelist"]:
                    if key in defaults:
                        dex_config[key] = defaults[key]
                config["dex_screener"] = dex_config
                print_success("Filtros restaurados a valores por defecto")
        
        _save_config(config)
        pause()


def handle_dex_whitelist(dex_config: Dict) -> None:
    """Edita la lista de DEXs permitidos."""
    print_header("EDITAR DEX WHITELIST")
    
    dex_list = list(dex_config.get("dex_whitelist", []))
    common_dexes = [
        "raydium", "meteora", "pump.fun", "orca", "fluxbeam",
        "crema", "cykura", "lifinity", "goosefx", "serum"
    ]
    
    print_info("DEXs comúnmente usados:")
    for i, dex in enumerate(common_dexes, 1):
        marker = "✓" if dex in dex_list else " "
        print(f"  [{marker}] {i}. {dex}")
    
    print()
    print_info("Ingrese números separados por coma para togglear")
    
    selected = input_string("Selección (ENTER para terminar)", default="")
    
    if selected:
        try:
            indices = [int(x.strip()) for x in selected.split(",")]
            for idx in indices:
                if 1 <= idx <= len(common_dexes):
                    dex = common_dexes[idx - 1]
                    if dex in dex_list:
                        dex_list.remove(dex)
                    else:
                        dex_list.append(dex)
            dex_config["dex_whitelist"] = dex_list
            print_success(f"DEXs actualizados: {', '.join(dex_list)}")
        except ValueError:
            print_error("Formato inválido")


# ============================================
# HANDLER 4: PRIORIZAR FUENTE DE DATOS
# ============================================

def handle_priority() -> bool:
    """
    Configura la prioridad de fuentes de datos.
    
    Opciones:
    - birdeye: Solo Birdeye
    - dexscreener: Solo DexScreener
    - hybrid: Ambos con enriquecimiento cruzado
    """
    config = _load_config()
    dex_config = config.get("dex_screener", {})
    
    priority_options = [
        ("birdeye", "Birdeye (API oficial con más datos)"),
        ("dexscreener", "DexScreener (más rápido, menos datos)"),
        ("hybrid", "Híbrido (Birdeye + DexScreener enriquecido)"),
    ]
    
    while True:
        print_header("PRIORIDAD DE FUENTE DE DATOS")
        
        current = dex_config.get("priority", "birdeye")
        print(f"\n  Prioridad actual: {current.upper()}")
        print()
        
        # Descripción de cada opción
        descriptions = {
            "birdeye": "   • Usa solo Birdeye API para datos de tokens\n"
                      "   • Más datos históricos y métricas\n"
                      "   • Puede ser más lento",
            "dexscreener": "   • Usa solo DexScreener API\n"
                          "   • Más rápido y actualizado\n"
                          "   • Menos métricas disponibles",
            "hybrid": "   • Combina ambas fuentes\n"
                      "   • Enriquece datos de Birdeye con DexScreener\n"
                      "   • Mejor precisión pero más lento",
        }
        
        print("  Opciones disponibles:")
        print_divider()
        
        for value, label in priority_options:
            marker = "→ " if current == value else "  "
            print(f"  {marker}{label}")
            print(descriptions.get(value, ""))
            print()
        
        print_divider()
        print()
        
        choice = input_menu(
            [label for _, label in priority_options],
            prompt="Seleccione prioridad"
        )
        
        if choice is not None:
            new_priority = priority_options[choice][0]
            dex_config["priority"] = new_priority
            config["dex_screener"] = dex_config
            _save_config(config)
            print_success(f"Prioridad cambiada a: {new_priority.upper()}")
        
        if input_yes_no("¿Volver al menú principal?", default=True):
            return True


# ============================================
# HANDLER 5: VER CONFIGURACIÓN
# ============================================

def handle_view_config() -> bool:
    """Muestra el estado actual de toda la configuración."""
    config = _load_config()
    dex_config = config.get("dex_screener", {})
    loop_config = config.get("loop", {})
    
    while True:
        print_header("ESTADO DE CONFIGURACIÓN")
        
        # Sección DexScreener
        print("\n  📊 DEXSCREENER:")
        print_divider()
        
        rows = [
            ["Habilitado", "Sí" if dex_config.get("enabled", True) else "No"],
            ["Prioridad", dex_config.get("priority", "birdeye").upper()],
            ["Min liquidez USD", f"${dex_config.get('min_liquidity_usd', 50000):,.0f}"],
            ["Min volumen 5m USD", f"${dex_config.get('min_volume_5m_usd', 10000):,.0f}"],
            ["Edad máxima", f"{dex_config.get('max_age_minutes', 60)} min"],
            ["Min holders", str(dex_config.get("min_holders", 100))],
            ["Max top holder %", f"{dex_config.get('max_top_holder_pct', 0.20) * 100:.1f}%"],
            ["Tokens en watchlist", str(len(dex_config.get("watchlist", [])))],
            ["DEXs activos", str(len(dex_config.get("dex_whitelist", [])))],
        ]
        print_table(["Parámetro", "Valor"], rows)
        
        # Sección Loop
        print("\n  🔄 LOOP DE TRADING:")
        print_divider()
        
        rows = [
            ["Capital operativo base", f"{loop_config.get('capital_operativo_base', 100.0):.1f} SOL"],
            ["Extracción por ciclo", f"{loop_config.get('extraccion_por_ciclo', 15.0):.1f} SOL"],
            ["Stop de ciclo", f"{loop_config.get('stop_ciclo', -50.0):.1f} SOL"],
        ]
        print_table(["Parámetro", "Valor"], rows)
        
        # Watchlist preview
        print("\n  📋 WATCHLIST (primeros 10):")
        print_divider()
        
        watchlist = dex_config.get("watchlist", [])
        if watchlist:
            rows = [[str(i+1), addr[:16] + "..."] for i, addr in enumerate(watchlist[:10])]
            print_table(["#", "Dirección"], rows)
            if len(watchlist) > 10:
                print_info(f"  ... y {len(watchlist) - 10} más")
        else:
            print_info("  Vacía")
        
        # DEXs whitelist
        print("\n  🏦 DEX WHITELIST:")
        print_divider()
        
        dex_list = dex_config.get("dex_whitelist", [])
        if dex_list:
            print(f"  {', '.join(dex_list)}")
        else:
            print_info("  Ninguno (todos permitidos)")
        
        print_footer()
        
        if input_yes_no("¿Volver al menú principal?", default=True):
            return True


# ============================================
# HANDLER 6: GUARDAR Y SALIR
# ============================================

def handle_save_exit() -> bool:
    """
    Guarda la configuración actual y sale.
    """
    config = _load_config()
    
    print_header("GUARDAR Y SALIR")
    
    # Mostrar resumen
    dex_config = config.get("dex_screener", {})
    
    print("\n  Resumen de cambios:")
    print_divider()
    print(f"  • Prioridad: {dex_config.get('priority', 'birdeye').upper()}")
    print(f"  • Tokens en watchlist: {len(dex_config.get('watchlist', []))}")
    print(f"  • Min liquidez: ${dex_config.get('min_liquidity_usd', 50000):,.0f}")
    print(f"  • Min volumen 5m: ${dex_config.get('min_volume_5m_usd', 10000):,.0f}")
    print_divider()
    
    if input_yes_no("¿Guardar cambios y salir?", default=True):
        _save_config(config)
        print_success("Configuración guardada correctamente")
        print_info(f"Archivos en: ~/.solana_memebot/")
        return True
    
    return False


# ============================================
# EJEMPLO DE USO
# ============================================

if __name__ == "__main__":
    # Test básico de handlers
    print_header("TEST HANDLERS")
    print_info("Ejecutando test...")
    
    # Test watchlist
    handle_view_config()
