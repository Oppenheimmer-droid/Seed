# 🪄 Solana Memecoin Trading Bot

## Version 0.3

Bot de trading algorítmico para memecoins de Solana con estrategia martingala y filtros de seguridad. **Totalmente funcional para Termux (Android)**.

### V0.3 - Trading Real Activo
- ✅ `simulacro.py` - Simulación visual completa con UI mejorada
- ✅ `trading_real.py` - Trading real con Jupiter API
- ✅ Validación de private key integrada
- ✅ Sin solders (compatible Python 3.13 ARM64)

---

## 🚀 Instalación Express en Termux (Android)

### Opción 1: Un solo comando (copia y pega todo)

```bash
pkg update -y && pkg upgrade -y && pkg install -y python git && cd ~ && rm -rf solana_bot && git clone https://github.com/Oppenheimmer-droid/Seed.git solana_bot && cd solana_bot && chmod +x setup_termux.sh && bash setup_termux.sh
```

### Opción 2: Paso a paso

```bash
# 1. Actualizar Termux
pkg update -y && pkg upgrade -y

# 2. Instalar dependencias
pkg install -y python git

# 3. Clonar el proyecto
cd ~
rm -rf solana_bot  # si ya existe
git clone https://github.com/Oppenheimmer-droid/Seed.git solana_bot
cd solana_bot

# 4. Instalar (esto instala todo automáticamente)
chmod +x setup_termux.sh
bash setup_termux.sh

# 5. Activar y usar
source venv/bin/activate
python solana_bot_complete.py backtest --sesiones 1000
```

---

## ⚙️ Si la instalación falla (Error de pydantic-core)

Si ves el error `Failed building wheel for pydantic-core`, ejecuta:

```bash
pkg install -y rust clang make
cd ~/solana_bot
source venv/bin/activate
pip install --force-reinstall pydantic pydantic-settings python-dotenv colorlog aiohttp
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
cd ~
git clone https://github.com/Oppenheimmer-droid/Seed.git solana_bot
cd solana_bot
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
./run.sh dryrun

# Modo real (⚠️ PELIGRO)
./run.sh run <TU_WALLET_PUBLICA> --real
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
# Activar entorno virtual
source venv/bin/activate

# Menú interactivo (recomendado)
./run.sh

# O directamente:
# Simulación visual (UI completa con barras de progreso)
python simulacro.py

# Trading real (requiere configuración previa)
python trading_real.py

# Backtesting histórico
python solana_bot_complete.py backtest --sesiones 10000

# Verificación del sistema
python solana_bot_complete.py verify --full
```

---

## 🔄 Gestión del Repositorio

```bash
# Actualizar desde GitHub
./download_release.sh update

# Subir cambios a GitHub
./git_manager.sh push "tu mensaje"

# Ver estado
./git_manager.sh status

# Backup de datos
./git_manager.sh backup

# Actualización completa (backup + pull + reinstall)
./git_manager.sh full-update
```

---

## 📱 Guía Completa Termux

Ver el archivo `termux.md` para instrucciones detalladas desde cero (instalación de Termux) hasta running.

---

## 📊 Resultados del Backtesting (10,000 sesiones)

| Métrica | Resultado |
|---------|-----------|
| Tasa de Éxito | 86% |
| Capital Promedio | 847 SOL |
| Win Rate | 75% |
| Sharpe Ratio | 0.8 |

---

## 📁 Estructura del Proyecto

```
solana_bot/
├── solana_bot_complete.py   # Bot principal (ejecutable)
├── setup_termux.sh          # Instalación rápida (1 comando)
├── install_termux.sh        # Instalación completa
├── run.sh                   # Ejecución rápida
├── git_manager.sh           # Gestión de Git (push/pull/backup)
├── download_release.sh      # Descargar/Actualizar releases
├── termux.md                # Guía completa Termux (desde cero)
├── requirements.txt         # Dependencias Python
├── .env.example             # Plantilla de configuración
├── .env                     # Tu configuración (creado por setup)
├── README.md                # Este archivo
└── venv/                    # Entorno virtual (creado por setup)
```

## 📌 Versión 0.2 - Novedades

- ✅ `termux.md` - Guía completa desde instalación de Termux hasta running
- ✅ `git_manager.sh` - Scripts para push, pull, backup y actualización
- ✅ `download_release.sh` - Descarga y actualización de releases
- ✅ Scripts mejorados con version V0.2
- ✅ Configuración interactiva mejorada
- ✅ Sin dependencia de pydantic (compatible con Python 3.13 de Termux)

---

## ⚠️ Disclaimer

ESTE SOFTWARE SE PROPORCIONA "TAL CUAL". EL TRADING DE CRIPTOMONEDAS IMPLICA RIESGOS SIGNIFICATIVOS. ÚSALO BAJO TU PROPIO RIESGO.

---

## 📄 Licencia

MIT License