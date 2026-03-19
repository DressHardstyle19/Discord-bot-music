# Discord Music Bot

Bot de Discord para reproducir música de YouTube en canales de voz.

## Requisitos

- Python 3.11+
- FFmpeg instalado en el sistema
- Token de bot de Discord

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/tu-repo.git
cd tu-repo
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura el token:
```bash
cp .env.example .env
# Edita .env y agrega tu DISCORD_TOKEN
```

4. Instala FFmpeg:
- **Ubuntu/Debian:** `sudo apt install ffmpeg`
- **CentOS/RHEL:** `sudo yum install ffmpeg`
- **Windows:** Descarga desde https://ffmpeg.org/download.html

## Ejecución

```bash
python main.py
```

## Con Docker

```bash
docker build -t discord-music-bot .
docker run -e DISCORD_TOKEN=tu_token discord-music-bot
```

## Comandos

| Comando | Descripción |
|---------|-------------|
| `!play <canción>` | Reproduce una canción (nombre o URL de YouTube) |
| `!pause` | Pausa la música |
| `!resume` | Reanuda la música |
| `!stop` | Detiene y desconecta el bot |
| `!skip` | Salta la canción actual |
| `!volume <0-100>` | Ajusta el volumen |
| `!queue` | Muestra la lista de reproducción |
| `!nowplaying` | Muestra la canción actual |
| `!clear` | Limpia la cola |
| `!leave` | Desconecta el bot |

## Permisos requeridos en Discord

El bot necesita los siguientes permisos en tu servidor:
- `Read Messages / View Channels`
- `Send Messages`
- `Connect` (canales de voz)
- `Speak` (canales de voz)
- `Use Voice Activity`

## Hosting 24/7

### Railway (recomendado, gratis)
1. Sube el código a GitHub
2. Ve a [railway.app](https://railway.app)
3. Crea un nuevo proyecto desde tu repo de GitHub
4. Agrega la variable de entorno `DISCORD_TOKEN`
5. Railway detectará el `Procfile` y correrá el bot automáticamente

### VPS (Ubuntu)
```bash
# Instala dependencias
sudo apt update && sudo apt install python3.11 ffmpeg -y
pip install -r requirements.txt

# Corre el bot en segundo plano con screen
screen -S discord-bot
python main.py
# Presiona Ctrl+A, D para dejar el proceso corriendo
```
