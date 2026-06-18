#!/data/data/com.termux/files/usr/bin/bash
# setup_termux.sh v2.1
# Solana Memecoin Trading Bot - Setup Termux (Android ARM64)

set -e
echo "🪄 Solana Bot v2.1 — Setup Termux"

# Detectar Termux
if [ -f "/data/data/com.termux/files/usr/bin/bash" ] || [ -d "/data/data/com.termux/files/usr" ]; then
    IS_TERMUX=true
else
    IS_TERMUX=false
fi

# Instalar dependencias del sistema
echo -e "\033[36m📦 [1/5] Instalando dependencias del sistema...\033[0m"
pkg update -y 2>/dev/null || apt update -y 2>/dev/null || true
pkg install -y python git curl wget 2>/dev/null || apt install -y python3 python3-pip git curl wget 2>/dev/null || true
echo -e "\033[32m✓\033[0m Dependencias del sistema"

# Crear venv
echo -e "\033[36m🗄️  [2/5] Creando entorno virtual...\033[0m"
[ -d "venv" ] && rm -rf venv
python -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
echo -e "\033[32m✓\033[0m Entorno virtual creado"

# Instalar paquetes Python (sin Rust)
echo -e "\033[36m📥 [3/5] Instalando paquetes Python...\033[0m"
pip install \
    "aiohttp==3.14.1" \
    "aiohttp-socks==0.11.0" \
    "base58==2.1.1" \
    "python-dotenv==1.2.2" \
    "colorlog==6.10.1" \
    "httpx==0.28.1" \
    -q 2>/dev/null || \
pip install aiohttp aiohttp-socks base58 python-dotenv colorlog httpx

# cryptography: intentar wheel precompilado primero
pip install cryptography --only-binary=:all: -q 2>/dev/null && echo -e "\033[32m✓\033[0m cryptography (wheel)" || {
    echo -e "\033[33m⚠️  cryptography wheel no disponible, usando fallback puro\033[0m"
}

# PyNaCl: intentar wheel precompilado
pip install PyNaCl==1.5.0 --only-binary=:all: -q 2>/dev/null && echo -e "\033[32m✓\033[0m PyNaCl (wheel)" || {
    echo -e "\033[33m⚠️  PyNaCl wheel no disponible, usando ed25519_pure.py\033[0m"
}

echo -e "\033[32m✓\033[0m Paquetes Python"

# Verificar
echo -e "\033[36m🔍 [4/5] Verificando instalación...\033[0m"
python -c "
import aiohttp, base58, dotenv, colorlog, httpx
print('  ✅ Dependencias base OK')
try:
    import nacl
    print('  ✅ PyNaCl OK')
except ImportError:
    print('  ⚠️  PyNaCl no disponible — usando ed25519_pure.py')
try:
    import cryptography
    print('  ✅ cryptography OK')
except ImportError:
    print('  ⚠️  cryptography no disponible — firma fallback activa')
"

# Crear .env con validación
echo -e "\033[36m📝 [5/5] Configurando...\033[0m"
if [ ! -f ".env" ]; then
    cat > .env << 'ENVEOF'
# Solana Memecoin Trading Bot v2.1 - Configuration
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
BIRDEYE_API_KEY=your_birdeye_api_key_here
WALLET_PRIVATE_KEY=your_private_key_base58_here
DRY_RUN=true
CAPITAL_INICIAL=500
OBJETIVO_GLOBAL=615
STOP_LOSS_GLOBAL=100
ENVEOF
fi

# Verificar Birdeye API Key
BIRDEYE_KEY=$(grep "^BIRDEYE_API_KEY=" .env 2>/dev/null | cut -d'=' -f2-)
if [[ "$BIRDEYE_KEY" == http* ]]; then
    echo -e "\033[31m❌ ERROR: BIRDEYE_API_KEY es una URL, no un API key\033[0m"
    echo -e "   ❌ Incorrecto: https://public-api.birdeye.so/defi/price"
    echo -e "   ✅ Correcto: 76641762bca44ff68ad89cd254b70e2d"
    echo -e "   Edita .env y cambia BIRDEYE_API_KEY al valor correcto"
    echo -e "   Obtén tu key en: https://birdeye.so/profile/api"
fi

# Hacer scripts ejecutables
chmod +x run.sh setup_termux.sh solana_bot_complete.py *.py 2>/dev/null || true

echo ""
echo -e "\033[32m╔══════════════════════════════════════════════════════════╗\033[0m"
echo -e "\033[32m║\033[0m\033[1m            ✅ SETUP COMPLETADO v2.1                     \033[0m\033[32m║\033[0m"
echo -e "\033[32m╚══════════════════════════════════════════════════════════╝\033[0m"
echo ""
echo -e "\033[1mCómo usar:\033[0m"
echo "  1. source venv/bin/activate"
echo "  2. ./run.sh              → Menú interactivo"
echo ""
echo -e "\033[33m⚠️  IMPORTANTE:\033[0m"
echo "  - Edita .env con tus credenciales reales"
echo "  - BIRDEYE_API_KEY debe ser la KEY, no la URL"
echo "  - WALLET_PRIVATE_KEY debe ser la PRIVATE KEY (~88 chars)"
echo "  - Empieza siempre en modo SIMULACRO"
echo ""
