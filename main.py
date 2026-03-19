import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import bot

if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("ERROR: La variable de entorno DISCORD_TOKEN no esta configurada.")
        print("Crea un archivo .env con: DISCORD_TOKEN=tu_token_aqui")
        sys.exit(1)
    bot.run(token)
