#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  INSTALACIÓN RÁPIDA - SOLANA MEMEBOT PARA TERMUX
# ═══════════════════════════════════════════════════════════════════════════════
#  Este script instala el bot como paquete pip para ejecutarlo desde
#  cualquier lugar con un solo comando: `memenot`
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════"
echo "  🔧 INSTALANDO SOLANA MEMEBOT"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detectar si es Termux
if [ -d "/data/data/com.termux/files/home" ]; then
    echo -e "${GREEN}[+]${NC} Detectado: Termux (Android)"
    TERMUX=true
else
    echo -e "${YELLOW}[!]${NC} Detectado: Sistema no-Termux"
    TERMUX=false
fi

# Paso 1: Actualizar paquetes
echo ""
echo -e "${GREEN}[1/4]${NC} Actualizando paquetes..."
if [ "$TERMUX" = true ]; then
    pkg update -y && pkg upgrade -y
    pkg install -y python python-pip git
else
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt upgrade -y
    elif command -v pacman &> /dev/null; then
        sudo pacman -Syu --noconfirm
    fi
fi

# Paso 2: Instalar dependencias
echo ""
echo -e "${GREEN}[2/4]${NC} Instalando dependencias de Python..."
pip install httpx aiohttp beautifulsoup4 python-dotenv

# Paso 3: Instalar el paquete
echo ""
echo -e "${GREEN}[3/4]${NC} Instalando solana-memebot..."

# Ir al directorio del script o /tmp
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    # Instalar desde el directorio local
    echo -e "${YELLOW}[i]${NC} Instalando desde directorio local..."
    cd "$SCRIPT_DIR"
    pip install -e . 2>/dev/null || pip install .
else
    # Instalar desde GitHub directamente
    echo -e "${YELLOW}[i]${NC} Instalando desde GitHub..."
    pip install git+https://github.com/Oppenheimmer-droid/Seed.git
fi

# Paso 4: Verificar
echo ""
echo -e "${GREEN}[4/4]${NC} Verificando instalación..."
if command -v solenot &> /dev/null; then
    echo -e "${GREEN}[✓]${NC} Comando 'solenot' instalado"
elif command -v solenot &> /dev/null; then
    echo -e "${GREEN}[✓]${NC} Comando 'solenot' instalado"  
elif pip show solana-memebot &> /dev/null; then
    echo -e "${GREEN}[✓]${NC} Paquete 'solana-memebot' instalado"
else
    echo -e "${RED}[✗]${NC} Error en la instalación"
fi

# Resumen
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ INSTALACIÓN COMPLETADA"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Para ejecutar el menú interactivo:"
echo ""
echo -e "    ${GREEN}memenot${NC}"
echo ""
echo "  O directamente con Python:"
echo ""
echo -e "    python -m solana_bot.menu.interactive"
echo ""
echo "  Archivos de configuración en:"
echo -e "    ${YELLOW}~/.solana_memebot/${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════"
