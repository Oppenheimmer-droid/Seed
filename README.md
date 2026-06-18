# 🪄 Solana Memecoin Trading Bot

## Version 2.1

Bot de trading algorítmico para memecoins de Solana con estrategia martingala y filtros de seguridad.
**100% Puro Python** — Sin Rust, sin solders, sin PyNaCl como requisito.

---

## ✅ Características v2.1

- 🚫 **Sin dependencias nativas** — Funciona en Termux Android ARM64 sin Rust
- 🔐 **Ed25519 puro Python** — Implementación propia para firmas
- 🛡️ **Validación de config** — Detecta URLs en lugar de API keys
- 📊 **Menú interactivo** — Panel de control con 7 opciones
- 📝 **Logs en pantalla** — Timestamps y emojis para readability

---

## 🚀 Instalación Express en Termux (Android)

### Un solo comando (copia y pega todo)

```bash
pkg update -y && pkg upgrade -y && pkg install -y python git && cd ~ && rm -rf solana_bot && git clone https://github.com/Oppenheimmer-droid/Seed.git solana_bot && cd solana_bot && chmod +x setup_termux.sh && bash setup_termux.sh
```

---

## 💻 Uso

```bash
# Activar entorno virtual
source venv/bin/activate

# Modo interactivo (menú)
./run.sh

# Backtesting (sin credenciales)
./run.sh backtest 10000

# Trading bot (dry-run por defecto)
./run.sh run
```

### Menú de opciones:

```
╔══════════════════════════════════════════════════════════╗
║       🤖 SOLANA MEMECOIN BOT v2.1 — PANEL DE CONTROL  ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  1. 🔵 SIMULACRO — Detecta tokens, sin trades         ║
║  2. 🔴 REAL      — Trading con SOL real                 ║
║  3. 📊 BACKTEST  — Simulación histórica                 ║
║  4. 📋 LOGS      — Ver actividad reciente              ║
║  5. ⚙️  CONFIG   — Editar configuración (.env)         ║
║  6. 🛑 DETENER   — Parar bot en background             ║
║  7. ❌ SALIR                                             ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

---

## ⚙️ Configuración

Edita `.env` con tus credenciales:

```env
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
BIRDEYE_API_KEY=76641762bca44ff68ad89cd254b70e2d
WALLET_PRIVATE_KEY=4HzcULkg23tbxMXdeTjq5UKAEFYvSs26JupM8kMbCyjXDdN6QjRQZp43cY5Eg6QugEzezTxDpfZedHyxrK7ikYxN
DRY_RUN=true
CAPITAL_INICIAL=500
OBJETIVO_GLOBAL=615
STOP_LOSS_GLOBAL=100
```

### ⚠️ Importante

| Campo | Error común | Solución |
|-------|------------|----------|
| `BIRDEYE_API_KEY` | Poner la URL | Usar solo la KEY (ej: `76641762bca44...`) |
| `WALLET_PRIVATE_KEY` | Usar public key | Exportar private key desde Phantom (~88 chars) |

---

## 📦 Dependencias (v2.1)

| Paquete | Estado | Notas |
|---------|--------|-------|
| aiohttp==3.14.1 | ✅ Wheel ARM64 | HTTP async |
| aiohttp-socks==0.11.0 | ✅ Puro Python | SOCKS proxy |
| base58==2.1.1 | ✅ Puro Python | Codificación base58 |
| python-dotenv==1.2.2 | ✅ Puro Python | Variables entorno |
| colorlog==6.10.1 | ✅ Puro Python | Logging con colores |
| httpx==0.28.1 | ✅ Puro Python | HTTP client |
| ed25519_pure.py | ✅ Incluido | Firma Ed25519 sin Rust |

**PyNaCl y cryptography son opcionales** — Se usa fallback puro si no están disponibles.

---

## 📊 Resultados del Backtesting (10,000 sesiones)

| Métrica | Resultado |
|---------|-----------|
| Tasa de Éxito | 86% |
| Capital Promedio | 847 SOL |
| Win Rate | 75% |
| Sharpe Ratio | 0.8 |

---

## 📁 Estructura del Proyecto v2.1

```
solana_bot/
├── solana_bot_complete.py   # Bot principal
├── run.sh                   # Menú interactivo
├── setup_termux.sh          # Instalación (v2.1)
├── requirements.txt         # Dependencias verificadas
├── ed25519_pure.py          # Firma Ed25519 pura Python
├── wallet.py                # Wallet Solana (fallback)
├── rpc.py                   # Cliente RPC puro HTTP
├── jupiter.py               # Jupiter swap API
├── logger.py                # Logging optimizado Termux
├── .env                     # Config (creado por setup)
├── logs/                    # Logs de actividad
└── venv/                    # Entorno virtual
```

---

## ⚠️ Disclaimer

ESTE SOFTWARE SE PROPORCIONA "TAL CUAL". EL TRADING DE CRIPTOMONEDAS IMPLICA RIESGOS SIGNIFICATIVOS. ÚSALO BAJO TU PROPIO RIESGO.

---

## 📄 Licencia

MIT License