# 🚀 SOLANA AUTONOMOUS TRADING BOT - RISK MODE

## ⚠️ ADVERTENCIA EXTREMA

**ESTE BOT OPERA SIN FILTROS DE SEGURIDAD**

- Compra CUALQUIER token detectado
- No valida liquidez, holders, taxes ni edad del pool
- Puedes perder el 100% de tu inversión
- Úsalo SOLO con capital que puedas permitir perder

---

## 📋 Características

### ✅ Facultades Operativas

| Función | Descripción |
|---------|-------------|
| **Snipe automático** | Compra inmediata de tokens en pump |
| **Trading autónomo** | Opera 24/7 sin intervención |
| **Sin filtros** | Compra CUALQUIER token |
| **Integración Jupiter** | Swaps DEX via Jupiter API v6 |
| **Ed25519 puro** | Firma con Python puro (compatible Termux) |
| **RPC Solana** | Conexión directa a mainnet |

### 🔧 Comandos Disponibles

```bash
# Generar nueva wallet (solo para pruebas)
python solana_bot_risk.py run generate

# Trading automático - monitorea y opera en cualquier token detectado
python solana_bot_risk.py run <PRIVATE_KEY> --amount 0.1

# Snipe - compra inmediata de un token específico
python solana_bot_risk.py snipe <PRIVATE_KEY> <TOKEN_MINT> --amount 0.5

# Monitor - monitorea un token específico y opera en pumps
python solana_bot_risk.py monitor <PRIVATE_KEY> --token <TOKEN_MINT>
```

### ⚙️ Parámetros

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `--amount` | 0.1 SOL | Cantidad por operación |
| `--slippage` | 1000 BPS | Slippage (10%) |
| `--rpc` | Solana mainnet | RPC endpoint |

---

## 🔐 Seguridad

### Formatos de Private Key Soportados

- Base58 (88 caracteres típico)
- Raw 32 bytes

### Cómo Obtener tu Private Key

**PHANTOM WALLET:**
1. Abrir Phantom → Configuración → Exportar clave privada
2. O usar la frase semilla con: `solana-keygen recover`

**COMANDO:**
```bash
# Recuperar desde frase semilla
solana-keygen recover "phrase word1 word2..." -o keypair.json
```

---

## 📊 Lógica de Trading

```
┌─────────────────────────────────────────────┐
│           RISK MODE - SIN FILTROS            │
├─────────────────────────────────────────────┤
│                                              │
│  1. Detecta pump (>5% precio)               │
│           ↓                                   │
│  2. Compra INMEDIATO sin verificar:          │
│     - Liquidez                               │
│     - Holders                                 │
│     - Taxes                                  │
│     - Edad del pool                          │
│           ↓                                   │
│  3. Detecta dump (>10% precio)               │
│           ↓                                   │
│  4. Vende TODO                               │
│                                              │
└─────────────────────────────────────────────┘
```

---

## 🔧 Instalación

```bash
# Dependencias (mínimas - solo aiohttp)
pip install aiohttp

# O desde requirements
pip install -r requirements.txt
```

---

## 📝 Ejemplo de Uso Completo

```bash
# 1. Monitorear BONK y hacer trading automático
python solana_bot_risk.py run 4jNXt7ZFV..." --amount 0.05 --slippage 1500

# 2. Snipear un nuevo token inmediatamente
python solana_bot_risk.py snipe 4jNXt7ZFV... DezXAZ8z7PnrnRJjz3wXBoRgixCa6jnB7 0.25

# 3. Monitorear un token específico
python solana_bot_risk.py monitor 4jNXt7ZFV... --token DezXAZ8z7PnrnRJjz3wXBoRgixCa6jnB7 --amount 0.1
```

---

## ⚡ Requisitos

- Python 3.8+
- Conexión a internet
- Fondos en wallet Solana
- aiohttp

---

## 📄 Licencia

**USO BAJO TU PROPIO RIESGO.** Este bot no garantiza ganancias. El trading de criptomonedas implica riesgo significativo de pérdida.

---

*Creado para la rama `risk` - Trading puro sin restricciones*
