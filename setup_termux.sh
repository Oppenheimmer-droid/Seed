# ============================================
# Solana Memecoin Trading Bot
# Quick Setup for Termux (Android)
# One-command installation
# ============================================

set -e

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

# Step 1: Install system packages
echo -e "${YELLOW}📦 [1/4] Instalando dependencias del sistema...${NC}"
pkg update -y 2>/dev/null || true
pkg upgrade -y 2>/dev/null || true
pkg install -y python git curl wget 2>/dev/null || true
echo -e "${GREEN}✓${NC} Dependencias instaladas"

# Step 2: Create venv
echo -e "${YELLOW}🗄️  [2/4] Creando entorno virtual...${NC}"
if [ ! -d "venv" ]; then
    python -m venv venv
    echo -e "${GREEN}✓${NC} Entorno virtual creado"
else
    echo -e "${GREEN}✓${NC} Entorno virtual ya existe"
fi

# Step 3: Install Python packages
echo -e "${YELLOW}📥 [3/4] Instalando paquetes de Python...${NC}"
source venv/bin/activate
pip install --upgrade pip -q 2>/dev/null || true
pip install pydantic pydantic-settings python-dotenv colorlog aiohttp aiohttp-socks -q 2>/dev/null || \
pip install pydantic pydantic-settings python-dotenv colorlog aiohttp aiohttp-socks
echo -e "${GREEN}✓${NC} Paquetes instalados"

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
chmod +x install_termux.sh run.sh solana_bot_complete.py

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