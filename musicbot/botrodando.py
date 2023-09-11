import discord
from discord import Intents
from discord.ext import commands
from discord.utils import get
import youtube_dl
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
import sys
import logging
import my_cog
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ignore the specific RuntimeWarning raised by the discord.py library
warnings.filterwarnings("ignore", category=RuntimeWarning, module="botrodando")

intents = Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

token = "seu token"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="your_client_id",
                                                           client_secret="your_client_secret"))


queue = []

async def play_next(ctx):
    guild_id = ctx.guild.id
    if len(queues[guild_id]) > 0:
        url = queues[guild_id].pop(0)
        await play(ctx, url)
    else:
        voice_client = get(ctx. voice_clients, guild=ctx.guild)
        if voice_client is not None:
            # Comment out or remove the following line to prevent the bot from disconnecting
            # await voice_client.disconnect()

            # Add these lines to inform users the queue is empty and the bot is waiting for new songs
            await ctx.send("The queue is empty. Waiting for new songs to be added.")
            while len(queues[guild_id]) == 0:
                await asyncio.sleep(5)
            await play_next(ctx)

@bot.command(name="play")
async def play(ctx, *, search_query):
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }
    YDL_OPTIONS = {'format': 'bestaudio', 'default_search': 'ytsearch'}

    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(search_query, download=False)
        except youtube_dl.utils.DownloadError:
            await ctx.send(f"Error: Unable to download or extract information from {search_query}")
            return

    if info is None or info.get("entries") is None or len(info["entries"]) == 0:
        video_url = info["url"]
    else:
        video_url = info["entries"][0]["url"]

    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel
    else:
        await ctx.send("You must be in a voice channel to use this command.")
        return

    voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
    if voice_client is None or not voice_client.is_connected():
        voice_client = await channel.connect()

    if voice_client.is_playing():
        queue.append(video_url)
        await ctx.send(f"Added to queue: {info.get('title', 'Unknown')}")
    else:
        video_title = info.get("title", "Unknown")
        voice_client.play(discord.FFmpegPCMAudio(video_url, **FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f"Playing: {video_title}")

@bot.command(name="showqueue")
async def show_queue(ctx):
    if queue:
        queue_string = "\n".join([f"{index + 1}. {url}" for index, url in enumerate(queue)])
        await ctx.send(f"Current queue:\n{queue_string}")
    else:
        await ctx.send("The queue is empty.")

@bot.command(name="pause")
async def pause(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Paused.")
    else:
        await ctx.send("Nothing is playing right now.")

@bot.command(name="resume")
async def resume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Resumed.")

@bot.command(name="clearqueue")
async def clear_queue(ctx):
    queue.clear()
    await ctx.send("Cleared the queue.")

@bot.command(name="skip")
async def skip(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        await ctx.send("Skipped.")
        if queue:
            url = queue.pop(0)
            await play(ctx, url)
    else:
        await ctx.send("There's nothing to skip.")

@bot.command(name="para")
async def stop(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client is not None:
        voice_client.stop()


async def start_bot():
    await bot.add_cog(my_cog.MyCog(bot))
    await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except Exception as e:
        logger.exception("An error occurred while running the bot.")
        sys.exit(1)


