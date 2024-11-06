import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
import json

with open('api_key.txt', 'r') as f:
          API_KEY = f.read
          

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
last_active_time = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    check_inactivity.start()

@bot.command()
async def play(ctx, url):
    try:
        # Set up yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        # Extract video information without downloading
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']  # Get the URL of the best audio format
            print(f"Extracted URL: {url2}")
        
        # Connect to the user's voice channel
        voice_channel = ctx.author.voice.channel
        vc = await voice_channel.connect()
        print(f"Connected to voice channel: {voice_channel}")
        
        # Define a callback function to be called after playback is finished
        def after_playback(error):
            if error:
                print(f"Error during playback: {error}")
            else:
                print("Playback finished")
            # Disconnect from the voice channel after playback
            asyncio.run_coroutine_threadsafe(vc.disconnect(), bot.loop)
        
        # Play the audio using FFmpeg
        vc.play(discord.FFmpegPCMAudio(executable=r"C:\Program Files\ffmpeg\ffmpeg\bin\ffmpeg.exe", source=url2), after=after_playback)
        print(f"Playing audio from URL: {url2}")
        
        # Update last active time for the guild
        last_active_time[ctx.guild.id] = asyncio.get_event_loop().time()
        # Send a confirmation message
        await ctx.send(f"Now playing: {info['title']}")
    except Exception as e:
        # Handle any errors that occur
        await ctx.send(f"An error occurred: {str(e)}")
        print(f"An error occurred: {str(e)}")


@bot.command()
async def search(ctx, *, query):
   try:
       print("not implimented yet")
   except Exception as e:
       print(e)

@bot.command()
async def mog_help(ctx):
    await ctx.send("Commands:\n!play <url>: Play audio from a URL\n!search <query>: Search for a video on YouTube\n!leave: Leave the voice channel")

@bot.command()
async def mog(ctx):
    await ctx.send("Get Mogged bro")

@tasks.loop(minutes=1)
async def check_inactivity():
    current_time = asyncio.get_event_loop().time()
    for guild_id, last_active in list(last_active_time.items()):
        if current_time - last_active > 240:  # 4 minutes
            guild = bot.get_guild(guild_id)
            if guild and guild.voice_client:
                await guild.voice_client.disconnect()
                del last_active_time[guild_id]

bot.run(API_KEY)