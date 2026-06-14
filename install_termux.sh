#!/bin/bash
# ============================================
# Solana Memecoin Trading Bot
# Install Script for Termux (Android) / Linux
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
echo "║   ${BOLD}Install Script for Termux/Android${NC}${CYAN}                   ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Detectar Termux
if [ -f "/data/data/com.termux/files/usr/bin/bash" ] || [ -d "/data/data/com.termux/files/usr" ]; then
    IS_TERMUX=true
    PKG="pkg"
    echo -e "${CYAN}📱 Detectado: Termux (Android)${NC}"
elif [ -f "/etc/os-release" ] && grep -q "Alpine" /etc/os-release; then
    IS_TERMUX=false
    PKG="apk"
    echo -e "${CYAN}🐧 Detectado: Alpine Linux${NC}"
else
    IS_TERMUX=false
    PKG="apt-get"
    echo -e "${CYAN}🐧 Detectado: Debian/Ubuntu${NC}"
fi

echo -e "${YELLOW}📋 Verificando sistema...${NC}"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no encontrado${NC}"
    if [ "$IS_TERMUX" = true ]; then
        echo "   Ejecuta: pkg install python"
    else
        echo "   Ejecuta: sudo apt install python3 python3-pip python3-venv"
    fi
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  ${GREEN}✓${NC} Python $PYTHON_VERSION"

# Instalar dependencias del sistema
echo -e "${YELLOW}📦 Instalando dependencias del sistema...${NC}"

if [ "$IS_TERMUX" = true ]; then
    $PKG update -y 2>/dev/null || true
    $PKG upgrade -y 2>/dev/null || true
    $PKG install -y git wget curl openssl libffi 2>/dev/null || true
elif [ "$PKG" = "apk" ]; then
    $PKG add --no-cache python3 py3-pip python3-venv git wget curl
else
    sudo $PKG update -y 2>/dev/null || true
    sudo $PKG install -y python3-pip python3-venv git wget curl 2>/dev/null || true
fi

echo -e "${GREEN}✓${NC} Dependencias del sistema instaladas"

# Crear entorno virtual
echo -e "${YELLOW}🗄️  Creando entorno virtual...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Entorno virtual creado"
else
    echo -e "${GREEN}✓${NC} El entorno virtual ya existe"
fi

# Activar venv
echo -e "${YELLOW}📚 Activando entorno virtual...${NC}"
source venv/bin/activate

# Actualizar pip
echo -e "${YELLOW}📥 Actualizando pip...${NC}"
pip install --upgrade pip setuptools wheel -q 2>/dev/null || true

# Instalar dependencias de Python
echo -e "${YELLOW}📦 Instalando dependencias de Python...${NC}"

pip install \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    python-dotenv>=1.0.0 \
    colorlog>=6.8.0 \
    aiohttp>=3.9.0 \
    aiohttp-socks>=0.8.0 \
    -q 2>/dev/null || pip install pydantic pydantic-settings python-dotenv colorlog aiohttp aiohttp-socks

echo -e "${GREEN}✓${NC} Dependencias de Python instaladas"

# Crear .env desde ejemplo si no existe
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Creando archivo de configuración...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} .env creado desde .env.example"
    else
        cat > .env << 'ENVFILE'
# Solana Memecoin Trading Bot - Configuration
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
BIRDEYE_API_KEY=your_birdeye_api_key_here
WALLET_PRIVATE_KEY=your_private_key_base58_here
DRY_RUN=true
ENVFILE
        echo -e "${GREEN}✓${NC} .env creado"
    fi
    echo -e "${YELLOW}⚠️  Por favor edita .env con tus credenciales${NC}"
else
    echo -e "${GREEN}✓${NC} .env ya existe"
fi

# Verificar que el script principal existe
if [ ! -f "solana_bot_complete.py" ]; then
    echo -e "${RED}❌ Error: solana_bot_complete.py no encontrado${NC}"
    exit 1
fi

# Hacer ejecutable el script
chmod +x solana_bot_complete.py

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}${BOLD}                  ✅ INSTALACIÓN COMPLETADA                     ${NC}${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}Próximos pasos:${NC}"
echo ""
echo -e "  1. Edita la configuración:"
echo -e "     ${CYAN}nano .env${NC}"
echo ""
echo -e "  2. Activa el entorno virtual:"
echo -e "     ${CYAN}source venv/bin/activate${NC}"
echo ""
echo -e "  3. Ejecuta backtesting (no necesita credenciales):"
echo -e "     ${CYAN}python solana_bot_complete.py backtest --sesiones 1000${NC}"
echo ""
echo -e "  4. O ejecuta en modo simulación:"
echo -e "     ${CYAN}python solana_bot_complete.py dryrun${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "  - Nunca compartas tu clave privada"
echo "  - Siempre empieza en modo dry-run"
echo "  - Usa una billetera dedicada para trading"
echo ""