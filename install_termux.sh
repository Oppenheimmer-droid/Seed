#!/bin/bash
# ============================================
# Solana Memecoin Trading Bot
# Install Script for Termux (Android) / Linux
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
echo "║   ${BOLD}Install Script for Termux/Android${NC}${CYAN}                   ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Detect OS
if [ -f /data/data/com.termux/files/usr/bin/bash ]; then
    IS_TERMUX=true
    PKG="pkg"
else
    IS_TERMUX=false
    PKG="apt-get"
fi

echo -e "${YELLOW}📋 Checking system...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    if [ "$IS_TERMUX" = true ]; then
        echo "   Run: pkg install python"
    else
        echo "   Run: sudo apt install python3 python3-pip python3-venv"
    fi
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  ${GREEN}✓${NC} Python $PYTHON_VERSION"

# Install system dependencies
echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
if [ "$IS_TERMUX" = true ]; then
    $PKG update -y
    $PKG upgrade -y
    $PKG install -y git wget curl openssl libffi
    # Optional: for compiling Rust packages
    # $PKG install -y rust cargo clang make
else
    sudo $PKG update -y
    sudo $PKG install -y python3-pip python3-venv git wget curl
fi

# Create virtual environment
echo -e "${YELLOW}🗄️  Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}📥 Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel -q

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"

# Core dependencies (without solana package that requires Rust compiler)
pip install \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    python-dotenv>=1.0.0 \
    colorlog>=6.8.0 \
    aiohttp>=3.9.0 \
    -q

# Optional: Try to install Solana SDK (requires Rust on Termux)
if [ "$IS_TERMUX" = true ]; then
    echo -e "${YELLOW}⚠️  Note: 'solana' package requires Rust compiler${NC}"
    echo "   For full trading, run: pkg install rust cargo clang make"
    echo "   Then: pip install solana solders"
else
    pip install solana solders base58 -q 2>/dev/null || true
fi

echo -e "${GREEN}✓${NC} Dependencies installed"

# Create .env from example if not exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Creating configuration file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓${NC} .env created"
    echo -e "${YELLOW}⚠️  Please edit .env with your credentials${NC}"
else
    echo -e "${GREEN}✓${NC} .env already exists"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}${BOLD}                  ✅ INSTALLATION COMPLETED                     ${NC}${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo ""
echo -e "  1. Edit configuration:"
echo -e "     ${CYAN}nano .env${NC}"
echo ""
echo -e "  2. Run backtesting (no credentials needed):"
echo -e "     ${CYAN}source venv/bin/activate${NC}"
echo -e "     ${CYAN}python solana_bot_complete.py backtest --sesiones 1000${NC}"
echo ""
echo -e "  3. Run in dry-run mode:"
echo -e "     ${CYAN}source venv/bin/activate${NC}"
echo -e "     ${CYAN}python solana_bot_complete.py dryrun${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "  - Never share your private key"
echo "  - Always start in dry-run mode"
echo "  - Use a dedicated wallet for trading"
echo ""