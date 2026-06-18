#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  SOLANA MEMEBOT - EJECUTOR PARA TERMUX
# ═══════════════════════════════════════════════════════════════════════════════
#  Este script ejecuta el bot con diferentes modos:
#    - Menú interactivo
#    - Loop continuo (escaneo perpetuo)
#    - Modo monitor (ver estado)
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuración
REPO_DIR="$HOME/Seed"
BOT_DIR="$HOME/.solana_memebot"

# Banner
show_banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                       ║"
    echo -e "║  ${BOLD}🤖 SOLANA MEMEBOT - EJECUTOR${NC}${CYAN}                               ║"
    echo -e "║     ${BOLD}Versión 1.1.0 - Rama Risk${NC}${CYAN}                                  ║"
    echo "║                                                                       ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Verificar instalación
check_install() {
    if [ ! -d "$REPO_DIR" ]; then
        echo -e "${RED}❌ Error: Bot no instalado${NC}"
        echo "   Ejecuta primero: bash $HOME/Seed/install_termux.sh"
        exit 1
    fi
    
    if [ ! -f "$REPO_DIR/solana_bot/menu/interactive.py" ]; then
        echo -e "${RED}❌ Error: Estructura del bot corrupta${NC}"
        exit 1
    fi
}

# Modo: Menú interactivo
mode_menu() {
    echo -e "${GREEN}[*]${NC} Ejecutando menú de configuración..."
    cd "$REPO_DIR"
    python solana_bot/menu/interactive.py
}

# Modo: Loop continuo
mode_loop() {
    echo -e "${GREEN}[*]${NC} Iniciando modo LOOP CONTINUO..."
    echo -e "${YELLOW}   Presiona Ctrl+C para detener${NC}"
    echo ""
    
    cd "$REPO_DIR"
    
    while true; do
        echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} Ejecutando ciclo de escaneo..."
        
        # Aquí se ejecutaría el loop principal del bot
        # Por ahora ejecutamos el menú en modo batch
        python solana_bot/menu/interactive.py --loop 2>/dev/null || {
            echo -e "${YELLOW}[!]${NC} Esperando 60 segundos antes del próximo ciclo..."
            sleep 60
        }
        
        sleep 5
    done
}

# Modo: Monitor (ver estado)
mode_monitor() {
    echo -e "${GREEN}[*]${NC} Monitor de estado"
    echo ""
    
    echo "═══════════════════════════════════════════════════════════════════════"
    echo "  ESTADO DEL SISTEMA"
    echo "═══════════════════════════════════════════════════════════════════════"
    echo ""
    
    echo -e "${BOLD}📁 Repositorio:${NC}"
    echo "   $REPO_DIR"
    if [ -d "$REPO_DIR/.git" ]; then
        cd "$REPO_DIR" && git log --oneline -1
    fi
    echo ""
    
    echo -e "${BOLD}📋 Configuración:${NC}"
    if [ -f "$BOT_DIR/dex_config.json" ]; then
        cat "$BOT_DIR/dex_config.json"
    else
        echo -e "${YELLOW}   No existe configuración${NC}"
    fi
    echo ""
    
    echo -e "${BOLD}📋 Watchlist:${NC}"
    if [ -f "$BOT_DIR/watchlist.json" ]; then
        python3 -c "
import json
with open('$BOT_DIR/watchlist.json') as f:
    data = json.load(f)
tokens = data.get('tokens', [])
print(f'   Tokens en watchlist: {len(tokens)}')
for i, t in enumerate(tokens[:5], 1):
    print(f'   {i}. {t[:20]}...')
if len(tokens) > 5:
    print(f'   ... y {len(tokens)-5} más')
"
    else
        echo -e "${YELLOW}   No existe watchlist${NC}"
    fi
    echo ""
    
    echo -e "${BOLD}🔗 Conexión DexScreener:${NC}"
    cd "$REPO_DIR" && timeout 10 python check_dexscreener.py 2>/dev/null || echo -e "${YELLOW}   No se pudo verificar${NC}"
}

# Modo: Quick scan (escaneo rápido)
mode_scan() {
    echo -e "${GREEN}[*]${NC} Ejecutando escaneo rápido..."
    cd "$REPO_DIR"
    python check_dexscreener.py
}

# Modo: Config (editar config)
mode_config() {
    echo -e "${GREEN}[*]${NC} Abriendo editor de configuración..."
    cd "$REPO_DIR"
    python solana_bot/menu/interactive.py
}

# Mostrar ayuda
show_help() {
    show_banner
    echo ""
    echo -e "${BOLD}USO:${NC}"
    echo "    bash run_termux.sh [OPCION]"
    echo ""
    echo -e "${BOLD}OPCIONES:${NC}"
    echo "    menu      - Menú de configuración interactivo"
    echo "    loop      - Ejecución continua (escaneo perpetuo)"
    echo "    monitor   - Ver estado del sistema"
    echo "    scan      - Escaneo rápido de DexScreener"
    echo "    config    - Abrir configuración"
    echo "    help      - Mostrar esta ayuda"
    echo ""
    echo -e "${BOLD}EJEMPLOS:${NC}"
    echo "    bash run_termux.sh menu"
    echo "    bash run_termux.sh loop"
    echo "    bash run_termux.sh monitor"
    echo ""
}

# MAIN
main() {
    check_install
    
    case "${1:-menu}" in
        menu)
            show_banner
            mode_menu
            ;;
        loop)
            show_banner
            mode_loop
            ;;
        monitor)
            show_banner
            mode_monitor
            ;;
        scan)
            show_banner
            mode_scan
            ;;
        config)
            show_banner
            mode_config
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ Opción desconocida: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
