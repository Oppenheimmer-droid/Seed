# 📖 Guía de Uso del Menú Interactivo

## Solana Memecoin Bot - Configuración mediante Menú

---

## 🚀 Inicio Rápido

### Desde Terminal (Termux/Android)

```bash
# Opción 1: Usando módulo Python
python -m solana_bot.menu.interactive

# Opción 2: Ejecutando script directamente
python solana_bot/menu/interactive.py
```

### Desde Computadora

```bash
# Instalar dependencias
pip install aiohttp httpx beautifulsoup4 python-dotenv

# Ejecutar menú
python -m solana_bot.menu.interactive
```

---

## 📋 Menú Principal

```
╔═══════════════════════════════════════════════════════════╗
║  🤖 SOLANA MEMEBOT — MENÚ DE CONFIGURACIÓN              ║
╠═══════════════════════════════════════════════════════════╣
║  1. Gestionar Watchlist (añadir/eliminar tokens)         ║
║  2. Importar tokens desde DexScreener                     ║
║  3. Configurar filtros cuantitativos                     ║
║  4. Priorizar fuente de datos                            ║
║  5. Ver estado actual de configuración                   ║
║  6. Guardar y salir                                      ║
║  7. Salir sin guardar                                    ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 📖 Opción 1: Gestionar Watchlist

La **watchlist** es la lista de tokens que deseas seguir y analizar.

### Agregar Tokens Manualmente

```
Menú → 1 → 1 → Ingresar dirección → ENTER
```

**Ejemplo:**
```
  Dirección del token Solana: 7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr
  ✅ Token agregado: 7GCihgDB8fe6KNjn2...
```

### Eliminar Tokens

```
Menú → 1 → 2 → Ingresar número → ENTER
```

**Ejemplo:**
```
  Número del token a eliminar: 3
  ✅ Token eliminado: Addr3...
```

### Limpiar Toda la Watchlist

```
Menú → 1 → 3 → Confirmar (s/n): s
```

⚠️ **Advertencia:** Esto eliminará TODOS los tokens de la lista.

---

## 📖 Opción 2: Importar desde DexScreener

Esta opción permite buscar y agregar tokens directamente desde DexScreener.

### 2.1. Buscar por Nombre/Símbolo

```
Menú → 2 → 1 → Término de búsqueda: DOGE
```

**Resultado:**
```
  #  W Símbolo  Precio         Liquidez    DEX
  ─────────────────────────────────────────────────
  1  ✓ BONK    $0.00001234    $500,000    raydium
  2    WIF     $0.001234       $1,200,000  raydium
  3    POPCAT  $0.00002345     $200,000    orca

  Seleccione números separados por coma: 1,2
  ✅ Agregados 2 tokens a watchlist
```

### 2.2. Ver Tokens Trending

```
Menú → 2 → 2
```

Esto obtiene los tokens más activos/volátiles en Solana actualmente.

**Resultado esperado:**
```
  #  W Símbolo  Precio         Liquidez    DEX
  ─────────────────────────────────────────────────
  1    MEME     $0.00012345    $150,000    raydium
  2    PEPE     $0.00002345    $80,000     orca
  ...
```

### 2.3. Info de Token Específico

```
Menú → 2 → 3 → Dirección: 7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr
```

**Resultado:**
```
  ═══════════════════════════════════════
    MEME
    Dirección: 7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr
  ═══════════════════════════════════════
    DEX:         raydium
    Precio USD:  $0.00012345000
    Liquidez:   $150,000.00
    Volumen 24h: $2,500,000.00
    Volumen 5m:  $50,000.00
    Age:         30 min
    Change 5m:   +2.50%
    Change 1h:   +5.20%
    Change 24h:  +10.30%
  ═══════════════════════════════════════

  ¿Agregar a watchlist? (s/N): s
  ✅ Agregado a watchlist
```

---

## 📖 Opción 3: Configurar Filtros Cuantitativos

Los filtros determinan qué tokens son elegibles para trading.

### Filtros Disponibles

| Filtro | Descripción | Valor Por Defecto |
|--------|-------------|-------------------|
| Min liquidez (USD) | Liquidez mínima en USD | $50,000 |
| Min volumen 5m (USD) | Volumen mínimo en 5 min | $10,000 |
| Edad máxima (min) | Tiempo máximo desde creación | 60 min |
| Min holders | Mínimo de holders | 100 |
| Max % top holder | Concentración máxima | 20% |
| DEXs permitidos | Lista blanca de DEXs | raydium, meteora, pump.fun |

### Modificar un Filtro

```
Menú → 3 → Seleccionar filtro → Nuevo valor → ENTER
```

**Ejemplo:**
```
  MODIFICAR: Min liquidez (USD)
  
  Nuevo valor (1000 - 10000000) [50000]: 75000
  
  ✅ Filtro actualizado: Min liquidez (USD)
```

### Editar DEX Whitelist

```
Menú → 3 → 6 → Editar lista de DEXs
```

**Selección:**
```
  DEXs comúnmente usados:
  [✓] 1. raydium
  [ ] 2. meteora
  [✓] 3. pump.fun
  [ ] 4. orca
  [ ] 5. fluxbeam

  Ingrese números separados por coma para togglear: 2,4
  ✅ DEXs actualizados: raydium, meteora, pump.fun, orca
```

### Restaurar Valores Por Defecto

```
Menú → 3 → 7 → ¿Restaurar filtros por defecto?: s
```

---

## 📖 Opción 4: Priorizar Fuente de Datos

Determina qué API usar para obtener datos de tokens.

### Opciones Disponibles

| Opción | Descripción | Pros | Contras |
|--------|-------------|------|---------|
| **Birdeye** | API oficial con más datos | Métricas históricas | Más lento |
| **DexScreener** | API rápida | Actualizado, rápido | Menos datos |
| **Híbrido** | Combina ambas | Mejor precisión | Más lento |

### Cambiar Prioridad

```
Menú → 4 → Seleccionar opción → ENTER
```

**Ejemplo:**
```
  Prioridad actual: BIRDEYE

  Opciones disponibles:
  ───────────────────────
  → birdeye
     • Usa solo Birdeye API para datos de tokens
     • Más datos históricos y métricas
     • Puede ser más lento

  Seleccione prioridad: 2 (dexscreener)
  
  ✅ Prioridad cambiada a: DEXSCREENER
```

---

## 📖 Opción 5: Ver Estado de Configuración

Muestra un resumen completo de toda la configuración actual.

```
Menú → 5
```

**Ejemplo de salida:**
```
  ═══════════════════════════════════════════════════════
    ESTADO DE CONFIGURACIÓN
  ═══════════════════════════════════════════════════════

  📊 DEXSCREENER:
  ─────────────────────
  Parámetro           Valor
  ─────────────────────────────────────────────────────
  Habilitado          Sí
  Prioridad           BIRDEYE
  Min liquidez USD    $50,000
  Min volumen 5m USD  $10,000
  Edad máxima         60 min
  Min holders         100
  Max top holder %    20.0%
  Tokens en watchlist 5
  DEXs activos        5

  🔄 LOOP DE TRADING:
  ─────────────────────
  Parámetro           Valor
  ─────────────────────────────────────────────────────
  Capital operativo   100.0 SOL
  Extracción/ciclo   15.0 SOL
  Stop de ciclo      -50.0 SOL

  📋 WATCHLIST (primeros 10):
  ─────────────────────
  #  Dirección
  ─────────────────────────────────────────────────────
  1  So1111111111111...
  2  EPjFWdd5AufqSSq...
  ...
```

---

## 📖 Opción 6: Guardar y Salir

Guarda todos los cambios y cierra el menú.

```
Menú → 6 → ¿Guardar cambios y salir?: s
```

**Resultado:**
```
  ═══════════════════════════════════════════════════════
    GUARDAR Y SALIR
  ═══════════════════════════════════════════════════════

  Resumen de cambios:
  ─────────────────────
  • Prioridad: BIRDEYE
  • Tokens en watchlist: 5
  • Min liquidez: $50,000
  • Min volumen 5m: $10,000

  ¿Guardar cambios y salir?: s
  ✅ Configuración guardada correctamente
  ℹ️ Archivos en: ~/.solana_memebot/
```

---

## 📖 Opción 7: Salir sin Guardar

Sale del menú sin guardar cambios.

```
Menú → 7
```

⚠️ **Advertencia:** Los cambios no guardados se perderán.

---

## 📁 Archivos de Configuración

Los archivos se guardan en `~/.solana_memebot/`:

| Archivo | Descripción |
|---------|-------------|
| `dex_config.json` | Configuración principal |
| `watchlist.json` | Lista de tokens seguidos |
| `trades.json` | Historial de trades |

### Ejemplo `dex_config.json`

```json
{
  "dex_screener": {
    "enabled": true,
    "priority": "birdeye",
    "min_liquidity_usd": 50000,
    "min_volume_5m_usd": 10000,
    "max_age_minutes": 60,
    "min_holders": 100,
    "max_top_holder_pct": 0.20,
    "dex_whitelist": ["raydium", "meteora", "pump.fun"],
    "watchlist": [
      "So11111111111111111111111111111111111111112",
      "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    ]
  },
  "loop": {
    "capital_operativo_base": 100.0,
    "extraccion_por_ciclo": 15.0,
    "stop_ciclo": -50.0
  }
}
```

---

## 🔧 Solución de Problemas

### Error: "No se encontró módulo"

```bash
# Asegúrate de estar en el directorio correcto
cd /ruta/al/proyecto/Seed
python -m solana_bot.menu.interactive
```

### Error: "httpx no está instalado"

```bash
pip install httpx aiohttp beautifulsoup4
```

### Error: "No se puede conectar a DexScreener"

- Verifica tu conexión a internet
- Intenta más tarde (posibles mantenimientos)
- Usa `--offline` para modo de prueba

### Menú se cierra inesperadamente

```bash
# Ejecutar con más información de debug
python -m solana_bot.menu.interactive --debug
```

---

## 💡 Tips de Uso

1. **Usa la watchlist** para seguir tokens específicos que conoces
2. **Importa desde DexScreener** para descubrir nuevos tokens trending
3. **Ajusta filtros** según tu tolerancia al riesgo:
   - Filtros altos = menos señales, más calidad
   - Filtros bajos = más señales, más ruido
4. **Prioriza Birdeye** si quieres datos históricos
5. **Prioriza DexScreener** si quieres velocidad
6. **Guarda siempre** antes de salir

---

## 📞 Soporte

Para reportar problemas o solicitar ayuda:
- GitHub Issues: [link]
- Discord: [link]

---

*Versión: 1.0.0 | Compatible con Python 3.13 | ARM64/Termux*
