import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
import os

API_KEY = os.getenv('DISCRODE_API_KEY')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='m!', intents=intents)
song_queue = []
ctx_queue = []

def extract_url(url):
    '''This function extracts the best audio format URL from a given video URL.
    @input: url: str
    @return: str'''
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']  # Get the URL of the best audio format
    return url2

async def join_vc(ctx):
    '''This function connects the bot to the voice channel of the user who called the command.
    @input: ctx: discord.ext.commands.Context
    @return: discord.VoiceClient'''
    voice_channel = ctx.author.voice.channel
    vc = await voice_channel.connect()
    return vc

async def is_bot_connected(ctx):
    '''This function checks if the bot is connected to a voice channel.
    @input: ctx: discord.ext.commands.Context
    @return: bool'''
    for vc in bot.voice_clients:
        if vc.guild == ctx.guild:
            return True
    return False

@bot.command()
async def search(ctx, url):
    '''Command to add a song URL to the queue.'''
    song_queue.append(url)
    ctx_queue.append(ctx)
    await ctx.send(f"Added {url} to the queue.")

@bot.command()
async def play(ctx, url):
    '''Command to add a song URL to the queue.'''
    song_queue.append(url)
    ctx_queue.append(ctx)
    await ctx.send(f"Added {url} to the queue.")

@bot.command()
async def queue(ctx):
    '''Command to display the current queue'''
    if song_queue:
        await ctx.send(f"Current queue: {', '.join(song_queue)}")
    else:
        await ctx.send("The queue is empty.")

@tasks.loop(seconds=2)
async def check_queue():
    '''Task to check the song queue and play songs.'''
    if song_queue:
        song_url = song_queue.pop(0)
        ctx = ctx_queue.pop(0)
        if not await is_bot_connected(ctx):
            await join_vc(ctx)
        await play_song_from_queue(song_url, ctx)

@bot.event
async def on_ready():
    '''Event called when the bot is ready.'''
    print(f'Logged in as {bot.user}')
    check_queue.start()

async def play_song_from_queue(song_url, ctx):
    '''This function takes a song URL from the song queue and plays it.
    @input: song_url: str
    @return: None or Error'''
    e_url = extract_url(song_url)
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc is None:
        vc = await join_vc(ctx)
    vc.play(discord.FFmpegPCMAudio(executable=r"C:\Program Files\ffmpeg\ffmpeg\bin\ffmpeg.exe", source=e_url))
    print(f"Playing audio from URL: {e_url}")
    await ctx.send(f"Now playing: {song_url}")

bot.run(API_KEY)