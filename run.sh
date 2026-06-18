#!/data/data/com.termux/files/usr/bin/bash
# run.sh v2.1 — Menú interactivo para Solana Bot

set -e
cd "$(dirname "$0")"

# Activar venv
source venv/bin/activate 2>/dev/null || {
    echo "❌ Ejecuta setup_termux.sh primero"
    exit 1
}

# Cargar .env
set -a
source .env 2>/dev/null || true
set +a

# Crear directorio de logs
mkdir -p logs

# ── FUNCIONES ──────────────────────────────────────────────

mostrar_estado() {
    local wallet_ok="❌ No configurada"
    local birdeye_ok="❌ No configurada"
    local rpc_ok="✅"

    # Validar private key
    local key_len=${#WALLET_PRIVATE_KEY}
    if [ "$key_len" -ge 85 ] 2>/dev/null; then
        wallet_ok="✅ Configurada (${key_len} chars)"
    elif [ "$key_len" -ge 40 ] 2>/dev/null; then
        wallet_ok="⚠️  Parece public key — necesitas private key"
    fi

    # Validar Birdeye key (no debe ser URL)
    if [ -n "$BIRDEYE_API_KEY" ] && \
       [ "$BIRDEYE_API_KEY" != "your_birdeye_api_key_here" ] && \
       [[ "$BIRDEYE_API_KEY" != http* ]]; then
        birdeye_ok="✅ Configurada"
    elif [[ "$BIRDEYE_API_KEY" == http* ]]; then
        birdeye_ok="❌ Es una URL, no un API key"
    fi

    echo "  💰 Wallet:  $wallet_ok"
    echo "  🌐 RPC:     $rpc_ok $SOLANA_RPC_URL"
    echo "  🔑 Birdeye: $birdeye_ok"
    echo "  🎮 Modo:    ${DRY_RUN:-true}"
}

iniciar_bot() {
    local modo=$1
    local dry=$2
    local logfile="logs/${modo}.log"

    pkg install tmux -y -q 2>/dev/null || true
    termux-wake-lock 2>/dev/null || true
    tmux kill-session -t bot 2>/dev/null || true

    tmux new-session -d -s bot \
        "cd $(pwd) && \
         source venv/bin/activate && \
         DRY_RUN=${dry} python solana_bot_complete.py run \
         2>&1 | tee -a ${logfile}"

    echo ""
    echo "✅ Bot en $modo iniciado en background"
    echo "   Log: $logfile"
    echo ""
    read -p "¿Ver log en pantalla ahora? (s/n): " ver
    if [ "$ver" = "s" ] || [ "$ver" = "S" ]; then
        echo "━━━━ LOG EN VIVO (Ctrl+B, D para salir sin detener) ━━━━"
        tmux attach-session -t bot
    else
        echo "   Para ver después: tmux attach -t bot"
        echo "   Para detener:     tmux kill-session -t bot"
    fi
}

# ── MENÚ PRINCIPAL ─────────────────────────────────────────

mostrar_menu() {
    clear
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║       🤖 SOLANA MEMECOIN BOT v2.1 — PANEL DE CONTROL  ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    mostrar_estado
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║                                                          ║"
    echo "║  1. 🔵 SIMULACRO — Detecta tokens, sin trades         ║"
    echo "║  2. 🔴 REAL      — Trading con SOL real                 ║"
    echo "║  3. 📊 BACKTEST  — Simulación histórica                 ║"
    echo "║  4. 📋 LOGS      — Ver actividad reciente              ║"
    echo "║  5. ⚙️  CONFIG   — Editar configuración (.env)         ║"
    echo "║  6. 🛑 DETENER   — Parar bot en background             ║"
    echo "║  7. ❌ SALIR                                             ║"
    echo "║                                                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
}

# ── PROCESAR OPCIÓN ────────────────────────────────────────

procesar_opcion() {
    local opt=$1

    case $opt in

      1) # ── SIMULACRO ──────────────────────────────────────
        clear
        echo "🔵 MODO SIMULACRO"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  ✅ Conecta a Solana mainnet"
        echo "  ✅ Detecta tokens reales con Birdeye"
        echo "  ✅ Aplica filtros y estrategia completa"
        echo "  ✅ Muestra señales en pantalla"
        echo "  ✅ Simula P&L sin ejecutar transacciones"
        echo "  ❌ No gasta SOL"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        # Validar Birdeye
        if [[ "$BIRDEYE_API_KEY" == http* ]] || \
           [ "$BIRDEYE_API_KEY" = "your_birdeye_api_key_here" ]; then
            echo ""
            echo "⚠️  BIRDEYE_API_KEY inválida."
            echo "   Consigue tu clave en: https://birdeye.so/profile/api"
            echo "   Luego edita con opción 5 (CONFIG)"
            read -p "Presiona Enter para volver..."
            return
        fi
        echo ""
        read -p "¿Iniciar simulacro? (s/n): " c
        [ "$c" = "s" ] || [ "$c" = "S" ] && iniciar_bot "simulacro" "true"
        ;;

      2) # ── REAL ────────────────────────────────────────────
        clear
        echo "🔴 MODO REAL — TRADING CON SOL REAL"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  ⚠️  USARÁ SOL REAL DE TU WALLET"
        echo "  ⚠️  CAPITAL: ${CAPITAL_INICIAL:-500}u"
        echo "  ⚠️  OBJETIVO: ${OBJETIVO_GLOBAL:-615}u"
        echo "  ⚠️  STOP LOSS: ${STOP_LOSS_GLOBAL:-100}u"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        # Validar private key
        local key_len=${#WALLET_PRIVATE_KEY}
        if [ "$key_len" -lt 85 ] 2>/dev/null; then
            echo ""
            echo "❌ PRIVATE KEY INVÁLIDA"
            if [ "$key_len" -ge 40 ]; then
                echo "   Lo que tienes parece una PUBLIC KEY (wallet address)"
                echo "   En Phantom: Settings → Export Private Key"
                echo "   La private key tiene ~88 caracteres"
            else
                echo "   Configura tu private key con opción 5 (CONFIG)"
            fi
            read -p "Presiona Enter para volver..."
            return
        fi

        # Validar Birdeye
        if [[ "$BIRDEYE_API_KEY" == http* ]] || \
           [ "$BIRDEYE_API_KEY" = "your_birdeye_api_key_here" ]; then
            echo ""
            echo "❌ BIRDEYE_API_KEY inválida"
            echo "   Consigue tu clave en: https://birdeye.so/profile/api"
            read -p "Presiona Enter para volver..."
            return
        fi

        echo ""
        echo "Escribe OPERAR para confirmar (cualquier otra cosa cancela):"
        read -p "> " confirm
        if [ "$confirm" = "OPERAR" ]; then
            iniciar_bot "real" "false"
        else
            echo "❌ Cancelado"
            sleep 1
        fi
        ;;

      3) # ── BACKTEST ─────────────────────────────────────────
        clear
        echo "📊 MODO BACKTEST"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        read -p "Número de sesiones (Enter=1000): " sesiones
        sesiones=${sesiones:-1000}
        echo ""
        echo "Ejecutando backtest con $sesiones sesiones..."
        python solana_bot_complete.py backtest --sesiones "$sesiones"
        echo ""
        read -p "Presiona Enter para volver..."
        ;;

      4) # ── LOGS ────────────────────────────────────────────
        clear
        echo "📋 LOGS DISPONIBLES"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  1. Ver log simulacro (logs/simulacro.log)"
        echo "  2. Ver log real (logs/real.log)"
        echo "  3. Ver log bot (logs/bot.log)"
        echo "  4. Conectar a bot activo (tmux)"
        echo "  5. Volver"
        echo ""
        read -p "Opción: " logopt
        case $logopt in
          1) tail -n 50 logs/simulacro.log 2>/dev/null \
               || echo "Sin log de simulacro todavía" ;;
          2) tail -n 50 logs/real.log 2>/dev/null \
               || echo "Sin log real todavía" ;;
          3) tail -n 50 logs/bot.log 2>/dev/null \
               || echo "Sin log todavía" ;;
          4) tmux attach-session -t bot 2>/dev/null \
               || echo "Bot no activo (inicia desde opción 1 o 2)" ;;
          5) return ;;
        esac
        read -p "Enter para volver..."
        ;;

      5) # ── CONFIG ──────────────────────────────────────────
        echo ""
        echo "⚙️  CONFIGURACIÓN — Editando .env"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  ⚠️  BIRDEYE_API_KEY debe ser el API key, NO una URL"
        echo "     Ejemplo correcto: 76641762bca44ff68ad89cd254b70e2d"
        echo "     Ejemplo INCORRECTO: https://public-api.birdeye.so/..."
        echo ""
        echo "  ⚠️  WALLET_PRIVATE_KEY debe ser la PRIVATE KEY"
        echo "     Desde Phantom: Settings → Export Private Key"
        echo "     Tiene ~88 caracteres en base58"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        read -p "Presiona Enter para abrir editor..."
        nano .env
        ;;

      6) # ── DETENER ─────────────────────────────────────────
        tmux kill-session -t bot 2>/dev/null \
          && echo "✅ Bot detenido" \
          || echo "ℹ️  Bot no estaba activo"
        read -p "Enter para continuar..."
        ;;

      7) echo "👋 Saliendo..."; exit 0 ;;

      *) echo "Opción inválida"; sleep 1 ;;
    esac
}

# ── LOOP PRINCIPAL ─────────────────────────────────────────

if [ $# -gt 0 ]; then
    # Modo línea de comandos
    case $1 in
      backtest)
        source venv/bin/activate
        python solana_bot_complete.py backtest --sesiones "${2:-1000}"
        ;;
      run)
        source venv/bin/activate
        DRY_RUN="${DRY_RUN:-true}" python solana_bot_complete.py run
        ;;
      *)
        echo "Uso: $0 [backtest|run]"
        echo "  backtest [n]  - Simulación histórica"
        echo "  run            - Trading bot"
        ;;
    esac
else
    # Modo interactivo
    while true; do
        mostrar_menu
        read -p "Selecciona (1-7): " opt
        procesar_opcion "$opt"
    done
fi