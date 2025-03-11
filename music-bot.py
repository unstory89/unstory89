import discord
from discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True  # 메시지 읽기 권한
bot = commands.Bot(command_prefix="!", intents=intents)

# 유튜브 DL 옵션
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6로 인한 문제 방지
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# 봇이 명령어를 받으면 실행하는 부분
@bot.command(name="실행")
async def play(ctx, url: str):
    if not ctx.message.author.voice:
        await ctx.send("먼저 음성 채널에 입장해야 합니다.")
        return

    channel = ctx.message.author.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if not voice_client:
        voice_client = await channel.connect()

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
    
    await ctx.send(f'재생 중: {player.title}')

@bot.command(name="멈춰")
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("음악을 멈추고 봇이 퇴장했습니다.")
    else:
        await ctx.send("봇이 음성 채널에 있지 않습니다.")

# 토큰으로 봇 실행
bot.run('MTM0ODc0NTQ2NDEwMjc4MTAwOA.GD4Otb.nIynvXtKySgAxtzDK2jL841DFjNLBfJlpvQy24')