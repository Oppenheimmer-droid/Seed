# 📱 Guía Completa: Solana Memecoin Trading Bot V0.3
## Instalación en Termux (Android) - Desde Cero Hasta Running (Trading Real)

---

## 🚀 ÍNDICE

1. [Requisitos Previos](#-requisitos-previos)
2. [Instalación Express (1 comando)](#-instalación-express-1-comando)
3. [Instalación Paso a Paso](#-instalación-paso-a-paso)
4. [Configuración](#-configuración)
5. [Ejecución](#-ejecución)
6. [Push a GitHub](#-push-a-github)
7. [Descarga Local](#-descarga-local)
8. [Solución de Problemas](#-solución-de-problemas)

---

## 📋 Requisitos Previos

### 1.1 Instalar Termux (Android)

⚠️ **IMPORTANTE**: NO instales Termux desde Google Play Store. La versión está desactualizada.

**Opción recomendada**: Instalar desde F-Droid
```
https://f-droid.org/packages/com.termux/
```

### 1.2 Configuración Inicial de Termux

Una vez instalado Termux, ejecuta estos comandos de configuración inicial:

```bash
# Actualizar repositorios
termux-setup-storage  # Solicitará permisos de almacenamiento

# Importante: actualizar inmediatamente
pkg update -y && pkg upgrade -y

# Instalar dependencias base
pkg install -y python git curl wget termux-services
```

### 1.3 Permisos Necesarios

```bash
# Otorgar permisos de almacenamiento (importante para guardar logs)
termux-setup-storage

# Verificar que los permisos funcionen
ls -la ~/storage/
```

---

## 🚀 Instalación Express (1 Comando)

### Opción A: Copia y Pega Este Comando Completo

```bash
pkg update -y && pkg upgrade -y && pkg install -y python git && cd ~ && rm -rf solana_bot 2>/dev/null; git clone https://github.com/Oppenheimmer-droid/Seed.git solana_bot && cd solana_bot && chmod +x setup_termux.sh && bash setup_termux.sh
```

### Opción B: Usando el Script de Instalación Rápida

```bash
# Paso 1: Clonar el repositorio
pkg update -y && pkg upgrade -y && pkg install -y python git
cd ~
git clone https://github.com/Oppenheimmer-droid/Seed.git solana_bot
cd solana_bot

# Paso 2: Ejecutar instalación automática
chmod +x setup_termux.sh
bash setup_termux.sh
```

---

## 📦 Instalación Paso a Paso

### Paso 1: Preparar el Entorno

```bash
# Actualizar Termux completamente
pkg update -y && pkg upgrade -y

# Instalar todas las dependencias necesarias
pkg install -y \
    python \
    git \
    curl \
    wget \
    openssl \
    libffi \
    clang \
    make \
    rust
```

### Paso 2: Clonar el Repositorio

```bash
# Ir al directorio home
cd ~

# Eliminar versión anterior si existe (opcional)
rm -rf solana_bot

# Clonar el repositorio
git clone https://github.com/Oppenheimmer-droid/Seed.git solana_bot

# Entrar al directorio
cd solana_bot

# Verificar archivos
ls -la
```

Deberías ver:
```
solana_bot_complete.py
setup_termux.sh
install_termux.sh
run.sh
requirements.txt
README.md
```

### Paso 3: Ejecutar el Script de Instalación

```bash
# Dar permisos de ejecución
chmod +x setup_termux.sh

# Ejecutar instalación
bash setup_termux.sh
```

El script realizará automáticamente:
- ✅ Crear entorno virtual Python (venv)
- ✅ Instalar dependencias de Python
- ✅ Crear archivo .env con configuración
- ✅ Ejecutar configuración interactiva (opcional)

### Paso 4: Verificación de Instalación

```bash
# Verificar que el entorno virtual existe
ls -la venv/

# Verificar que pip funciona
source venv/bin/activate
pip --version

# Verificar dependencias instaladas
pip list | grep -E "dotenv|colorlog|aiohttp"
```

Deberías ver:
```
python-dotenv    X.X.X
colorlog         X.X.X
aiohttp          X.X.X
aiohttp-socks    X.X.X
```

---

## ⚙️ Configuración

### 4.1 Configuración Automática (Recomendada)

Durante la ejecución de `setup_termux.sh`, el script preguntará interactivamente:

```
¿Deseas configurar ahora? (y/n)
```

Responde `y` para configurar interactivamente.

### 4.2 Configuración Manual

```bash
# Abrir archivo de configuración
nano .env
```

### 4.3 Variables de Configuración

Edita el archivo `.env` con tus credenciales:

```env
# ============================================
# Solana Memecoin Trading Bot - Configuración
# ============================================

# RPC de Solana (endpoint para blockchain)
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# RPC alternativo (recomendado para producción)
# SOLANA_RPC_URL=https://rpc.helius.xyz/?api-key=TU_API_KEY

# API de Birdeye (opcional, para datos extendidos)
BIRDEYE_API_KEY=tu_birdeye_api_key_aqui

# Clave privada de wallet (⚠️ MANTENER EN SECRETO)
# Usa una wallet DEDICADA para trading
WALLET_PRIVATE_KEY=tu_clave_privada_en_base58

# Modo de operación
# true = simulación (SEGURO - recomendado)
# false = trading real (PELIGRO)
DRY_RUN=true
```

### 4.4 Donde Obtener las Credenciales

#### Solana RPC:
- **Gratuito**: `https://api.mainnet-beta.solana.com` (rate limited)
- **Helius** (recomendado): https://dashboard.helius.xyz/ (free tier disponible)
- **QuickNode**: https://quicknode.com/ (free tier disponible)

#### Birdeye API:
- Registro gratis: https://birdeye.so/
- Dashboard: https://birdeye.so/dashboard

#### Wallet Private Key:
```bash
# En Phantom Wallet:
# 1. Abre la wallet
# 2. Click en el icono de ajustes (⚙️)
# 3. Selecciona "Export Private Key"
# 4. Ingresa tu contraseña
# 5. Copia la clave (formato base58)
```

⚠️ **ADVERTENCIAS DE SEGURIDAD**:
- NUNCA compartas tu clave privada
- Usa una wallet DEDICADA para trading
- Empieza SIEMPRE con `DRY_RUN=true`
- Haz backup de tu clave en un lugar seguro

---

## 🎯 Ejecución

### 5.1 Activar el Entorno Virtual

```bash
# Activar entorno virtual
source venv/bin/activate

# Verificar (deberías ver (venv) al inicio)
which python
python --version
```

### 5.2 Modos de Ejecución

#### Modo 1: Backtesting (Simulación Histórica)
```bash
# 100 sesiones de prueba
python solana_bot_complete.py backtest --sesiones 100

# 1000 sesiones (más preciso)
python solana_bot_complete.py backtest --sesiones 1000

# 10000 sesiones (completo)
python solana_bot_complete.py backtest --sesiones 10000
```

**No necesita credenciales** - Perfecto para probar.

#### Modo 2: Dry-Run (Simulación en Tiempo Real)
```bash
# Con wallet pública
python solana_bot_complete.py dryrun <WALLET_PUBLICA>

# O usando el script
./run.sh dryrun <WALLET_PUBLICA>

# Ejemplo:
./run.sh dryrun 7xK21...abc123
```

**No envía transacciones reales** - Solo simula.

#### Modo 3: Run (Trading Real) ⚠️
```bash
# ¡PELIGRO! Solo con DRY_RUN=false en .env
python solana_bot_complete.py run <WALLET_PUBLICA> --real

# O con el script
./run.sh run <WALLET_PUBLICA> --real
```

⚠️ **SOLO DESPUÉS DE PROBAR EXTENSAMENTE EN DRY-RUN**

### 5.3 Usando el Script run.sh

```bash
# Asegúrate de que el script es ejecutable
chmod +x run.sh

# Ejecutar con diferentes modos
./run.sh backtest --sesiones 1000    # Backtesting
./run.sh dryrun <WALLET>              # Simulación
./run.sh run <WALLET> --real          # Real (⚠️)
```

### 5.4 Ver Logs

```bash
# Ver logs en tiempo real
tail -f trading_bot.log

# Ver últimos 50 líneas
tail -50 trading_bot.log

# Buscar errores
grep -i error trading_bot.log

# Ver trades ejecutados
cat trades.json
```

---

## 🔄 Push a GitHub

### 6.1 Configurar Git (Primera vez)

```bash
cd ~/solana_bot

# Configurar identidad
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"

# Configurar GitHub token (para push)
git remote set-url origin https://GITHUB_TOKEN@github.com/Oppenheimmer-droid/Seed.git
```

### 6.2 Actualizar y Subir Cambios

```bash
# 1. Ver estado
git status

# 2. Agregar archivos modificados
git add .

# 3. Ver qué cambió
git diff --staged

# 4. Commit con mensaje
git commit -m "release: v0.2 - Termux complete setup"

# 5. Push a GitHub
git push origin main
```

### 6.3 Push Rápido (Si ya está configurado)

```bash
cd ~/solana_bot
git add .
git commit -m "update: $(date '+%Y-%m-%d %H:%M')"
git push origin main
```

### 6.4 Manejo de Conflictos

```bash
# Descartar cambios locales (⚠️ cuidado)
git checkout -- .

# O hacer pull primero
git pull origin main --rebase
```

---

## 💾 Descarga Local (Actualizar V0.2)

### Opción 1: Pull desde GitHub

```bash
cd ~/solana_bot

# Hacer backup de tu configuración
cp .env .env.backup

# Actualizar desde remote
git pull origin main

# Restaurar configuración
cp .env.backup .env  # o manualmente
```

### Opción 2: Descargar Release

```bash
cd ~

# Descargar release V0.2
wget https://github.com/Oppenheimmer-droid/Seed/releases/download/v0.2/solana_bot_v0.2.tar.gz

# Extraer
tar -xzf solana_bot_v0.2.tar.gz

# Entrar al directorio
cd solana_bot_v0.2

# Hacer backup de .env anterior si existe
cp ~/solana_bot/.env ~/solana_bot/.env.backup 2>/dev/null || true

# Instalar/actualizar
bash setup_termux.sh
```

### Opción 3: Clonar de Nuevo (Limpio)

```bash
cd ~

# Backup de configuración actual
cp solana_bot/.env solana_bot/.env.backup 2>/dev/null || true

# Backup de logs y trades
cp solana_bot/trading_bot.log solana_bot/trades.json ~/ 2>/dev/null || true

# Eliminar versión anterior
rm -rf solana_bot

# Clonar de nuevo
git clone https://github.com/Oppenheimmer-droid/Seed.git solana_bot

# Restaurar configuración
cp .env.backup solana_bot/.env 2>/dev/null || echo "Edita .env manualmente"

# Reinstalar
cd solana_bot
bash setup_termux.sh
```

---

## 🔧 Solución de Problemas

### Problema 1: Error de Permisos

```bash
# Solución
chmod +x *.sh *.py
chmod 700 .env  # Proteger archivo con claves
```

### Problema 2: Python no encontrado

```bash
# Reinstalar Python
pkg uninstall python
pkg install python

# Verificar
python --version
```

### Problema 3: Error con pip (pydantic-core)

Si ves errores como `Failed building wheel for pydantic-core`:

```bash
# Instalar herramientas de compilación
pkg install -y rust clang make

# Reinstalar con force
source venv/bin/activate
pip install --force-reinstall --no-cache-dir pydantic pydantic-settings
```

O simplemente usa la versión sin pydantic (ya incluida en V0.2):
```bash
pip install python-dotenv colorlog aiohttp aiohttp-socks
```

### Problema 4: Error de SSL/Certificate

```bash
# Actualizar certificados
pkg install -y ca-certificates
pip install --upgrade certifi

# Reinstalar dependencias de SSL
pip install --upgrade --force-reinstall urllib3 requests
```

### Problema 5: Entorno Virtual Corrupto

```bash
# Eliminar y recrear
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Problema 6: Git Authentication Error

```bash
# Usar token en lugar de contraseña
git remote set-url origin https://GITHUB_TOKEN@github.com/Oppenheimmer-droid/Seed.git

# O usar SSH
git remote set-url origin git@github.com:Oppenheimmer-droid/Seed.git
```

### Problema 7: Termux Storage Permission Denied

```bash
# Reconfigurar storage
rm -rf ~/storage
termux-setup-storage

# Verificar
ls ~/storage/
```

---

## 📊 Resumen de Comandos Rápidos

### Instalación Nueva
```bash
pkg update && pkg install -y python git && cd ~ && rm -rf solana_bot && git clone https://github.com/Oppenheimmer-droid/Seed.git && cd solana_bot && bash setup_termux.sh
```

### Ejecutar Backtesting
```bash
cd ~/solana_bot && source venv/bin/activate && python solana_bot_complete.py backtest --sesiones 1000
```

### Ejecutar Dry-Run
```bash
cd ~/solana_bot && source venv/bin/activate && ./run.sh dryrun <TU_WALLET>
```

### Actualizar
```bash
cd ~/solana_bot && git pull origin main && source venv/bin/activate && pip install -r requirements.txt
```

### Ver Logs
```bash
cd ~/solana_bot && tail -f trading_bot.log
```

---

## 📞 Recursos Adicionales

- **Documentación del Bot**: Ver README.md
- **Reportar Issues**: GitHub Issues
- **Ayuda de Solana RPC**: https://docs.solana.com/
- **Termux Wiki**: https://wiki.termux.com/

---

## ⚠️ DISCLAIMER

**ESTE BOT IMPLICA RIESGOS SIGNIFICATIVOS.**

- El trading de criptomonedas puede resultar en pérdidas totales
- Los resultados pasados no garantizan resultados futuros
- Esta es una versión BETA - úsala bajo tu propio riesgo
- NUNCA inviertas más de lo que puedas permitirte perder
- Siempre haz backup de tu wallet

---

**Versión**: 0.2
**Última Actualización**: 2024
**Autor**: Oppenheimmer-droid
