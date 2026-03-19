import discord
import asyncio
import yt_dlp
from collections import deque

YDL_SEARCH_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

FFMPEG_BEFORE_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn"


async def fetch_stream_url(webpage_url):
    loop = asyncio.get_event_loop()
    opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "source_address": "0.0.0.0",
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
        self.volume = 100
        self._loop = asyncio.get_event_loop()

    async def add_to_queue(self, ctx, query):
        song_info = await self._fetch_song_info(query)
        if song_info is None:
            await ctx.send("No se pudo encontrar la cancion. Intenta con otro nombre o URL.")
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
            with yt_dlp.YoutubeDL(YDL_SEARCH_OPTIONS) as ydl:
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
            print(f"[ERROR] Al buscar la cancion: {e}")
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
            print(f"[INFO] Stream URL obtenido correctamente")

            source = discord.FFmpegOpusAudio(
                stream_url,
                before_options=FFMPEG_BEFORE_OPTIONS,
                options=FFMPEG_OPTIONS,
            )

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
            await ctx.send(f"No se pudo reproducir esta cancion. Saltando a la siguiente...")
            await self._play_next(ctx)
