import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
import secrets
import re

# Configuración de FFmpeg con la ruta específica
ffmpeg_opts = {'options': '-vn', 'executable': 'C:\\ffmpeg\\bin\\ffmpeg.exe'}

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
        await goodbye_channel.send(f"{member.name} 𝓼𝓮 𝓯𝓾𝓮 𝓭𝓮𝓵 𝓼𝓮𝓻𝓿𝓲𝓭𝓸𝓻 𝓺𝓾𝓮 𝓹𝓮𝓷𝓪 :𝓬." )

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
    # Verificar si el usuario está en un canal de voz
    if ctx.author.voice is None:
        await ctx.send("¡Debes estar en un canal de voz para usar este comando!")
        return

    voice_channel = ctx.author.voice.channel

    # Conectar al canal de voz
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_connected():
        await vc.move_to(voice_channel)
    else:
        vc = await voice_channel.connect()

    # Configuración de yt_dlp
    ydl_opts = {'format': 'bestaudio', 'noplaylist': 'True'}

    # Detectar si el input es un enlace o un término de búsqueda
    url_regex = re.compile(r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$')
    is_url = bool(url_regex.match(search))

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if is_url:  # Si es un enlace directo
                info = ydl.extract_info(search, download=False)
            else:  # Si es un término de búsqueda
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]

            url = info['url']
            title = info['title']
    except Exception as e:
        await ctx.send("No se encontró la música o ocurrió un error al procesar la búsqueda.")
        print(f"Error: {e}")
        return

    # Reproducir el audio
    if not vc.is_playing():
        vc.play(discord.FFmpegPCMAudio(url, **ffmpeg_opts), after=lambda e: print(f"Error en reproducción: {e}") if e else None)
        await ctx.send(f"Reproduciendo: {title}")
    else:
        await ctx.send("Ya se está reproduciendo una canción. Usa un comando de detener o pausa primero.")

# Tarea para desconectar el bot de canales inactivos
@tasks.loop(seconds=60)
async def check_voice_channels():
    for vc in bot.voice_clients:
        if not vc.is_playing() and not vc.is_paused():
            await vc.disconnect()
            
            
# Comando !stop
@bot.command(name="stop")
async def stop(ctx):
    # Obtener el cliente de voz conectado al servidor actual
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if not vc or not vc.is_connected():
        await ctx.send("El bot no está conectado a un canal de voz.")
        return

    if vc.is_playing() or vc.is_paused():
        vc.stop()
        await ctx.send("La música ha sido detenida.")
    else:
        await ctx.send("No hay música reproduciéndose en este momento.")

    # Desconectar del canal de voz
    await vc.disconnect()


# Evento on_ready
@bot.event
async def on_ready():
    print(f"{bot.user} está conectado")
    check_voice_channels.start()

# Clase personalizada para el botón
class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        author = interaction.user

        # Verificar si existe una categoría llamada "tickets"
        category = discord.utils.get(guild.categories, name="tickets")
        if category is None:
            category = await guild.create_category("tickets")

        # Verificar si ya hay un canal de ticket para el usuario
        existing_channel = discord.utils.get(category.text_channels, name=f"ticket-{author.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(
                "Ya tienes un ticket abierto. Ve a tu canal de ticket existente.", ephemeral=True
            )
            return

        # Crear un nuevo canal de texto privado
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True),
        }
        for admin_role in guild.roles:
            if admin_role.permissions.administrator:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ticket_channel = await category.create_text_channel(name=f"ticket-{author.name.lower()}", overwrites=overwrites)
        await interaction.response.send_message(
            f"Tu ticket ha sido creado: {ticket_channel.mention}. Se eliminará automáticamente en 2 horas.",
            ephemeral=True,
        )

        # Enviar mensaje en el canal de ticket
        await ticket_channel.send(
            f"¡Hola, {author.mention}! Este es tu ticket. Describe tu problema aquí. Un administrador te responderá pronto.\n\nEste canal será eliminado automáticamente en 2 horas."
        )

        # Programar la eliminación del canal después de 2 horas
        await asyncio.sleep(7200)  # 2 horas en segundos
        await ticket_channel.delete()

# Evento on_ready para agregar la vista
@bot.event
async def on_ready():
    print(f"{bot.user} está conectado")
    # Añadir la vista del botón al bot
    bot.add_view(TicketButton())

# Comando para mostrar el botón de "Abrir Ticket"
@bot.command(name="ticket")
async def ticket(ctx):
    view = TicketButton()
    await ctx.send("Presiona el botón de abajo para abrir un ticket.", view=view)

# Ejecutar el bot
bot.run(secrets.TOKEN)
    