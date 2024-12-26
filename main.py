import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
import os
import re
from flask import Flask
from threading import Thread

# Configuración de FFmpeg (sin ruta específica, ya que Railway la proporciona)
ffmpeg_opts = {'options': '-vn'}

# Configuración del bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


# Evento cuando el bot se une a un servidor
@bot.event
async def on_guild_join(guild):
    # Crear canal de bienvenida
    welcome_channel = await guild.create_text_channel("bienvenida")
    await welcome_channel.send("¡Bienvenidos! Exploren los canales y disfruten del servidor.")

    # Crear canal de despedida
    goodbye_channel = await guild.create_text_channel("despedida")
    await goodbye_channel.send("Este será el lugar donde despediremos a los miembros.")


# Evento para dar la bienvenida a nuevos miembros
@bot.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name="bienvenida")
    if welcome_channel:
        await welcome_channel.send(f"¡𝓑𝓲𝓮𝓷𝓿𝓮𝓷𝓲𝓭𝓸/𝓪 {member.mention} 𝓪 𝓐𝓫𝔂𝓼𝓶𝓪𝓵 𝓢𝓱𝓪𝓭𝓸𝔀!")


# Evento para despedir a miembros que salen 
@bot.event
async def on_member_remove(member):
    goodbye_channel = discord.utils.get(member.guild.text_channels, name="despedida")
    if goodbye_channel:
        await goodbye_channel.send(f"{member.name} 𝓼𝓮 𝓯𝓾𝓮 𝓭𝓮𝓵 𝓼𝓮𝓻𝓿𝓲𝓭𝓸𝓻 𝓺𝓾𝓮 𝓹𝓮𝓷𝓪 :𝓬.")


# Comando de compatibilidad
@bot.command()
async def compatibilidad(ctx, user1: str, user2: str):
    import random
    guild = ctx.guild
    member1 = discord.utils.get(guild.members, mention=user1) or discord.utils.get(guild.members, name=user1)
    member2 = discord.utils.get(guild.members, mention=user2) or discord.utils.get(guild.members, name=user2)

    if not member1 or not member2:
        await ctx.send("No se encontró a uno o ambos usuarios. Por favor, menciona correctamente o usa nombres de usuario válidos.")
        return

    porcentaje = random.randint(0, 100)
    await ctx.send(f"La compatibilidad entre {member1.mention} y {member2.mention} es del {porcentaje}%.")


# Comando de ayuda
@bot.command()
async def help(ctx):
    help_message = (
        "!p (link de YT) @AbysmalBot \n\n !stop @AbysmalBot  \n\n  !compatibilidad @user1 @user2 @AbysmalBot"
    )
    await ctx.send(help_message)


# Comando !play
@bot.command(name="play", aliases=["p"])
async def play(ctx, *, search):
    if ctx.author.voice is None:
        await ctx.send("¡Debes estar en un canal de voz para usar este comando!")
        return

    voice_channel = ctx.author.voice.channel
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_connected():
        await vc.move_to(voice_channel)
    else:
        vc = await voice_channel.connect()

    ydl_opts = {'format': 'bestaudio', 'noplaylist': 'True'}
    url_regex = re.compile(r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$')
    is_url = bool(url_regex.match(search))

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if is_url:
                info = ydl.extract_info(search, download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]

            url = info['url']
            title = info['title']
    except Exception as e:
        await ctx.send("No se encontró la música o ocurrió un error al procesar la búsqueda.")
        print(f"Error: {e}")
        return

    if not vc.is_playing():
        vc.play(discord.FFmpegPCMAudio(url, **ffmpeg_opts), after=lambda e: print(f"Error en reproducción: {e}") if e else None)
        await ctx.send(f"Reproduciendo: {title}")
    else:
        await ctx.send("Ya se está reproduciendo una canción. Usa un comando de detener o pausa primero.")


# Comando !stop
@bot.command(name="stop")
async def stop(ctx):
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not vc or not vc.is_connected():
        await ctx.send("El bot no está conectado a un canal de voz.")
        return

    if vc.is_playing() or vc.is_paused():
        vc.stop()
        await ctx.send("La música ha sido detenida.")
    else:
        await ctx.send("No hay música reproduciéndose en este momento.")

    await vc.disconnect()


TOKEN = os.getenv("TOKEN")

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

bot.run(TOKEN)
