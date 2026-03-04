import discord
from discord.app_commands import Choice
from discord.ext import commands
from discord import app_commands
from typing import Optional
import os # .env 파일 로드를 위해 추가
from dotenv import load_dotenv
import aiohttp
import json
import asyncio

# 관리자는 쿨다운 없이, 일반 유저는 30초에 1번만 사용 가능하도록 설정합니다.
def cooldown_check(interaction: discord.Interaction) -> Optional[app_commands.Cooldown]:
    if interaction.user.guild_permissions.administrator:
        return None  # 관리자는 쿨다운 없음
    return app_commands.Cooldown(1, 30.0)

def load_prompt(filename):
    path = f"./prompt/{filename}.txt"
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

# 코그 클래스 정의
class MiniCouncilCog(commands.Cog):
    # 초기화 함수
    def __init__(self, bot: commands.Bot):
        load_dotenv()
        self.bot = bot
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.key = os.getenv("OPENROUTER_KEY")
        self.chairman = "google/gemini-3.1-pro-preview"
        self.workers = {
            "flash": "google/gemini-2.5-flash",
            "mini": "openai/gpt-5-mini",
            "haiku": "anthropic/claude-haiku-4.5",
            "sonar": "perplexity/sonar",
            "fast": "x-ai/grok-4.1-fast"
        }
        self.roles = {
            "flash": "빠르고 정확한 데이터 요약 전문가",
            "mini": "친절하고 상세한 가이드 전문가",
            "haiku": "논리적 허점을 찾아내는 비판적 분석가",
            "sonar": "최신 정보를 샅샅이 뒤지는 실시간 검색 전문가",
            "fast": "실시간 여론과 트렌드를 읽는 유행 민감 전문가"
        }

    # 쿨다운에 걸린 사용자에게 안내 메시지를 보냅니다.
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            # 남은 시간을 소수점 없이 정수로 표시
            remaining_time = int(error.retry_after)
            await interaction.response.send_message(
                f"코미 쎄진다고 일 더 시키면 안돼? 그러니까 {remaining_time}초 뒤에 다시 시도해 줘.",
                ephemeral=True # 메시지를 본인에게만 보이게 함
            )
        else:
            # 다른 종류의 오류는 콘솔에 출력
            print(error)

    async def get_response(self, model, prompt, user):
        headers = {
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user},
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, headers=headers, json=payload) as resp:
                data = await resp.json()

                if 'choices' not in data:
                    print(f"{model}L {data}")
                    return ""

                content = data['choices'][0]['message']['content']
                return content if content is not None else ""


    @app_commands.command(name="council", description="코미에게 이것저것 물어보기")
    @app_commands.describe(question="물어보고 싶은 것들을 자유롭게 입력해 보세요.")
    @app_commands.checks.dynamic_cooldown(cooldown_check)

    async def ask_kommy(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()

        # 1. 질문을 전달받은 의장님이 각 모델에게 던질 질문을 생성하기
        try:
            council_text = await self.get_response(self.chairman, load_prompt("chairman"), question)
            council_json = council_text.replace("```json", "").replace("```", "").strip()
            council_plan = json.loads(council_json)
            print(council_plan)
        except Exception as e:
            print(f"1. 의장님 소환 중 오류 발생: {e}")
            await interaction.followup.send("으... 잠이 부족했나봐. (아르바이트 실패)")
            return

        # 2. 각 모델들의 동시 출동. (병렬 처리 필요.)
        try:
            assignment = council_plan.get("assignments", {})
            tasks = []
            for name, model in self.workers.items():
                task = assignment.get(name, "관련 내용을 조사해줘.")
                role = self.roles.get(name, "특정 분야의 전문가")
                message = (
                    f"당신은 {role}입니다. 주어지는 업무를 전문적으로 수행하세요."
                    "불필요한 인사말이나 서론은 생략하고, 간결하게 의견만 이야기 하세요."
                    "응답은 10문장 내외로 간추려 주세요."
                )
                tasks.append(self.get_response(model, message, task))

            response = await asyncio.gather(*tasks)
            worker_results = dict(zip(self.workers.keys(), response))
            print(worker_results)
        except Exception as e:
            print(f"2. 모델 소집 중 오류 발생: {e}")
            await interaction.followup.send("아무리 이래도 어거지 공부는 안 할거야~! (아르바이트 실패)")
            return
        # 3. 코미의 최종 수합 보고.
        try:
            results = [f"[{name} 친구의 보고]: {content}" for name, content in worker_results.items() if content.strip()]
            input_prompt = f"교주의 원래 질문: {question}\n\n친구들이 조사한 결과는 다음과 같아:\n{results}"
            kommy_text = await self.get_response(self.chairman, load_prompt("kommy"), input_prompt)
            kommy_json = kommy_text.replace("```json", "").replace("```", "").strip()
            kommy_data = json.loads(kommy_json)
            print(kommy_data)
        except Exception as e:
            print(f"3. 코미 대답 중 오류 발생: {e}")
            await interaction.followup.send("아무것도 하기 싫다... 으으... (아르바이트 실패)")
            return
        # 4. 최종 Embed 출력
        try:
            embed = discord.Embed(
                title=f"💤 {kommy_data.get('one_liner', '하암...')}",
                description=kommy_data.get('final_report', "교주, 코미가 아무래도 보고서를 잃어버렸어..."),
                color=discord.Color.pink()
            )

            summaries = kommy_data.get("worker_summaries", {})
            count = 1
            for name, summary in summaries.items():
                # 만약 내용이 비어있거나 AI가 제대로 응답하지 않았다면 추가하지 않고 건너뜁니다.
                if not summary or summary.strip() == "":
                    continue

                embed.add_field(
                    name=f"🐾 익명의 사료 친구 {count}",
                    value=summary,
                    inline=False
                )
                count += 1  # 필드가 추가될 때만 번호를 올립니다.

            embed.set_author(name=f"{interaction.user.display_name} 교주에게", icon_url=interaction.user.avatar.url)
            embed.set_footer(text="코미도 할 때는 한다고. 그래도 코미는 실수할 수 있는 거 알지?")

            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"4. 임베드 출력 중 오류 발생: {e}")
            await interaction.followup.send("코미 이거... 해야 돼? (아르바이트 실패)")
            return
# 봇에 코그를 추가하기 위한 필수 함수
async def setup(bot: commands.Bot):
    await bot.add_cog(MiniCouncilCog(bot))
