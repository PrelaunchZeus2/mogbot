import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
import os
import random as rand

API_KEY = os.getenv('DISCRODE_API_KEY')
if API_KEY is None:
    raise ValueError("Please set the DISCRODE_API_KEY environment variable.")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='m!', intents=intents)
song_queue = []
ctx_queue = []
search_results_cache = {}

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
async def search(ctx, *, search_query):
    '''Command to search for a song on YouTube and prompt the user to select a result.'''
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch:{search_query}", download=False)
        if 'entries' in search_results:
            search_results_cache[ctx.author.id] = search_results['entries']
            results_message = '\n'.join([f"{i+1}. {entry['title']}" for i, entry in enumerate(search_results['entries'][:10])])
            await ctx.send(f"Search results:\n{results_message}\nEnter the number of the song you want to add to the queue:")
        else:
            await ctx.send("No results found.")

@bot.command()
async def stop(ctx):
    '''Command to stop the bot from playing audio.'''
    if vc is not None:
        await vc.disconnect()
        await ctx.send("Stopped playing audio.")
    else:
        await ctx.send("I am not currently playing audio.")
    
bot.command()
async def coinflip(ctx):
    '''Command to flip a coin.'''
    result = rand.choice(['Heads', 'Tails'])
    await ctx.send(result)
@bot.command()
async def help(ctx):
    '''Command to display the help message.'''
    await ctx.send("Commands:\n"
                   "m!play <url>: Add a song to the queue.\n"
                   "m!queue: Display the current queue.\n"
                   "m!search <url>: Add a song to the queue.\n"
                   "m!help: Display this message.\n"
                   "m!coinflip: Flip a coin.\n"
                   "m!stop: Stop the bot from playing audio.")
    
@bot.command()
async def quit(ctx):
    '''Secret Command to stop the bot.'''
    await ctx.send("Goodbye!")
    await bot.close()
    
@bot.command()
async def stay_frosty(ctx):
    '''secret spam command'''
    for i in range(1000):
        a = rand.int(0, 1000000000000)
        if a == 999999: #surely you win these no?
            await ctx.send(API_KEY)
        else:
            await ctx.send("you got mogged by PLZ2")

@bot.event
async def on_message(message):
    '''Event listener to handle user responses for song selection.'''
    await bot.process_commands(message)  # Ensure commands still work

    if message.author.id in search_results_cache:
        try:
            selection = int(message.content)
            if 1 <= selection <= 10:
                selected_song = search_results_cache[message.author.id][selection - 1]
                song_url = selected_song['webpage_url']
                song_queue.append(song_url)
                ctx_queue.append(await bot.get_context(message))  # Store the entire Context object
                await message.channel.send(f"Added {selected_song['title']} to the queue.")
                del search_results_cache[message.author.id]  # Clear the cache for the user
            else:
                await message.channel.send("Please enter a number between 1 and 10.")
        except ValueError:
            await message.channel.send("Please enter a valid number.")

@bot.command()
async def play(ctx, url):
    '''Command to add a song URL to the queue directly.'''
    song_queue.append(url)
    ctx_queue.append(ctx)
    await ctx.send(f"Added to the queue.")

@bot.command()
async def queue(ctx):
    '''Command to display the current queue'''
    if song_queue:
        await ctx.send(f"Current queue: {', '.join(song_queue)}")
    else:
        await ctx.send("The queue is empty.")

@bot.command()
async def skip(ctx):
    '''Command to skip the current song and play the next one in the queue.'''
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("Skipped the current song.")
    else:
        await ctx.send("No song is currently playing.")

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

    def after_playback(error):
        if error:
            print(f"Error during playback: {error}")
        else:
            print("Playback finished")
        if song_queue:
            next_song_url = song_queue.pop(0)
            next_ctx = ctx_queue.pop(0)
            asyncio.run_coroutine_threadsafe(play_song_from_queue(next_song_url, next_ctx), bot.loop)

    vc.play(discord.FFmpegPCMAudio(executable=r"C:\Program Files\ffmpeg\ffmpeg\bin\ffmpeg.exe", source=e_url), after=after_playback)
    print(f"Playing audio from URL: {e_url}")
    await ctx.send(f"Now playing: {song_url}")

bot.run(API_KEY)