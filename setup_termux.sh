#!/bin/bash
# ============================================
# Solana Memecoin Trading Bot
# Quick Setup for Termux (Android)
# One-command installation - Robusto
# ============================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║   ${BOLD}🪄 Solana Memecoin Trading Bot${NC}${CYAN}                        ║"
echo "║   ${BOLD}Quick Setup for Termux${NC}${CYAN}                              ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar si estamos en Termux
if [ -f "/data/data/com.termux/files/usr/bin/bash" ] || [ -d "/data/data/com.termux/files/usr" ]; then
    IS_TERMUX=true
else
    IS_TERMUX=false
fi

# Step 1: Install system packages
echo -e "${YELLOW}📦 [1/4] Instalando dependencias del sistema...${NC}"

# Detectar gestor de paquetes
if command -v pkg &> /dev/null; then
    PKG="pkg"
elif command -v apt &> /dev/null; then
    PKG="apt"
elif command -v apk &> /dev/null; then
    PKG="apk"
else
    echo -e "${RED}❌ No se detectó gestor de paquetes${NC}"
    exit 1
fi

echo -e "  Usando: $PKG"

# Instalar según el sistema
if [ "$IS_TERMUX" = true ]; then
    $PKG update -y 2>/dev/null || true
    $PKG upgrade -y 2>/dev/null || true
    $PKG install -y python git curl wget 2>/dev/null || true
elif [ "$PKG" = "apk" ]; then
    $PKG add --no-cache python3 py3-pip git curl wget
else
    sudo $PKG update -y 2>/dev/null || true
    sudo $PKG install -y python3 python3-pip git curl wget 2>/dev/null || true
fi

echo -e "${GREEN}✓${NC} Dependencias del sistema instaladas"

# Step 2: Create venv
echo -e "${YELLOW}🗄️  [2/4] Creando/verificando entorno virtual...${NC}"

# Eliminar venv existente si está corrupto
if [ -d "venv" ]; then
    if [ ! -f "venv/bin/activate" ]; then
        echo -e "  ${YELLOW}Limpiando venv corrupto...${NC}"
        rm -rf venv
    else
        echo -e "${GREEN}✓${NC} Entorno virtual ya existe"
    fi
fi

if [ ! -d "venv" ]; then
    python -m venv venv
    echo -e "${GREEN}✓${NC} Entorno virtual creado"
fi

# Step 3: Install Python packages
echo -e "${YELLOW}📥 [3/4] Instalando paquetes de Python...${NC}"
source venv/bin/activate

# Actualizar pip primero
pip install --upgrade pip setuptools wheel -q 2>/dev/null || true

# Instalar paquetes - solo los necesarios (sin pydantic que requiere compilación)
echo -e "  Instalando dependencias principales..."

if pip install python-dotenv colorlog aiohttp aiohttp-socks 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Paquetes instalados"
else
    # Fallback sin output silencioso
    echo -e "  Reintentando..."
    pip install python-dotenv colorlog aiohttp aiohttp-socks || {
        echo -e "${RED}❌ Error instalando paquetes${NC}"
        echo -e "${YELLOW}  Intenta manualmente:${NC}"
        echo -e "  pkg install rust clang make"
        echo -e "  source venv/bin/activate"
        echo -e "  pip install python-dotenv colorlog aiohttp aiohttp-socks"
        exit 1
    }
fi

# Step 4: Setup config
echo -e "${YELLOW}📝 [4/4] Configurando...${NC}"
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Solana Memecoin Trading Bot - Configuration
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
BIRDEYE_API_KEY=your_birdeye_api_key_here
WALLET_PRIVATE_KEY=your_private_key_base58_here
DRY_RUN=true
EOF
    echo -e "${GREEN}✓${NC} Archivo .env creado"
else
    echo -e "${GREEN}✓${NC} Archivo .env ya existe"
fi

# Make scripts executable
chmod +x install_termux.sh run.sh setup_termux.sh solana_bot_complete.py 2>/dev/null || true

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}${BOLD}                  ✅ CONFIGURACIÓN COMPLETADA                    ${NC}${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}Cómo usar:${NC}"
echo ""
echo -e "  1. Activa el entorno virtual:"
echo -e "     ${CYAN}source venv/bin/activate${NC}"
echo ""
echo -e "  2. Ejecuta backtesting (no necesita credenciales):"
echo -e "     ${CYAN}python solana_bot_complete.py backtest --sesiones 1000${NC}"
echo ""
echo -e "  3. O usa el script rápido:"
echo -e "     ${CYAN}./run.sh backtest --sesiones 1000${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "  - Edita .env antes de usar con dinero real"
echo "  - Empieza siempre en modo dry-run"
echo "  - Nunca compartas tu clave privada"
echo ""