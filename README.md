# Bitácora Bot

Bot de Telegram para el registro de trabajos de viña, con generación de informes en PDF y análisis asistido por IA (DeepSeek). Pensado para llevar la bitácora de tareas del viñedo y producir reportes ordenados.

**Tecnología:** Python + python-telegram-bot. Genera PDFs con ReportLab y consulta a DeepSeek para analizar las tareas registradas.

---

## Requisitos del servidor

- **Sistema:** Ubuntu / Debian (probado en VPS)
- **Python:** versión 3.10 o superior
- Un **token de bot de Telegram** (se obtiene de @BotFather)
- Una **API key de DeepSeek** (de https://platform.deepseek.com)

---

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
cd ~
git clone https://github.com/Agro-bot2026/bitacora-bot.git bitacora_bot
cd bitacora_bot
```

### 2. Instalar Python y el entorno virtual (si el VPS es nuevo)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 3. Crear el entorno virtual e instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Esto instala:
- `python-telegram-bot` — conexión con Telegram
- `requests` — peticiones HTTP (a DeepSeek)
- `reportlab` — generación de PDFs
- `python-dotenv` — lectura del archivo `.env`
- `PyPDF2` — lectura de PDFs

### 4. Configurar las credenciales (¡el paso clave!)

El bot lee sus secretos de un archivo `.env` que **no está en el repositorio** por seguridad. Hay que crearlo a partir de la plantilla:

```bash
cp .env.example .env
nano .env
```

Completá los dos valores con los tuyos:

```
TELEGRAM_TOKEN=tu_token_real_de_telegram
DEEPSEEK_API_KEY=tu_api_key_real_de_deepseek
```

> Guardá en nano con `Ctrl+O`, Enter, y salí con `Ctrl+X`.

**¿De dónde saco cada uno?**
- **TELEGRAM_TOKEN:** escribile a [@BotFather](https://t.me/BotFather) en Telegram, comando `/newbot` (o `/token` si ya lo tenés creado).
- **DEEPSEEK_API_KEY:** desde tu cuenta en https://platform.deepseek.com → API keys.

- ---

## Arrancar el bot

```bash
source venv/bin/activate
python3 bot.py
```

Si todo está bien, muestra: `✅  Bitácora Bot iniciado`

> **Importante:** Telegram solo permite una instancia del bot corriendo a la vez. Si arrancás una segunda copia con el mismo token, da el error `Conflict: terminated by other getUpdates request`. Eso significa que el bot ya está corriendo en otro lado — cerrá la otra instancia primero.

### Dejarlo corriendo en segundo plano (recomendado en VPS)

Con tmux, para que siga activo aunque cierres la terminal:

```bash
tmux new-session -d -s bitacora "cd ~/bitacora_bot && source venv/bin/activate && python3 bot.py"
```

Ver los logs: `tmux attach -t bitacora`
Salir sin cortar: `Ctrl+B`, luego `D`

---

## Estructura del proyecto

```
bitacora_bot/
├── bot.py             # Bot principal (Telegram + PDF + DeepSeek)
├── requirements.txt   # Dependencias de Python
├── .env               # ⚠️ NO incluido - tus credenciales (crealo desde .env.example)
├── .env.example       # Plantilla de credenciales (sin secretos)
├── documentos/        # Leyes y modelos (Estatuto, Jubilación Vinícola, contrato)
├── bitacora.json      # ⚠️ NO incluido - registros de trabajo
└── perfiles.json      # ⚠️ NO incluido - datos de usuarios
```

---

## Archivos que NO vienen en el repo

Por seguridad y privacidad, estos quedan fuera de GitHub:

- **`.env`** — token de Telegram y API key de DeepSeek (crealo desde `.env.example`)
- **`bitacora.json`** — registros de trabajo (se genera solo al usar el bot)
- **`perfiles.json`** — datos de usuarios (se genera solo)
- **`venv/`** — entorno virtual (se regenera con `pip install -r requirements.txt`)
