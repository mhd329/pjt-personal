import os
import sys
import asyncio
from dotenv import load_dotenv


from Bot import Commands, Settings


load_dotenv()


token_bot = os.getenv("TOKEN_BOT")
token_server = os.getenv("TOKEN_SERVER")


# 호스트 전원 제어(/종료, /재부팅)는 제거함.
# 지금 서버는 팰월드 전용기가 아니라 마인크래프트·모니터링 등이 같이 도는 서버라
# 디스코드 봇 권한으로 호스트를 내릴 수 있으면 안 된다. 재시작은 !!재시작(컨테이너)으로 대체.
if __name__ == "__main__":
    if "debugpy" in sys.modules:
        token_server = os.getenv("TOKEN_SERVER_DEBUG")
    bot = Settings(server_id=token_server)
    asyncio.run(bot.add_cog(Commands(bot)))
    bot.run(token_bot)
