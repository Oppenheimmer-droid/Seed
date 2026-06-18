# 🪄 Solana Memecoin Trading Bot - Termux Edition

## Versión 1.1.0 - Rama Risk

Bot de trading algorítmico para memecoins en Solana con estrategia martingala y filtros de seguridad. Diseñado para ejecutarse en **Termux (Android)**.

---

## ⚡ Instalación Rápida

### Una sola línea:

```bash
bash <(curl -sL https://git.io/seed-termux)
```

### O manual paso a paso:

```bash
# 1. Actualizar Termux
pkg update && pkg upgrade

# 2. Instalar Python y Git
pkg install -y python git

# 3. Clonar el repositorio
git clone -b release/termux-v1.1.0 https://github.com/Oppenheimmer-droid/Seed.git ~/Seed

# 4. Ejecutar instalador
cd ~/Seed
bash install_termux.sh
```

---

## 🚀 Uso

### Ejecutar Menú Interactivo

```bash
cd ~/Seed
python solana_bot/menu/interactive.py
```

### Ejecutar en Modo Loop Continuo

```bash
cd ~/Seed
bash run_termux.sh loop
```

### Verificar Conexión DexScreener

```bash
cd ~/Seed
python check_dexscreener.py
```

---

## 📱 Opciones del Menú

```
╔═══════════════════════════════════════════════════════════╗
║  🤖 SOLANA MEMEBOT — MENÚ DE CONFIGURACIÓN            ║
╠═══════════════════════════════════════════════════════════╣
║  1. Gestionar Watchlist (añadir/eliminar tokens)        ║
║  2. Importar tokens desde DexScreener                   ║
║  3. Configurar filtros cuantitativos                    ║
║  4. Priorizar fuente de datos                           ║
║  5. Ver estado actual de configuración                  ║
║  6. Guardar y salir                                    ║
║  7. Salir sin guardar                                  ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 📁 Estructura de Archivos

```
~/.solana_memebot/           ← Directorio de datos
├── dex_config.json         ← Configuración principal
├── watchlist.json          ← Tokens seguidos
└── trades.json            ← Historial de trades

~/Seed/                     ← Repositorio
├── solana_bot/
│   ├── clients/
│   │   └── dexscreener.py  ← Cliente DexScreener
│   ├── config/
│   │   ├── bot_config.py   ← Configuración
│   │   └── schema.json     ← Schema de validación
│   ├── menu/
│   │   ├── interactive.py ← Menú principal
│   │   ├── handlers.py     ← Manejadores
│   │   └── widgets.py      ← Utilidades UI
│   └── storage.py          ← Persistencia
├── install_termux.sh       ← Script de instalación
├── run_termux.sh          ← Script de ejecución
└── check_dexscreener.py  ← Verificación API
```

---

## 🔧 Configuración

### Filtros Disponibles

| Parámetro | Por defecto | Descripción |
|-----------|-------------|-------------|
| Min liquidez USD | $50,000 | Liquidez mínima del pool |
| Min volumen 5m | $10,000 | Volumen mínimo en 5 min |
| Edad máxima | 60 min | Tiempo máximo del token |
| Min holders | 100 | Mínimo de holders |
| Max top holder % | 20% | Concentración máxima |
| DEXs permitidos | raydium, meteora, pump.fun | Lista blanca |

### Fuentes de Datos

- **Birdeye**: API oficial, más datos históricos
- **DexScreener**: Más rápido, menos datos
- **Híbrido**: Combina ambas fuentes

---

## ⚠️ Importante

1. **NUNCA** uses `pip install --upgrade pip` en Termux - rompe el paquete
2. **SIEMPRE** usa `pkg install` para herramientas del sistema
3. Este bot es de **ALTO RIESGO** - trading de memecoins
4. Usa **siempre** modo dry-run primero para probar

---

## 🔄 Actualizar

```bash
cd ~/Seed
git pull
```

---

## 📦 Dependencias

- Python 3.10+
- httpx
- aiohttp
- beautifulsoup4
- python-dotenv

---

## ⚠️ Disclaimer

**ESTE SOFTWARE SE PROPORCIONA "TAL CUAL". EL TRADING DE CRIPTOMONEDAS IMPLICA RIESGOS SIGNIFICATIVOS. ÚSALO BAJO TU PROPIO RIESGO.**

---

## 📄 Licencia

MIT License
