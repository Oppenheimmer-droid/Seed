#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  SOLANA AUTONOMOUS TRADING BOT - RISK MODE
#  Script de ejecución rápida
# ═══════════════════════════════════════════════════════════════

# Colores
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${YELLOW}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     SOLANA AUTONOMOUS TRADING BOT - RISK MODE         ║"
echo "║     ⚠️  SIN FILTROS DE SEGURIDAD ⚠️                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no encontrado${NC}"
    exit 1
fi

# Verificar aiohttp
python3 -c "import aiohttp" 2>/dev/null || {
    echo -e "${YELLOW}📦 Instalando dependencias...${NC}"
    pip3 install aiohttp
}

# Función de ayuda
show_help() {
    echo ""
    echo -e "${GREEN}USO:${NC}"
    echo "  $0 run <PRIVATE_KEY> [opciones]"
    echo "  $0 snipe <PRIVATE_KEY> <TOKEN_MINT> [opciones]"
    echo "  $0 monitor <PRIVATE_KEY> <TOKEN_MINT> [opciones]"
    echo ""
    echo -e "${GREEN}OPCIONES:${NC}"
    echo "  --amount    Cantidad en SOL por trade (default: 0.1)"
    echo "  --slippage  Slippage en BPS (default: 1000)"
    echo "  --rpc       RPC URL (default: Solana mainnet)"
    echo ""
    echo -e "${GREEN}EJEMPLOS:${NC}"
    echo "  $0 run 4jNXt7ZFV... --amount 0.05"
    echo "  $0 snipe 4jNXt7ZFV... DezXAZ8z7PnrnRJjz3wXBoRgixCa6jnB7 0.25"
    echo "  $0 monitor 4jNXt7ZFV... --token DezXAZ8z7PnrnRJjz3wXBoRgixCa6jnB7"
    echo ""
}

# Sin argumentos
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

COMMAND=$1
shift

# Ejecutar
case $COMMAND in
    run|snipe|monitor)
        echo -e "${YELLOW}▶️ Ejecutando: $COMMAND${NC}"
        python3 solana_bot_risk.py $COMMAND "$@"
        ;;
    generate)
        python3 solana_bot_risk.py run generate
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Comando desconocido: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac
