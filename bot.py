import discord
from discord.ext import commands
import asyncio
import os
from music import MusicPlayer

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

music_players = {}


def get_player(ctx):
    player = music_players.get(ctx.guild.id)
    if player is None:
        player = MusicPlayer(ctx)
        music_players[ctx.guild.id] = player
    return player


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
    print("Listo para reproducir musica!")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Falta un argumento. Uso: `!play <cancion o URL>`")
        return
    await ctx.send(f"Error: {str(error)}")
    raise error


@bot.command(name="play", aliases=["p"], help="Reproduce una cancion de YouTube")
async def play(ctx, *, query: str):
    if not ctx.author.voice:
        await ctx.send("Debes estar en un canal de voz para usar este comando.")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await voice_channel.connect()
    elif ctx.voice_client.channel != voice_channel:
        await ctx.voice_client.move_to(voice_channel)

    player = get_player(ctx)
    async with ctx.typing():
        await player.add_to_queue(ctx, query)


@bot.command(name="pause", help="Pausa la musica")
async def pause(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await ctx.send("Musica pausada.")
    else:
        await ctx.send("No hay musica reproduciendose.")


@bot.command(name="resume", help="Reanuda la musica")
async def resume(ctx):
    vc = ctx.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await ctx.send("Musica reanudada.")
    else:
        await ctx.send("La musica no esta pausada.")


@bot.command(name="stop", help="Detiene la musica y desconecta al bot")
async def stop(ctx):
    vc = ctx.voice_client
    if vc:
        player = music_players.get(ctx.guild.id)
        if player:
            player.queue.clear()
            player.current = None
        vc.stop()
        await vc.disconnect()
        music_players.pop(ctx.guild.id, None)
        await ctx.send("Musica detenida. Hasta luego!")
    else:
        await ctx.send("El bot no esta en un canal de voz.")


@bot.command(name="skip", aliases=["s"], help="Salta la cancion actual")
async def skip(ctx):
    vc = ctx.voice_client
    if vc and (vc.is_playing() or vc.is_paused()):
        vc.stop()
        await ctx.send("Cancion saltada.")
    else:
        await ctx.send("No hay musica reproduciendose.")


@bot.command(name="volume", aliases=["vol"], help="Ajusta el volumen (0-100)")
async def volume(ctx, level: int):
    if level < 0 or level > 100:
        await ctx.send("El volumen debe ser entre 0 y 100.")
        return
    player = get_player(ctx)
    player.volume = level / 100
    vc = ctx.voice_client
    if vc and vc.source:
        vc.source.volume = level / 100
    await ctx.send(f"Volumen ajustado a {level}%.")


@bot.command(name="queue", aliases=["q"], help="Muestra la lista de reproduccion")
async def queue(ctx):
    player = get_player(ctx)
    if not player.queue and not player.current:
        await ctx.send("La lista de reproduccion esta vacia.")
        return

    embed = discord.Embed(title="Lista de Reproduccion", color=discord.Color.blue())

    if player.current:
        embed.add_field(
            name="Reproduciendo ahora:",
            value=f"[{player.current['title']}]({player.current['url']})",
            inline=False
        )

    if player.queue:
        queue_list = []
        for i, song in enumerate(list(player.queue)[:10], 1):
            queue_list.append(f"`{i}.` [{song['title']}]({song['url']})")
        embed.add_field(
            name="En cola:",
            value="\n".join(queue_list),
            inline=False
        )
        if len(player.queue) > 10:
            embed.set_footer(text=f"... y {len(player.queue) - 10} cancion(es) mas")

    await ctx.send(embed=embed)


@bot.command(name="nowplaying", aliases=["np"], help="Muestra la cancion actual")
async def nowplaying(ctx):
    player = get_player(ctx)
    if player.current:
        embed = discord.Embed(
            title="Reproduciendo ahora",
            description=f"[{player.current['title']}]({player.current['url']})",
            color=discord.Color.green()
        )
        if player.current.get("thumbnail"):
            embed.set_thumbnail(url=player.current["thumbnail"])
        if player.current.get("duration"):
            mins, secs = divmod(player.current["duration"], 60)
            embed.add_field(name="Duracion", value=f"{mins}:{secs:02d}", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send("No hay musica reproduciendose.")


@bot.command(name="clear", help="Limpia la lista de reproduccion")
async def clear(ctx):
    player = get_player(ctx)
    player.queue.clear()
    await ctx.send("Lista de reproduccion limpiada.")


@bot.command(name="leave", help="Desconecta el bot del canal de voz")
async def leave(ctx):
    vc = ctx.voice_client
    if vc:
        player = music_players.get(ctx.guild.id)
        if player:
            player.queue.clear()
        vc.stop()
        await vc.disconnect()
        music_players.pop(ctx.guild.id, None)
        await ctx.send("Desconectado del canal de voz.")
    else:
        await ctx.send("No estoy en un canal de voz.")


@bot.command(name="comandos", aliases=["ayuda"], help="Muestra la lista de comandos")
async def comandos(ctx):
    embed = discord.Embed(
        title="Comandos del Bot de Musica",
        color=discord.Color.purple()
    )
    comandos_lista = [
        ("!play <cancion>", "Reproduce una cancion de YouTube (URL o nombre)"),
        ("!pause", "Pausa la musica"),
        ("!resume", "Reanuda la musica"),
        ("!stop", "Detiene la musica y desconecta al bot"),
        ("!skip", "Salta la cancion actual"),
        ("!volume <0-100>", "Ajusta el volumen"),
        ("!queue", "Muestra la lista de reproduccion"),
        ("!nowplaying", "Muestra la cancion que suena ahora"),
        ("!clear", "Limpia la lista de reproduccion"),
        ("!leave", "Desconecta el bot del canal de voz"),
    ]
    for cmd, desc in comandos_lista:
        embed.add_field(name=cmd, value=desc, inline=False)
    embed.set_footer(text="Prefijo: !  |  Aliases: !p=!play, !s=!skip, !q=!queue, !np=!nowplaying")
    await ctx.send(embed=embed)


if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN no esta configurado en las variables de entorno.")
    bot.run(token)
