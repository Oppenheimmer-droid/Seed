# Solana Memecoin Bot - Guía de Instalación Termux

## Índice
1. [Instalación en Termux](#instalación-en-termux)
2. [Configuración Inicial](#configuración-inicial)
3. [Casos de Uso](#casos-de-uso)
4. [Uso del Scanner DexScreener](#uso-del-scanner-dexscreener)
5. [Solución de Problemas](#solución-de-problemas)

---

## Instalación en Termux

### Requisitos
- Android 7.0+ (ARM64 recomendado)
- Termux desde F-Droid (no Google Play - versión actualizada)

### Paso 1: Instalar Termux
```bash
# Descargar desde F-Droid (recomendado)
# https://f-droid.org/en/packages/com.termux/

# O buscar "Termux" en F-Droid
```

### Paso 2: Actualizar Termux
```bash
pkg update && pkg upgrade -y
```

### Paso 3: Instalar Python
```bash
pkg install python -y
python --version  # Verificar Python 3.x
```

### Paso 4: Instalar dependencias
```bash
pip install --upgrade pip
pip install aiohttp aiohttp-socks python-dotenv colorlog base58 httpx
```

### Paso 5: Clonar el repositorio
```bash
cd ~/storage/shared  # o ~/storage/downloads
git clone https://github.com/Oppenheimmer-droid/Seed.git
cd Seed
```

### Paso 6: Verificar instalación
```bash
python solana_bot_complete.py --help
```

---

## Configuración Inicial

### 1. Crear archivo .env
```bash
cp .env.example .env
nano .env
```

### 2. Configurar variables
```env
# RPC de Solana (gratuito)
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# DexScreener (gratuito, sin API key)
DEXSCREENER_BASE_URL=https://api.dexscreener.com

# Wallet (PRIVATE - NUNCA COMMITEAR!)
WALLET_PRIVATE_KEY=tu_clave_privada_base58_aqui

# Modo: true = simulación, false = trading real
DRY_RUN=true
```

### 3. Configurar Wallet (opcional para backtest)
```bash
# Para trading real, necesitas tu private key en base58
# ¡NUNCA compartas tu private key!
```

---

## Casos de Uso

### Caso 1: Backtest (Sin Wallet Requerida)
Prueba la estrategia con datos históricos simulados.

```bash
# Backtest rápido (100 sesiones)
python solana_bot_complete.py backtest --sesiones 100

# Backtest completo (10000 sesiones)
python solana_bot_complete.py backtest --sesiones 10000

# Verificación de estadísticas
python solana_bot_complete.py verify --full
```

**Salida esperada:**
```
======================================================================
🧪 INICIANDO BACKTEST
======================================================================
   Capital: 500.0u → Objetivo: 615.0u
   Completado en 0.0s

📊 RESULTADOS SESIÓN
  Éxito (≥615.0u):  86.2% (teórico)
  Capital prom:  847.0u
  Win rate:     75.0%
```

---

### Caso 2: Simulación Dry-Run (Wallet Opcional)
Simula trading sin enviar transacciones reales.

```bash
# Modo simulación (DRY_RUN=true por defecto)
python solana_bot_complete.py run

# Con wallet (solo para mostrar dirección)
python solana_bot_complete.py run --real
# ⚠️  Salida: MODO REAL ACTIVADO
```

**Comportamiento:**
- Detecta pumps en tokens via DexScreener
- Simula compras y martingalas
- Muestra logs de operaciones
- No envía transacciones a la blockchain

---

### Caso 3: Trading Real (⚠️ PELIGRO)
Ejecuta operaciones reales con SOL.

```bash
# 1. CONFIGURAR .env
nano .env
# DRY_RUN=false
# WALLET_PRIVATE_KEY=tu_clave_real

# 2. VERIFICAR dos veces antes de ejecutar
python solana_bot_complete.py verify --full

# 3. EJECUTAR con extrema precaución
python solana_bot_complete.py run --real
```

**⚠️  ADVERTENCIAS:**
- Solo para usuarios experimentados
- Riesgo de pérdida total de capital
- Empezar con capital pequeño
- Monitorear constantemente

---

### Caso 4: Menú Interactivo
```bash
./run.sh
```

Opciones del menú:
```
╔══════════════════════════════════════╗
║   SOLANA MEMECOIN BOT - MENÚ       ║
╠══════════════════════════════════════╣
║  1. 🧪 Backtest (100 sesiones)     ║
║  2. 🧪 Backtest (10000 sesiones)    ║
║  3. 🔵 Simulación Dry-Run          ║
║  4. 🔴 Trading Real (⚠️)            ║
║  5. 📊 Verificar Estadísticas       ║
║  6. 📝 Ver Logs                     ║
║  0. 🚪 Salir                       ║
╚══════════════════════════════════════╝
```

---

## Uso del Scanner DexScreener

El scanner usa DexScreener como fuente de datos primaria para detectar pumps.

### Desde Python (API directa)

```python
import asyncio
from dexscreener import DexScreenerClient

async def ejemplo():
    client = DexScreenerClient()
    
    # Obtener precio de SOL
    sol_price = await client.get_precio_sol_usd()
    print(f"SOL: ${sol_price:.2f}")
    
    # Escanear tokens con pump
    pumps = await client.escanear_pumps(
        pump_minimo=0.10,        # 10% mínimo
        liquidez_minima_sol=10,  # 10 SOL mínimo
        volumen_minimo_sol=50,   # 50 SOL en 5min
        pool_age_min_seconds=120 # Pool con 2+ minutos
    )
    
    for token in pumps:
        print(f"🚀 {token.symbol}: {token.change_m5:+.1f}%")
        print(f"   Liquidez: ${token.liquidity_usd:,.0f}")
        print(f"   Volumen 5m: ${token.volume_m5:,.0f}")
    
    await client.close()

asyncio.run(ejemplo())
```

### Integración con el Bot

El bot usa automáticamente DexScreener:

```python
# El Scanner del bot usa DexScreener
from solana_bot_complete import Scanner

async def detectar_pumps():
    scanner = Scanner()
    
    # Escanear tokens
    tokens = await scanner.escanear()
    
    for token in tokens:
        print(f"{token.symbol}: pump={token.pump_percent*100:.1f}%")
    
    await scanner.close()

asyncio.run(detectar_pumps())
```

### Endpoints DexScreener Utilizados

| Endpoint | Uso |
|----------|-----|
| `/latest/dex/tokens/{addr}` | Datos de token específico |
| `/token-profiles/latest/v1` | Nuevos tokens en Solana |
| `/token-boosts/latest/v1` | Tokens con boost activo |
| `/latest/dex/search?q={query}` | Búsqueda por nombre |
| `/latest/dex/tokens/SOL` | Precio SOL/USDC |

---

## Solución de Problemas

### Error: "No module named 'base58'"
```bash
pip install base58
```

### Error: "aiohttp timeout"
```bash
# Verificar conexión
ping api.dexscreener.com

# Aumentar timeout en el código si es necesario
```

### Error: "Wallet inválida"
```bash
# Verificar formato de private key (base58)
python -c "from wallet import SolanaWallet; w = SolanaWallet('tu_key')"
```

### Error: "RPC no responde"
```bash
# Cambiar RPC en .env
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
# O usar otro público:
# SOLANA_RPC_URL=https://solana-api.projectserum.com
```

### Termux: "Permission denied"
```bash
# Dar permisos de almacenamiento
termux-setup-storage

# Luego aceptar los permisos en la app
```

### Optimizar Rendimiento en Android
```bash
# Usar swap si hay poca RAM
pkg install termux-services

# Reducir sesiones de backtest si es lento
python solana_bot_complete.py backtest --sesiones 1000
```

---

## Estructura de Archivos

```
Seed/
├── solana_bot_complete.py   # Bot principal
├── dexscreener.py           # Cliente DexScreener
├── wallet.py                # Gestión de wallet
├── rpc.py                   # Cliente RPC Solana
├── jupiter.py               # Swaps Jupiter
├── transaction.py           # Transacciones
├── logger.py                # Logging
├── run.sh                   # Menú interactivo
├── .env.example             # Template configuración
├── requirements.txt         # Dependencias
└── TERMUX.md               # Esta guía
```

---

## Comandos Rápidos de Referencia

```bash
# Help
python solana_bot_complete.py --help

# Backtest
python solana_bot_complete.py backtest --sesiones 1000

# Simulación
DRY_RUN=true python solana_bot_complete.py run

# Trading real (⚠️)
python solana_bot_complete.py run --real

# Verificación
python solana_bot_complete.py verify --full

# Menú interactivo
./run.sh
```

---

## Recursos Adicionales

- **Documentación DexScreener:** https://docs.dexscreener.com/
- **API Solana:** https://docs.solana.com/
- **Jupiter Exchange:** https://jup.ag/
