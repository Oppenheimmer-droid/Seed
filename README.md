# 🤖 SOLANA TRADING BOT - 100% TERMUX COMPATIBLE

<div align="center">

![Solana](https://img.shields.io/badge/Solana-000000?style=for-the-badge&logo=solana)
![Python](https://img.shields.io/badge/Python-3.13+-yellow?style=for-the-badge&logo=python)
![Android](https://img.shields.io/badge/Android-TERMUX-green?style=for-the-badge&logo=android)
![License](https://img.shields.io/badge/License-MIT-red?style=for-the-badge)

**Bot de trading autónomo para Solana - Sin dependencias nativas, 100% Python puro**

</div>

---

## ⚠️ ADVERTENCIA

**ESTE SOFTWARE IMPLICA RIESGOS SIGNIFICATIVOS.**
- Puede haber pérdidas parciales o totales del capital
- Úsalo SIEMPRE primero en modo dry-run
- No nos hacemos responsables de pérdidas financieras

---

## 🚀 CARACTERÍSTICAS PRINCIPALES

### ✅ Facultades Operativas (Todas Funcionales)

| Módulo | Descripción | Termux |
|--------|-------------|--------|
| **Ed25519 Puro** | Criptografía sin extensiones nativas | ✅ |
| **Base58 Inline** | Codificación/decodificación built-in | ✅ |
| **Wallet Management** | Generación, importación, firma | ✅ |
| **RPC Solana** | Cliente async para mainnet | ✅ |
| **Jupiter Swap API v6** | Swaps DEX reales | ✅ |
| **DexScreener** | Datos de tokens (precio, liquidez) | ✅ |
| **Trading Engine** | Martingala, snipe, auto-trade | ✅ |
| **Backtesting** | Simulación de estrategias | ✅ |

---

## 📁 ESTRUCTURA DEL PROYECTO

```
Seed/
├── solana_bot_risk.py     # 🤖 Bot autónomo SIN filtros (PRINCIPAL)
├── solana_bot_complete.py # Bot con filtros de seguridad
├── solana_bot_alpha.py    # Alpha con DexScreener
├── solana_bot_beta.py     # Beta con Birdeye
├── crypto.py              # Ed25519 via cryptography
├── ed25519_pure.py        # Ed25519 100% Python
├── wallet.py              # Clase SolanaWallet
├── rpc.py                 # Cliente RPC async
├── transaction.py         # Constructor de TX
├── jupiter.py             # Integración Jupiter
├── logger.py              # Logging optimizado
├── requirements.txt       # Dependencias
├── setup_termux.sh        # Instalación Termux
├── run.sh                 # Ejecutar bot principal
└── run_risk.sh            # Ejecutar modo risk
```

---

## 🔧 INSTALACIÓN EN TERMUX

```bash
# 1. Actualizar Termux
pkg update && pkg upgrade -y

# 2. Instalar Python
pkg install python -y

# 3. Instalar dependencias
pip install aiohttp

# 4. Clonar repositorio
cd ~ && git clone https://github.com/Oppenheimmer-droid/Seed.git
cd Seed

# 5. O usar el script automático
bash setup_termux.sh
```

---

## 🎮 MODOS DE OPERACIÓN

### 1️⃣ RISK MODE (Recomendado para producción)

**SIN FILTROS DE SEGURIDAD** - Trading agresivo y autónomo.

```bash
# Trading automático - opera con CUALQUIER token detectado
python solana_bot_risk.py run <PRIVATE_KEY> --amount 0.1

# Snipe inmediato
python solana_bot_risk.py snipe <PRIVATE_KEY> <TOKEN_MINT> --amount 0.5

# Monitor - observa y opera en un token específico
python solana_bot_risk.py monitor <PRIVATE_KEY> --token <TOKEN_MINT>

# Generar wallet nueva
python solana_bot_risk.py run generate
```

### 2️⃣ CON FILTROS (Conservador)

```bash
# Backtest (simulación)
python solana_bot_complete.py backtest --sesiones 10000

# Dry-run
python solana_bot_complete.py dryrun <WALLET_PUBKEY>

# Real con filtros
python solana_bot_complete.py run <WALLET_PUBKEY> --real
```

### 3️⃣ TEST API

```bash
python solana_bot_alpha.py test-api
```

---

## 📊 CAPACIDADES DE TRADING

### Configuración Riesgo/Conservador

| Parámetro | Risk Mode | Con Filtros |
|-----------|-----------|-------------|
| Liquidez mínima | ❌ Sin filtro | ✅ 10 SOL |
| Holders mínimos | ❌ Sin filtro | ✅ 100 |
| Pool age mínimo | ❌ Sin filtro | ✅ 120s |
| Top holder % | ❌ Sin filtro | ✅ 20% |
| Sell tax máximo | ❌ Sin filtro | ✅ 10% |
| Slippage default | 10% (1000 bps) | 3-5% |

### Estrategias Implementadas

1. **Martingala Alcista**: Múltiples entradas por token
2. **Snipe Automático**: Compra en pumps detectados
3. **Sell en Dump**: Venta automática en caídas
4. **Backtesting**: Simulación con 10,000+ sesiones

---

## 🔐 FUNCIONES CRIPTOGRÁFICAS

### Ed25519 - Implementaciones

| Implementación | Uso | Termux |
|----------------|-----|--------|
| `crypto.py` | cryptography library | ✅ |
| `ed25519_pure.py` | 100% Python (fallback) | ✅ |
| Inline en wallet.py | Base58 + Ed25519 | ✅ |

### Formatos de Private Key Soportados

- **Base58** (~88 caracteres)
- **Raw 32 bytes**
- **Phantom 64 bytes** (seed + pubkey)

---

## 🔌 APIs INTEGRADAS

| API | Endpoint | Propósito |
|-----|----------|-----------|
| **Jupiter v6** | quote-api.jup.ag/v6 | Swaps DEX |
| **DexScreener** | api.dexscreener.com | Precio, liquidez, volumen |
| **Solana RPC** | api.mainnet-beta.solana.com | TX, balances, blockhash |

---

## 📱 COMPATIBILIDAD

| Entorno | Estado |
|---------|--------|
| Python 3.8+ | ✅ |
| Python 3.13 | ✅ |
| Termux (Android ARM64) | ✅ |
| Linux | ✅ |
| Sin Rust/C extensions | ✅ |
| Sin solders/PyNaCl | ✅ |

---

## 🛠️ DEPENDENCIAS

```txt
# requirements.txt
aiohttp>=3.8.0
# cryptography>=42.0.0  # Opcional - usa fallback puro si no disponible
```

**Instalación mínima para Termux:**
```bash
pip install aiohttp
```

---

## 📖 GUÍA RÁPIDA

### 1. Obtener tu Private Key

**Phantom Wallet:**
1. Abrir Phantom → Configuración → Exportar clave privada

**Desde frase semilla:**
```bash
pkg install solana-toolbox
solana-keygen recover "word1 word2..." -o keypair.json
```

### 2. Ejecutar en Dry-Run (Prueba)

```bash
python solana_bot_risk.py run <TU_PRIVATE_KEY> --amount 0.01
```

### 3. Monitorear un Token

```bash
python solana_bot_risk.py monitor <PRIVATE_KEY> --token <TOKEN_MINT>
```

### 4. Snipe un Token

```bash
python solana_bot_risk.py snipe <PRIVATE_KEY> <TOKEN_MINT> --amount 0.1
```

---

## 📊 LÓGICA DE TRADING

### Risk Mode (Sin Filtros)

```
┌─────────────────────────────────────────────┐
│           RISK MODE - SIN FILTROS            │
├─────────────────────────────────────────────┤
│                                              │
│  1. Detecta pump (>5% precio)               │
│           ↓                                   │
│  2. Compra INMEDIATO sin verificar:        │
│     - Liquidez ❌                            │
│     - Holders ❌                             │
│     - Taxes ❌                               │
│     - Edad del pool ❌                       │
│           ↓                                   │
│  3. Detecta dump (>10% precio)              │
│           ↓                                   │
│  4. Vende TODO                               │
│                                              │
└─────────────────────────────────────────────┘
```

### Modo Conservador (Con Filtros)

```
┌─────────────────────────────────────────────┐
│           CONSERVADOR - CON FILTROS          │
├─────────────────────────────────────────────┤
│                                              │
│  1. Detecta pump >1%                        │
│           ↓                                   │
│  2. Verifica:                               │
│     - Liquidez > 10 SOL ✅                   │
│     - Holders > 100 ✅                       │
│     - Top holder < 20% ✅                    │
│     - Sell tax < 10% ✅                      │
│           ↓                                   │
│  3. Martingala en caidas                    │
│           ↓                                   │
│  4. Vende en ATH o stop-loss                │
│                                              │
└─────────────────────────────────────────────┘
```

---

## 🔧 CONFIGURACIÓN

### Variables de Entorno (Opcional)

```bash
export WALLET_PRIVATE_KEY="tu_private_key"
export SOLANA_RPC_URL="https://api.mainnet-beta.solana.com"
export DRY_RUN="true"
```

### Parámetros CLI

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `--amount` | 0.1 SOL | Cantidad por trade |
| `--slippage` | 1000 BPS | Slippage (10%) |
| `--rpc` | mainnet | RPC endpoint |

---

## 📝 CHANGELOG

### v2.0.0 (Rama Principal)
- ✅ Unificación de todas las ramas
- ✅ Bot Risk Mode autonomous
- ✅ Base58 inline (sin dependencias)
- ✅ Ed25519 puro 100% Python
- ✅ Compatibilidad Termux total

### v1.0.0
- Bot básico con filtros
- Integración Jupiter
- Backtesting

---

## ⚠️ DISCLAIMER

**ESTE SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍAS DE NINGÚN TIPO.**
- El trading de criptomonedas implica alto riesgo
- Puedes perder la totalidad de tu inversión
- No nos hacemos responsables por pérdidas
- Úsalo bajo tu propio riesgo y discreción

---

## 📄 LICENCIA

MIT License - Ver archivo LICENSE

---

<div align="center">

**Hecho con ❤️ para la comunidad Solana**

*Compatible 100% con Termux - Sin dependencias nativas*

</div>
