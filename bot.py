import discord
from discord.app_commands import Choice
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio

# .env 파일에서 환경 변수 로드
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# 봇 인텐트 설정
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='/', intents=intents)

MY_GUILD = discord.Object(id=os.getenv('MY_GUILD'))  # 실제 서버 ID로 교체하세요
OWNER_ID = os.getenv('OWNER_ID')  # 이 코드를 파일 상단에 추가하여 봇 주인 ID를 변수로 저장합니다.

@bot.event
async def on_ready():
    print(f'{bot.user}이(가) 성공적으로 로그인했습니다.')
    print(f'봇이 {len(bot.guilds)}개의 서버에 연결되었습니다.')
    try:
        synced = await bot.tree.sync(
            # guild=MY_GUILD
        )
        print("전역 커맨드 동기화를 시도합니다. (최대 1시간 소요)")
        print(f"{len(synced)}개의 커맨드가 동기화되었습니다.")
    except Exception as e:
        print(f"커맨드 동기화 중 오류 발생: {e}")

# 봇이 시작될 때 cogs 폴더의 모든 파일을 불러오는 함수
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            # 'cogs.' prefix + 파일 이름에서 '.py' 제거
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"파이썬 파일 발견: {filename[:-3]}")

# 메인 실행 함수
async def main():
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_TOKEN)

# 비동기 함수 실행
if __name__ == '__main__':
    asyncio.run(main())



# 기존 /동기화 명령어
    @app_commands.command(name="동기화", description="봇의 커맨드를 강제로 동기화합니다. (봇 주인 전용)")
    async def sync(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("봇 주인만 사용할 수 있는 명령어입니다.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        synced = await self.bot.tree.sync(guild=interaction.guild)
        await interaction.followup.send(f"✅ {len(synced)}개의 커맨드를 이 서버에 동기화했습니다.")