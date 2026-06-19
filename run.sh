#!/data/data/com.termux/files/usr/bin/bash
# ============================================
# Solana Memecoin Trading Bot v0.3
# Menú Principal - Termux/Android
# ============================================

# Versión
VERSION="0.3"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null
else
    echo -e "${RED}❌ Entorno virtual no encontrado${NC}"
    echo "   Ejecuta primero: bash setup_termux.sh"
    exit 1
fi

# Cargar .env
if [ -f ".env" ]; then
    set -a
    source .env 2>/dev/null
    set +a
fi

# Función para validar private key
validar_key() {
    local key="$1"
    local len=${#key}
    
    # Private key válida: ~88 caracteres en base58 (64 bytes)
    if [ "$len" -ge 80 ]; then
        echo "OK"
    elif [ "$len" -ge 40 ] && [ "$len" -lt 60 ]; then
        echo "PUBLIC_KEY"  # Probablemente es public key
    else
        echo "INVALID"
    fi
}

# Función para mostrar estado
mostrar_estado() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║        🤖 SOLANA MEMECOIN BOT v${VERSION}                        ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║                                                          ║"
    
    # Validar wallet
    KEY_STATUS="❌ No configurada"
    if [ -n "$WALLET_PRIVATE_KEY" ] && [ "$WALLET_PRIVATE_KEY" != "your_private_key_base58_here" ]; then
        key_result=$(validar_key "$WALLET_PRIVATE_KEY")
        if [ "$key_result" = "OK" ]; then
            KEY_STATUS="✅ Configurada (${#WALLET_PRIVATE_KEY} chars)"
        elif [ "$key_result" = "PUBLIC_KEY" ]; then
            KEY_STATUS="⚠️  PARECE PUBLIC KEY (necesitas private key)"
        else
            KEY_STATUS="❌ Inválida"
        fi
    fi
    
    # Validar RPC
    if [ -n "$SOLANA_RPC_URL" ]; then
        RPC_STATUS="✅ ${SOLANA_RPC_URL:0:35]}..."
    else
        RPC_STATUS="❌ No configurada"
    fi
    
    # Validar Birdeye
    if [ -n "$BIRDEYE_API_KEY" ] && [ "$BIRDEYE_API_KEY" != "your_birdeye_api_key_here" ]; then
        BIRDEYE_STATUS="✅ Configurada"
    else
        BIRDEYE_STATUS="⚠️  No configurada"
    fi
    
    # Capital
    CAPITAL=${CAPITAL_INICIAL:-500}
    OBJETIVO=${OBJETIVO_GLOBAL:-615}
    
    echo "║  👛 Wallet:  $KEY_STATUS"
    echo "║  🌐 RPC:     $RPC_STATUS"
    echo "║  📊 Birdeye: $BIRDEYE_STATUS"
    echo "║  💰 Capital: ${CAPITAL} SOL"
    echo "║  🎯 Objetivo: ${OBJETIVO} SOL"
    echo "║                                                          ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║                                                          ║"
    echo "║  1. 🎮 SIMULACRO v0.3  — Nueva UI mejorada            ║"
    echo "║  2. 📈 BACKTEST      — Simulación histórica 10k sesiones║"
    echo "║  3. 🚀 TRADING REAL  — Con SOL real (⚠️  MUY PELIGRO) ║"
    echo "║  4. 🔍 VERIFICAR     — Diagnosticar sistema             ║"
    echo "║  5. ⚙️  CONFIGURAR    — Editar .env                    ║"
    echo "║  6. 📋 VER LOGS      — Historial de trades            ║"
    echo "║  7. 📊 VERIFICACIÓN  — Estadísticas                  ║"
    echo "║  8. ❌ SALIR                                             ║"
    echo "║                                                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
}

# Función para iniciar simulacro
iniciar_simulacro() {
    echo ""
    echo -e "${CYAN}🎮 MODO SIMULACRO v0.3${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✅ Interfaz visual mejorada con barras de progreso"
    echo "  ✅ Detecta pumps y aplica martingala"
    echo "  ✅ Filtros de seguridad activos"
    echo "  ✅ Muestra ROI en tiempo real"
    echo "  ❌ NO ejecuta transacciones reales"
    echo "  ❌ NO gasta SOL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    mkdir -p logs
    
    # Verificar si tmux está disponible
    if command -v tmux &> /dev/null; then
        echo -e "${GREEN}Ejecutando con tmux...${NC}"
        tmux kill-session -t solana_sim 2>/dev/null
        tmux new-session -d -s solana_sim \
            "cd '$SCRIPT_DIR' && source venv/bin/activate && python simulacro.py 2>&1 | tee -a logs/simulacro.log"
        sleep 1
        echo ""
        echo -e "${GREEN}✅ Simulacro iniciado en background${NC}"
        echo "   Ver logs: tmux attach -t solana_sim"
        echo "   Detener:  tmux kill-session -t solana_sim"
        echo ""
        read -p "¿Ver simulacro ahora? (s/n): " verlog
        if [ "$verlog" = "s" ] || [ "$verlog" = "S" ]; then
            tmux attach-session -t solana_sim
        fi
    else
        echo -e "${YELLOW}Ejecutando en primer plano...${NC}"
        echo "   Presiona Ctrl+C para detener"
        echo ""
        python simulacro.py
    fi
}

# Función para backtest
iniciar_backtest() {
    echo ""
    echo -e "${CYAN}📈 MODO BACKTEST${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    read -p "Número de sesiones [1000]: " SESIONES
    SESIONES=${SESIONES:-1000}
    
    echo -e "${CYAN}Ejecutando backtest con $SESIONES sesiones...${NC}"
    echo ""
    
    python solana_bot_complete.py backtest --sesiones $SESIONES
    
    echo ""
    read -p "Presiona Enter para continuar..."
}

# Función para iniciar modo real
iniciar_real() {
    echo ""
    echo -e "${RED}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║${NC}${BOLD}          🚨⚠️  ATENCIÓN: TRADING REAL ⚠️🚨                   ${NC}${RED}║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  ⚠️  USARÁ SOL REAL DE TU WALLET"
    echo "  ⚠️  PUEDES PERDER TODA TU INVERSIÓN"
    echo "  ⚠️  Capital: ${CAPITAL_INICIAL:-500} SOL"
    echo "  ⚠️  Stop Loss: ${STOP_LOSS_GLOBAL:-100} SOL"
    echo ""
    
    # Validar private key
    if [ -n "$WALLET_PRIVATE_KEY" ]; then
        key_result=$(validar_key "$WALLET_PRIVATE_KEY")
        if [ "$key_result" = "PUBLIC_KEY" ]; then
            echo -e "${RED}❌ ERROR: La private key parece ser una PUBLIC KEY${NC}"
            echo ""
            echo "   Tu wallet tiene ${#WALLET_PRIVATE_KEY} caracteres."
            echo "   Una private key válida tiene ~88 caracteres."
            echo ""
            echo "   Para obtener tu private key:"
            echo "   1. Abre Phantom Wallet"
            echo "   2. ⚙️  → Selecciona wallet → Export Private Key"
            echo "   5. Copia la clave (empieza con números, no con '7xK...')"
            echo ""
            read -p "Presiona Enter para volver al menú..."
            return
        elif [ "$key_result" = "INVALID" ]; then
            echo -e "${RED}❌ ERROR: Private key inválida${NC}"
            read -p "Presiona Enter para volver al menú..."
            return
        fi
    else
        echo -e "${RED}❌ ERROR: Private key no configurada${NC}"
        read -p "Presiona Enter para configurar..."
        nano .env
        return
    fi
    
    echo -e "${YELLOW}Escribe 'CONFIRMO' para continuar:${NC}"
    read -p "> " confirm
    
    if [ "$confirm" = "CONFIRMO" ]; then
        mkdir -p logs
        
        if command -v tmux &> /dev/null; then
            echo -e "${RED}⚠️  Iniciando trading REAL en background...${NC}"
            tmux kill-session -t solana_real 2>/dev/null
            tmux new-session -d -s solana_real \
                "cd '$SCRIPT_DIR' && source venv/bin/activate && python trading_real.py --start 2>&1 | tee -a logs/real.log"
            sleep 1
            echo ""
            echo -e "${RED}✅ Trading REAL iniciado${NC}"
            echo "   Ver: tmux attach -t solana_real"
            echo "   Stop: tmux kill-session -t solana_real"
        else
            echo -e "${RED}Ejecutando en primer plano...${NC}"
            python trading_real.py --start
        fi
    else
        echo -e "${YELLOW}❌ Cancelado${NC}"
    fi
    
    read -p "Presiona Enter para continuar..."
}

# Función para ver logs
ver_logs() {
    echo ""
    echo -e "${CYAN}📋 LOGS DISPONIBLES:${NC}"
    echo ""
    
    if [ -d "logs" ]; then
        ls -la logs/ 2>/dev/null || echo "Directorio vacío"
    else
        echo "Sin logs todavía"
    fi
    
    echo ""
    echo "1. Simulacro (simulacro.log)"
    echo "2. Real (trading_real.log)"
    echo "3. Bot activo (tmux)"
    echo "4. Volver"
    read -p "Ver (1-4): " logopt
    
    case $logopt in
        1)
            if [ -f "logs/simulacro.log" ]; then
                tail -100 logs/simulacro.log
            else
                echo "Sin logs de simulacro"
            fi
            ;;
        2)
            if [ -f "logs/trades_real.log" ]; then
                tail -100 logs/trades_real.log
            else
                echo "Sin logs de trading real"
            fi
            ;;
        3)
            if command -v tmux &> /dev/null; then
                echo "Sesiones activas:"
                tmux list-sessions 2>/dev/null || echo "  No hay sesiones activas"
                echo ""
                echo "1. Attach sim (solana_sim)"
                echo "2. Attach real (solana_real)"
                read -p "Selecciona (1-2): " attachopt
                case $attachopt in
                    1) tmux attach-session -t solana_sim 2>/dev/null || echo "No activo" ;;
                    2) tmux attach-session -t solana_real 2>/dev/null || echo "No activo" ;;
                esac
            else
                echo "tmux no disponible"
            fi
            ;;
        *) return ;;
    esac
    
    echo ""
    read -p "Presiona Enter para continuar..."
}

# Función verificar
verificar_sistema() {
    echo ""
    echo -e "${CYAN}🔍 VERIFICACIÓN DEL SISTEMA${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    python solana_bot_complete.py verify --full
    
    echo ""
    read -p "Presiona Enter para continuar..."
}

ver_estadisticas() {
    echo ""
    echo -e "${CYAN}📊 ESTADÍSTICAS${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -f "backtest_results.json" ]; then
        echo ""
        echo "Último Backtest:"
        cat backtest_results.json
    else
        echo ""
        echo "No hay resultados de backtest."
        echo "Ejecuta: python solana_bot_complete.py backtest --sesiones 1000"
    fi
    
    echo ""
    read -p "Presiona Enter para continuar..."
}

# ============================================
# MAIN LOOP
# ============================================

while true; do
    mostrar_estado
    read -p "Selecciona (1-8): " opt
    
    case $opt in
        1) iniciar_simulacro ;;
        2) iniciar_backtest ;;
        3) iniciar_real ;;
        4) verificar_sistema ;;
        5)
            nano .env
            set -a
            source .env 2>/dev/null
            set +a
            ;;
        6) ver_logs ;;
        7) ver_estadisticas ;;
        8)
            echo ""
            echo -e "${CYAN}👋 Saliendo...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Opción inválida${NC}"
            sleep 1
            ;;
    esac
done