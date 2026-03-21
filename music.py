import discord
import asyncio
import yt_dlp
import subprocess
import os
from collections import deque

# Headers de navegador real para evitar bloqueos de YouTube en IPs de nube
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "http_headers": BROWSER_HEADERS,
    "extractor_args": {"youtube": {"skip": ["dash", "hls"]}},
    "socket_timeout": 15,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn -ar 48000 -ac 2",
}


def find_and_load_opus():
    if discord.opus.is_loaded():
        return True

    # Rutas estandar de Linux (Ubuntu/Debian - Railway, VPS)
    standard_paths = [
        "libopus.so.0",
        "libopus.so",
        "/usr/lib/x86_64-linux-gnu/libopus.so.0",
        "/usr/lib/aarch64-linux-gnu/libopus.so.0",
        "/usr/lib/libopus.so.0",
        "/usr/local/lib/libopus.so.0",
        "/lib/x86_64-linux-gnu/libopus.so.0",
    ]
    for path in standard_paths:
        try:
            discord.opus.load_opus(path)
            print(f"[INFO] libopus cargada: {path}")
            return True
        except Exception:
            continue

    # Rutas de NixOS (Replit)
    nix_paths = [
        "/nix/store/0py9xncsn0s6vqxhvqblvhs2cqbb30s8-libopus-1.5.2/lib/libopus.so.0",
        "/nix/store/235dxwql4lqrfjfhqrld8i3pwcffhwxf-libopus-1.4/lib/libopus.so.0",
    ]
    for path in nix_paths:
        if os.path.exists(path):
            try:
                discord.opus.load_opus(path)
                print(f"[INFO] libopus cargada (nix): {path}")
                return True
            except Exception:
                continue

    # Busqueda dinamica en NixOS como ultimo recurso
    try:
        result = subprocess.run(
            ["sh", "-c", "ls /nix/store 2>/dev/null | grep -m3 'libopus'"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().splitlines():
            path = f"/nix/store/{line.strip()}/lib/libopus.so.0"
            if os.path.exists(path):
                try:
                    discord.opus.load_opus(path)
                    print(f"[INFO] libopus cargada (nix dinamico): {path}")
                    return True
                except Exception:
                    continue
    except Exception:
        pass

    print("[ERROR] No se pudo cargar libopus. El audio no funcionara.")
    return False


async def fetch_stream_url(webpage_url):
    loop = asyncio.get_event_loop()
    opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "source_address": "0.0.0.0",
        "http_headers": BROWSER_HEADERS,
        "socket_timeout": 15,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = await loop.run_in_executor(
            None, lambda: ydl.extract_info(webpage_url, download=False)
        )
        return info["url"]


class MusicPlayer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.queue = deque()
        self.current = None
        self.volume = 0.5
        self._loop = asyncio.get_event_loop()

    async def add_to_queue(self, ctx, query):
        song_info = await self._fetch_song_info(query)
        if song_info is None:
            await ctx.send(
                "No se pudo encontrar la cancion. Intenta con una URL directa de YouTube "
                "o un nombre diferente."
            )
            return

        self.queue.append(song_info)

        embed = discord.Embed(
            title="Agregado a la cola",
            description=f"[{song_info['title']}]({song_info['url']})",
            color=discord.Color.green()
        )
        if song_info.get("thumbnail"):
            embed.set_thumbnail(url=song_info["thumbnail"])
        if song_info.get("duration"):
            mins, secs = divmod(song_info["duration"], 60)
            embed.add_field(name="Duracion", value=f"{mins}:{secs:02d}", inline=True)
        embed.add_field(name="Posicion en cola", value=str(len(self.queue)), inline=True)
        await ctx.send(embed=embed)

        vc = ctx.voice_client
        if not vc.is_playing() and not vc.is_paused():
            await self._play_next(ctx)

    async def _fetch_song_info(self, query):
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                if not query.startswith("http"):
                    query = f"ytsearch:{query}"
                info = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(query, download=False)
                )
                if "entries" in info:
                    info = info["entries"][0]
                return {
                    "title": info.get("title", "Titulo desconocido"),
                    "url": info.get("webpage_url") or info.get("original_url") or query,
                    "thumbnail": info.get("thumbnail"),
                    "duration": info.get("duration", 0),
                }
        except Exception as e:
            print(f"[ERROR] Al buscar '{query}': {type(e).__name__}: {e}")
            return None

    async def _play_next(self, ctx):
        if not self.queue:
            self.current = None
            return

        self.current = self.queue.popleft()
        vc = ctx.voice_client

        if vc is None or not vc.is_connected():
            self.current = None
            return

        try:
            print(f"[INFO] Obteniendo stream para: {self.current['title']}")
            stream_url = await fetch_stream_url(self.current["url"])
            print(f"[INFO] Stream obtenido, iniciando reproduccion...")

            find_and_load_opus()

            source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
            source = discord.PCMVolumeTransformer(source, volume=self.volume)

            def after_playing(error):
                if error:
                    print(f"[ERROR] Durante reproduccion: {error}")
                fut = asyncio.run_coroutine_threadsafe(
                    self._play_next(ctx), self._loop
                )
                try:
                    fut.result()
                except Exception as e:
                    print(f"[ERROR] En after_playing: {e}")

            vc.play(source, after=after_playing)
            print(f"[INFO] Reproduciendo: {self.current['title']}")

            embed = discord.Embed(
                title="Reproduciendo ahora",
                description=f"[{self.current['title']}]({self.current['url']})",
                color=discord.Color.blue()
            )
            if self.current.get("thumbnail"):
                embed.set_thumbnail(url=self.current["thumbnail"])
            if self.current.get("duration"):
                mins, secs = divmod(self.current["duration"], 60)
                embed.add_field(name="Duracion", value=f"{mins}:{secs:02d}", inline=True)
            await ctx.send(embed=embed)

        except Exception as e:
            print(f"[ERROR] Al reproducir '{self.current['title']}': {type(e).__name__}: {e}")
            await ctx.send("No se pudo reproducir esta cancion. Saltando...")
            await self._play_next(ctx)
