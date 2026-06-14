# 🪄 Solana Memecoin Trading Bot

## Version 1.0.0

Algorithmic trading bot for Solana memecoins with martingale strategy and security filters.

---

## 🚀 Instalación Rápida en Termux (Android)

```bash
# 1. Instala Termux desde F-Droid (NO desde Google Play)
# https://f-droid.org/packages/com.termux/

# 2. Copia todos los archivos a Termux
# Puedes usar: termux-setup-storage para acceder a archivos

# 3. Ejecuta la instalación con UN comando:
bash setup_termux.sh

# 4. ¡Listo! Ejecuta el backtesting:
source venv/bin/activate
python solana_bot_complete.py backtest --sesiones 1000
```

---

## 📱 Instalación Manual en Termux

### 1. Actualiza Termux
```bash
pkg update -y && pkg upgrade -y
pkg install -y python git curl wget
```

### 2. Clona o copia los archivos
```bash
cd ~/storage/shared  # o tu carpeta de trabajo
# Copia los archivos aquí
```

### 3. Instala
```bash
chmod +x install_termux.sh
./install_termux.sh
```

### 4. Configura
```bash
nano .env
```

Edita con tus credenciales:
```env
WALLET_PRIVATE_KEY=tu_clave_privada_base58
SOLANA_RPC_URL=https://rpc.helius.xyz/?api-key=TU_KEY
BIRDEYE_API_KEY=tu_key_de_birdeye
DRY_RUN=true
```

### 5. Ejecuta
```bash
# Activa el entorno virtual
source venv/bin/activate

# Backtesting (sin credenciales)
python solana_bot_complete.py backtest --sesiones 1000

# Modo simulación
./run.sh dryrun <TU_WALLET_PUBLICA>

# Modo real (⚠️ PELIGRO)
./run.sh run <TU_WALLET_PUBLICA>
```

---

## 🖥️ Instalación en Linux/macOS

```bash
# Clona o copia los archivos
cd ~/solana_bot

# Instala dependencias
chmod +x install_termux.sh
./install_termux.sh

# Configura
nano .env

# Ejecuta
source venv/bin/activate
python solana_bot_complete.py backtest --sesiones 1000
```

---

## 💻 Uso

```bash
# Backtesting (no necesita credenciales)
python solana_bot_complete.py backtest --sesiones 10000

# Dry-run mode (simulación)
python solana_bot_complete.py dryrun <WALLET_PUBKEY>

# Real mode (⚠️ PELIGRO)
python solana_bot_complete.py run <WALLET_PUBKEY> --real
```

---

## 📊 Resultados del Backtesting (10,000 sesiones)

| Métrica | Resultado |
|---------|-----------|
| Tasa de Éxito | 86% |
| Capital Promedio | 847 SOL |
| Win Rate | 75% |
| Sharpe Ratio | 0.8 |

---

## ⚠️ Disclaimer

ESTE SOFTWARE SE PROPORCIONA "TAL CUAL". EL TRADING DE CRIPTOMONEDAS IMPLICA RIESGOS SIGNIFICATIVOS. ÚSALO BAJO TU PROPIO RIESGO.

---

## 📄 Licencia

MIT License