#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  SOLANA MEMEBOT - INSTALADOR PARA TERMUX (Android)
# ═══════════════════════════════════════════════════════════════════════════════
#  Compatible con: Termux (Android 7+), Python 3.10+
#  Versión: 1.1.0
# ═══════════════════════════════════════════════════════════════════════════════
#  Uso:
#    bash <(curl -sL https://git.io/seed-termux)
#    O guarda este archivo y ejecuta: bash install_termux.sh
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
REPO_URL="https://github.com/Oppenheimmer-droid/Seed"
REPO_DIR="$HOME/Seed"
BOT_DIR="$HOME/.solana_memebot"
PYTHON_MIN="3.10"

# Banner
show_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                       ║"
    echo -e "║  ${BOLD}🤖 SOLANA MEMEBOT${NC}${CYAN}                                            ║"
    echo -e "║     ${BOLD}Instalador para Termux (Android)${NC}${CYAN}                            ║"
    echo -e "║     ${BOLD}Versión 1.1.0${NC}${CYAN}                                               ║"
    echo "║                                                                       ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Verificar Termux
check_termux() {
    if [ ! -d "/data/data/com.termux/files/home" ]; then
        echo -e "${YELLOW}⚠️  ADVERTENCIA:${NC} Este script está diseñado para Termux."
        echo "    Se detectó un sistema diferente. Continuando de todos modos..."
        echo ""
        read -p "¿Continuar? (s/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            exit 0
        fi
    fi
}

# Verificar Python
check_python() {
    echo -e "${BLUE}[1/6]${NC} Verificando Python..."
    
    if ! command -v python &> /dev/null; then
        echo -e "${YELLOW}  Python no encontrado. Instalando...${NC}"
        pkg update -y && pkg install -y python
    fi
    
    PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "  Python version: ${GREEN}$PYTHON_VERSION${NC}"
    
    # Verificar versión mínima
    PYTHON_MAJOR=$(python -c 'import sys; print(sys.version_info[0])')
    PYTHON_MINOR=$(python -c 'import sys; print(sys.version_info[1])')
    REQUIRED_MAJOR=3
    REQUIRED_MINOR=10
    
    if [ "$PYTHON_MAJOR" -lt "$REQUIRED_MAJOR" ] || \
       ([ "$PYTHON_MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$REQUIRED_MINOR" ]); then
        echo -e "${RED}❌ Error: Se requiere Python 3.10 o superior${NC}"
        echo "    Versión actual: $PYTHON_VERSION"
        exit 1
    fi
}

# Instalar dependencias
install_deps() {
    echo ""
    echo -e "${BLUE}[2/6]${NC} Instalando dependencias del sistema..."
    
    # Actualizar pkg (sin --upgrade pip)
    pkg update -y
    pkg install -y git curl
    
    echo ""
    echo -e "${BLUE}[3/6]${NC} Instalando dependencias de Python..."
    
    # NO usar pip install --upgrade pip (rompe Termux)
    pip install httpx aiohttp beautifulsoup4 python-dotenv
    
    echo -e "  ${GREEN}✓${NC} Dependencias instaladas"
}

# Clonar o actualizar repositorio
setup_repo() {
    echo ""
    echo -e "${BLUE}[4/6]${NC} Configurando repositorio..."
    
    if [ -d "$REPO_DIR/.git" ]; then
        echo "  Repositorio encontrado. Actualizando..."
        cd "$REPO_DIR"
        git pull origin release/termux-v1.1.0 || git pull origin main
        echo -e "  ${GREEN}✓${NC} Repositorio actualizado"
    else
        echo "  Clonando repositorio..."
        git clone -b release/termux-v1.1.0 "$REPO_URL" "$REPO_DIR"
        echo -e "  ${GREEN}✓${NC} Repositorio clonado"
    fi
}

# Crear directorio de datos
setup_data_dir() {
    echo ""
    echo -e "${BLUE}[5/6]${NC} Creando directorio de datos..."
    
    mkdir -p "$BOT_DIR"
    
    # Crear archivo de configuración por defecto si no existe
    if [ ! -f "$BOT_DIR/dex_config.json" ]; then
        cat > "$BOT_DIR/dex_config.json" << 'EOF'
{
  "dex_screener": {
    "enabled": true,
    "priority": "birdeye",
    "min_liquidity_usd": 50000,
    "min_volume_5m_usd": 10000,
    "max_age_minutes": 60,
    "min_holders": 100,
    "max_top_holder_pct": 0.20,
    "dex_whitelist": ["raydium", "meteora", "pump.fun"],
    "watchlist": []
  },
  "loop": {
    "capital_operativo_base": 100.0,
    "extraccion_por_ciclo": 15.0,
    "stop_ciclo": -50.0
  }
}
EOF
        echo -e "  ${GREEN}✓${NC} Configuración por defecto creada"
    else
        echo -e "  ${YELLOW}ℹ${NC} Configuración existente preservada"
    fi
    
    # Crear watchlist vacía si no existe
    if [ ! -f "$BOT_DIR/watchlist.json" ]; then
        echo '{"version": "1.0", "updated_at": "", "tokens": []}' > "$BOT_DIR/watchlist.json"
    fi
    
    echo "  Directorio: $BOT_DIR"
}

# Verificar instalación
verify_install() {
    echo ""
    echo -e "${BLUE}[6/6]${NC} Verificando instalación..."
    
    cd "$REPO_DIR"
    
    # Verificar estructura
    if [ -f "solana_bot/menu/interactive.py" ]; then
        echo -e "  ${GREEN}✓${NC} Estructura del bot correcta"
    else
        echo -e "  ${RED}✗${NC} Error: Estructura del bot no encontrada"
        exit 1
    fi
    
    # Verificar dependencias de Python
    python -c "import httpx; import aiohttp; import bs4; print('  ✓ Dependencias OK')" 2>/dev/null || {
        echo -e "  ${RED}✗${NC} Error: Faltan dependencias de Python"
        exit 1
    }
    
    echo -e "  ${GREEN}✓${NC} Instalación verificada"
}

# Mostrar instrucciones finales
show_instructions() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  ✅ INSTALACIÓN COMPLETADA${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BOLD}📱 EJECUTAR EL BOT:${NC}"
    echo ""
    echo -e "  1. Ir al directorio:"
    echo -e "     ${GREEN}cd $REPO_DIR${NC}"
    echo ""
    echo -e "  2. Ejecutar el menú interactivo:"
    echo -e "     ${GREEN}python solana_bot/menu/interactive.py${NC}"
    echo ""
    echo -e "  3. Para ejecución continua (loop):"
    echo -e "     ${GREEN}python solana_bot/menu/interactive.py --loop${NC}"
    echo ""
    echo -e "${BOLD}📁 ARCHIVOS:${NC}"
    echo "     Datos: $BOT_DIR"
    echo "     Repo:  $REPO_DIR"
    echo ""
    echo -e "${BOLD}🔄 ACTUALIZAR:${NC}"
    echo "     cd $REPO_DIR && git pull"
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
}

# Menú interactivo post-instalación
show_menu() {
    while true; do
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${BOLD}  MENÚ PRINCIPAL${NC}"
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "  1. Ejecutar menú de configuración"
        echo "  2. Ver estado de configuración"
        echo "  3. Agregar token a watchlist"
        echo "  4. Probar conexión DexScreener"
        echo "  5. Actualizar bot"
        echo "  0. Salir"
        echo ""
        read -p "  Seleccione opción: " choice
        
        case $choice in
            1)
                cd "$REPO_DIR"
                python solana_bot/menu/interactive.py
                ;;
            2)
                cat "$BOT_DIR/dex_config.json" 2>/dev/null || echo "No hay configuración"
                ;;
            3)
                read -p "  Dirección del token: " token_addr
                if [ -n "$token_addr" ]; then
                    python -c "
import json
with open('$BOT_DIR/watchlist.json', 'r') as f:
    data = json.load(f)
if '$token_addr' not in data['tokens']:
    data['tokens'].append('$token_addr')
    with open('$BOT_DIR/watchlist.json', 'w') as f:
        json.dump(data, f, indent=2)
    print('  ✓ Token agregado')
else:
    print('  ℹ Token ya existe')
"
                fi
                ;;
            4)
                echo "  Probando conexión..."
                cd "$REPO_DIR"
                python check_dexscreener.py
                ;;
            5)
                cd "$REPO_DIR"
                git pull
                ;;
            0)
                echo "  ¡Hasta luego!"
                exit 0
                ;;
            *)
                echo "  Opción inválida"
                ;;
        esac
    done
}

# MAIN
main() {
    show_banner
    check_termux
    check_python
    install_deps
    setup_repo
    setup_data_dir
    verify_install
    
    echo ""
    read -p "¿Ejecutar menú de configuración ahora? (s/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        show_menu
    else
        show_instructions
    fi
}

main "$@"
