#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║                    MENÚ INTERACTIVO                                     ║
║          Menú de configuración para Solana Memecoin Bot                 ║
║          Compatible con ARM64 / Termux / Python 3.13                   ║
╚══════════════════════════════════════════════════════════════════════════╝

Uso:
    python -m solana_bot.menu.interactive
    python solana_bot/menu/interactive.py

Este módulo proporciona un menú interactivo en terminal para:
1. Gestionar watchlist de tokens
2. Importar tokens desde DexScreener
3. Configurar filtros cuantitativos
4. Priorizar fuente de datos
5. Ver estado de configuración
6. Guardar y salir

No requiere dependencias externas (solo stdlib).
"""

import logging
import sys
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from solana_bot.menu.handlers import (
    handle_filters,
    handle_import_dexscreener,
    handle_priority,
    handle_save_exit,
    handle_view_config,
    handle_watchlist,
)
from solana_bot.menu.widgets import (
    clear_screen,
    input_menu,
    print_banner,
    print_error,
    print_footer,
    print_header,
    print_info,
    print_success,
)

# ============================================
# CONFIGURACIÓN DE LOGGING
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


# ============================================
# CONSTANTES DEL MENÚ
# ============================================

MENU_TITLE = "🤖 SOLANA MEMEBOT — MENÚ DE CONFIGURACIÓN"

MENU_OPTIONS = [
    "Gestionar Watchlist (añadir/eliminar tokens)",
    "Importar tokens desde DexScreener",
    "Configurar filtros cuantitativos",
    "Priorizar fuente de datos",
    "Ver estado actual de configuración",
    "Guardar y salir",
    "Salir sin guardar",
]

MENU_WIDTH = 65


# ============================================
# FUNCIONES PRINCIPALES
# ============================================

def print_menu() -> None:
    """Imprime el menú principal con formato."""
    clear_screen()
    
    print()
    print("╔" + "═" * (MENU_WIDTH - 2) + "╗")
    print("║" + " " * (MENU_WIDTH - 2) + "║")
    
    # Título centrado
    title = "  " + MENU_TITLE
    padding = (MENU_WIDTH - 2 - len(title)) // 2
    print("║" + " " * padding + title + " " * (MENU_WIDTH - 2 - padding - len(title)) + "║")
    
    print("║" + " " * (MENU_WIDTH - 2) + "║")
    print("╚" + "═" * (MENU_WIDTH - 2) + "╝")
    print()
    
    # Opciones
    print("  ┌" + "─" * (MENU_WIDTH - 4) + "┐")
    print("  │" + " " * (MENU_WIDTH - 4) + "│")
    
    for i, option in enumerate(MENU_OPTIONS, 1):
        # Ajustar para que quepa
        display = f"  {i}. {option}"
        if len(display) < MENU_WIDTH - 4:
            display = display + " " * (MENU_WIDTH - 4 - len(display))
        print(f"  │{display}│")
    
    print("  │" + " " * (MENU_WIDTH - 4) + "│")
    print("  └" + "─" * (MENU_WIDTH - 4) + "┘")
    print()


def run_menu() -> int:
    """
    Ejecuta el menú principal en bucle.
    
    Returns:
        Código de salida:
        0 = Guardó y salió
        1 = Salió sin guardar
        2 = Error
    """
    while True:
        try:
            print_menu()
            
            choice = input_menu(
                MENU_OPTIONS,
                prompt="Seleccione una opción",
                allow_cancel=False,
            )
            
            if choice is None:
                continue
            
            # Ejecutar handler correspondiente
            result = execute_option(choice)
            
            if result == "exit_save":
                print_success("¡Hasta luego!")
                return 0
            elif result == "exit_no_save":
                print_info("Cambios descartados")
                return 1
            
            # Continuar en el menú
            
        except KeyboardInterrupt:
            print("\n")
            print_info("Saliendo del menú...")
            return 1
        except Exception as e:
            print_error(f"Error inesperado: {e}")
            logger.exception("Error en el menú")
            input("\n  Presione ENTER para continuar...")


def execute_option(choice: int) -> str:
    """
    Ejecuta la opción seleccionada del menú.
    
    Args:
        choice: Índice de la opción (0-indexed)
        
    Returns:
        String indicando el resultado:
        - "continue": Continuar en el menú
        - "exit_save": Salir guardando
        - "exit_no_save": Salir sin guardar
    """
    from solana_bot.menu.widgets import pause
    
    if choice == 0:
        # Gestionar Watchlist
        print_info("Abriendo gestión de watchlist...")
        handle_watchlist()
        return "continue"
    
    elif choice == 1:
        # Importar desde DexScreener
        print_info("Abriendo importador de DexScreener...")
        try:
            handle_import_dexscreener()
        except Exception as e:
            print_error(f"Error conectando con DexScreener: {e}")
            logger.exception("Error en DexScreener")
        pause()
        return "continue"
    
    elif choice == 2:
        # Configurar filtros
        print_info("Abriendo configuración de filtros...")
        handle_filters()
        return "continue"
    
    elif choice == 3:
        # Prioridad de datos
        print_info("Abriendo configuración de prioridad...")
        handle_priority()
        return "continue"
    
    elif choice == 4:
        # Ver configuración
        print_info("Mostrando estado de configuración...")
        handle_view_config()
        return "continue"
    
    elif choice == 5:
        # Guardar y salir
        if handle_save_exit():
            return "exit_save"
        return "continue"
    
    elif choice == 6:
        # Salir sin guardar
        print_info("Saliendo sin guardar cambios...")
        return "exit_no_save"
    
    return "continue"


# ============================================
# PUNTO DE ENTRADA
# ============================================

def main() -> int:
    """
    Punto de entrada principal del menú interactivo.
    
    Returns:
        Código de salida del programa
    """
    print_info("Iniciando menú de configuración...")
    print_info("Archivos de config en: ~/.solana_memebot/")
    print()
    
    try:
        exit_code = run_menu()
        return exit_code
    except Exception as e:
        print_error(f"Error fatal: {e}")
        logger.exception("Error fatal en main")
        return 2


if __name__ == "__main__":
    # Detectar si se ejecuta como módulo o script directo
    if __package__ is None or __package__ == "":
        # Ejecutado directamente: python interactive.py
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        # Importar de nuevo con el path correcto
        from menu.handlers import (
            handle_filters,
            handle_import_dexscreener,
            handle_priority,
            handle_save_exit,
            handle_view_config,
            handle_watchlist,
        )
        from menu.widgets import (
            clear_screen,
            input_menu,
            print_banner,
            print_error,
            print_header,
            print_info,
            print_success,
        )
    
    exit_code = main()
    sys.exit(exit_code)
