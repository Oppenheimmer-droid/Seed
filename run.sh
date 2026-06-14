#!/bin/bash
# ============================================
# Solana Memecoin Trading Bot
# Quick Run Script - Termux/Linux
# ============================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${CYAN}🟢 Entorno virtual activado${NC}"
else
    echo -e "${YELLOW}⚠️  Entorno virtual no encontrado. Ejecuta primero: ./install_termux.sh${NC}"
    exit 1
fi

# Verificar que el bot existe
if [ ! -f "solana_bot_complete.py" ]; then
    echo -e "${RED}❌ Error: solana_bot_complete.py no encontrado${NC}"
    exit 1
fi

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}🪄 Solana Memecoin Trading Bot${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Modos de uso:"
echo "  ${CYAN}./run.sh backtest --sesiones 1000${NC}  → Simulación histórica"
echo "  ${CYAN}./run.sh dryrun <WALLET>${NC}            → Simulación sin TX"
echo "  ${CYAN}./run.sh run <WALLET>${NC}                → Trading real (⚠️)"
echo ""

# Si no hay argumentos, mostrar ayuda
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Ejecutando backtest por defecto...${NC}"
    echo ""
    python solana_bot_complete.py backtest --sesiones 100
else
    # Pasar argumentos al bot
    python solana_bot_complete.py "$@"
fi