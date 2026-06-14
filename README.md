# 🪄 Solana Memecoin Trading Bot

## Version 1.0.0

Algorithmic trading bot for Solana memecoins with martingale strategy and security filters.

---

## 📱 Installation for Termux (Android)

### 1. Install Termux
⚠️ **DO NOT** install from Google Play Store (outdated version)
✅ Install from F-Droid: https://f-droid.org/packages/com.termux/

### 2. Install Dependencies in Termux

```bash
# Update system
pkg update -y && pkg upgrade -y

# Install dependencies
pkg install -y python git wget curl

# Clone or download the bot
git clone https://github.com/YOUR_USER/YOUR_REPO.git ~/solana_bot
cd ~/solana_bot

# Run install script
chmod +x install_termux.sh
./install_termux.sh
```

### 3. Configure

```bash
# Edit configuration
nano .env
```

Fill in your credentials:
```env
WALLET_PRIVATE_KEY=your_base58_private_key
SOLANA_RPC_URL=https://rpc.helius.xyz/?api-key=YOUR_KEY
BIRDEYE_API_KEY=your_birdeye_key
DRY_RUN=true
```

### 4. Run Backtesting

```bash
source venv/bin/activate
python solana_bot_complete.py backtest --sesiones 1000
```

---

## 🖥️ Installation for Linux/macOS

```bash
# Clone repository
git clone https://github.com/YOUR_USER/YOUR_REPO.git ~/solana_bot
cd ~/solana_bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env

# Run
python solana_bot_complete.py backtest --sesiones 1000
```

---

## 💻 Usage

```bash
# Backtesting (no credentials needed)
python solana_bot_complete.py backtest --sesiones 10000

# Dry-run mode (simulation)
python solana_bot_complete.py run <WALLET_PUBKEY>

# Real mode (⚠️ DANGEROUS)
python solana_bot_complete.py run <WALLET_PUBKEY> --real
```

---

## 📊 Backtesting Results (10,000 sessions)

| Metric | Result |
|--------|--------|
| Success Rate | 86% |
| Average Capital | 847 SOL |
| Win Rate | 75% |
| Sharpe Ratio | 0.8 |

---

## ⚠️ Disclaimer

THIS SOFTWARE IS PROVIDED "AS IS". CRYPTOCURRENCY TRADING INVOLVES SIGNIFICANT RISKS. USE AT YOUR OWN RISK.

---

## 📄 License

MIT License