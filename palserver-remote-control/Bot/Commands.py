import os
import random
import asyncio
from datetime import datetime, timedelta

from discord import Embed, Color, File
from discord.ext import commands, tasks

from Log.Settings import logger, logger_detail
from Bot.PalServer import PalServer


def now_kst():
    return datetime.utcnow() + timedelta(hours=9)


class Commands(commands.Cog):
    '''
    봇 명령어 관리 클래스.
    '''
    def __init__(self, bot):
        self.bot = bot
        self.pal = PalServer()
        self.emo_list = (":grinning:", ":partying_face:", ":star_struck:", ":sunglasses:", ":cowboy:",)
        self.funny_list = ("으거려으", "으으으", "으그래으", "으?", "으.", ":grimacing:", ":face_with_spiral_eyes:",)
        self.member_open = None
        self.member_close = None
        self.member_update = None
        self.time_update = None
        # 자동 알림(서버 다운/복구, 접속/퇴장) 채널. 미설정 시 워처 비활성.
        self.notice_channel_id = int(os.getenv("CHANNEL_NOTICE", "0"))
        self.prev_alive = None
        self.prev_players = None
        if self.notice_channel_id:
            self.watcher.start()

    def cog_unload(self):
        if self.notice_channel_id:
            self.watcher.cancel()

    # 만료된 디스코드 CDN 링크 대신 로컬 images/ 파일을 첨부해서 쓴다.
    @staticmethod
    def thumbnail(name):
        return File(f"./images/{name}", filename=name), f"attachment://{name}"

    async def build_status(self):
        '''서버 상태 엠베드 생성. (엠베드, 썸네일 파일) 반환.'''
        running = await self.pal.container_running()
        alive = running and await self.pal.alive()

        if alive:
            msg, state_color, thumb = "가동중...", Color.green(), "check.png"
            person_title, person_name = "연 사람", self.member_open
        elif running:
            msg, state_color, thumb = "부팅중... (컨테이너는 켜짐, 게임 서버 응답 대기)", Color.yellow(), "cogs.png"
            person_title, person_name = "연 사람", self.member_open
        else:
            msg, state_color, thumb = "닫혀있음.", Color.red(), "x.png"
            person_title, person_name = "닫은 사람", self.member_close

        file, thumb_url = self.thumbnail(thumb)
        ebd = Embed(title=f":eyes: 서버 상태\n{msg}", color=state_color)
        ebd.add_field(name=f":gear: 서버 {person_title}", value=person_name or "기록 없음.", inline=True)

        if alive:
            try:
                info = await self.pal.info()
                metrics = await self.pal.metrics()
                players = await self.pal.players()
                ebd.add_field(name=":bulb: 서버 실행시간", value=self.pal.format_uptime(metrics.get("uptime", 0)), inline=True)
                ebd.add_field(name=":video_game: 게임 버전", value=info.get("version", "?"), inline=True)
                ebd.add_field(name=":chart_with_upwards_trend: 서버 FPS", value=metrics.get("serverfps", "?"), inline=True)
                names = ", ".join(p.get("name", "?") for p in players) or "없음"
                ebd.add_field(
                    name=f":busts_in_silhouette: 접속자 {metrics.get('currentplayernum', len(players))}/{metrics.get('maxplayernum', '?')}",
                    value=names,
                    inline=False,
                )
            except Exception as error:
                logger.error("ERROR : log_detail_palserver.log 참조")
                logger_detail.error(error)
                ebd.add_field(name=":warning:", value="REST API 조회 실패 (자세한 정보 생략)", inline=False)
        else:
            ebd.add_field(name=":bulb: 서버 실행시간", value="00:00", inline=True)

        ebd.add_field(name=":globe_with_meridians: 서버 주소", value=f"`{self.pal.address}`", inline=False)
        person_update = "업데이트 기록 없음." if self.member_update is None else f"{self.member_update} -> {self.time_update} 재시작·업데이트."
        ebd.add_field(name=":loudspeaker: 마지막 업데이트", value=person_update, inline=False)
        ebd.set_thumbnail(url=thumb_url)
        ebd.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)
        return ebd, file

    async def send_status(self, ctx, msg=None):
        try:
            ebd, file = await self.build_status()
            ebd.set_footer(text=f"{ctx.message.author.display_name}", icon_url=ctx.message.author.display_avatar)
            if msg:
                await msg.edit(content=None, embed=ebd, attachments=[file])
            else:
                await ctx.send(embed=ebd, file=file)
        except Exception as error:
            logger.error("ERROR : log_detail_palserver.log 참조")
            logger_detail.error(error)
            text = "예상하지 못한 에러가 발생했습니다."
            await (msg.edit(content=text) if msg else ctx.send(text))

    # ── 개성 커맨드 (초기 버전 그대로) ─────────────────────────
    @commands.command(aliases=["으"])
    async def funny_sound(self, ctx):
        await ctx.send(f"{self.funny_list[random.randrange(len(self.funny_list))]}")

    @commands.command(aliases=["인사", "안녕"])
    async def hello(self, ctx):
        await ctx.send(f"{ctx.author.display_name}님, 안녕하세요! {self.emo_list[random.randrange(len(self.emo_list))]}")

    @commands.command(aliases=["명령", "명령어"])
    async def find_command(self, ctx):
        file, thumb_url = self.thumbnail("cogs.png")
        ebd = Embed(title="명령어 모음", description="서버 원격 조종 명령어 모음 안내입니다.\n자세한 사항은 [여기](https://github.com/mhd329/pjt-personal)를 참조하세요.\n```md\n 1. [!!핑][봇 응답속도 확인.]\n\n 2. [!!인사][봇과 인사 주고받기.]\n\n 3. [!!명령][봇 명령어 확인.]\n\n 4. [!!상태][서버 상태 확인.]\n\n 5. [!!접속자][현재 접속자 목록.]\n\n 6. [!!열기][서버 열기.]\n\n 7. [!!닫기][서버 닫기.]\n\n 8. [!!업데이트][서버 재시작 + 업데이트.]\n\n 9. [!!저장][월드 즉시 저장.]\n\n10. [!!공지 <내용>][인게임 전체 공지.]\n```")
        ebd.set_thumbnail(url=thumb_url)
        ebd.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)
        ebd.set_footer(text=f"{ctx.message.author.display_name}", icon_url=ctx.message.author.display_avatar)
        await ctx.send(embed=ebd, file=file)

    @commands.command(aliases=["핑"])
    async def ping(self, ctx):
        msg = await ctx.send(":ping_pong:")
        latency = round((msg.created_at - ctx.message.created_at).microseconds // 1000)
        api_latency = round(self.bot.latency * 1000)
        ping_color = Color.red()
        result = "늦음"
        if latency < 501:
            ping_color = Color.yellow()
            result = "보통 "
        if latency < 201:
            ping_color = Color.green()
            result = "빠름"
        file, thumb_url = self.thumbnail("android.png")
        ebd = Embed(title=":ping_pong:", description=f"\n**속도** : {result}\n**Latency** : `{latency}ms`\n**API Latency** : `{api_latency}ms`\n위 수치들은 인게임 서버 상태와는 무관합니다.\n", color=ping_color)
        ebd.set_thumbnail(url=thumb_url)
        ebd.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)
        ebd.set_footer(text=f"{ctx.message.author.display_name}", icon_url=ctx.message.author.display_avatar)
        await msg.edit(content=None, embed=ebd, attachments=[file])

    # ── 서버 제어 커맨드 ──────────────────────────────────────
    @commands.command(aliases=["상태"])
    async def state(self, ctx):
        await self.send_status(ctx)

    @commands.command(aliases=["접속자", "명단"])
    async def player_list(self, ctx):
        try:
            players = await self.pal.players()
            if not players:
                await ctx.send("현재 접속자가 없습니다.")
                return
            lines = "\n".join(
                f"- **{p.get('name', '?')}** (Lv.{p.get('level', '?')}, {p.get('ping', 0):.0f}ms)"
                for p in players
            )
            ebd = Embed(title=f":busts_in_silhouette: 접속자 {len(players)}명", description=lines, color=Color.green())
            await ctx.send(embed=ebd)
        except Exception as error:
            logger.error("ERROR : log_detail_palserver.log 참조")
            logger_detail.error(error)
            await ctx.send("서버가 꺼져 있거나 응답하지 않습니다.")

    @commands.cooldown(1, 60, commands.BucketType.guild)  # 1분에 한 번만 가능
    @commands.command(aliases=["열기"])
    async def open_server(self, ctx):
        msg = await ctx.send("서버를 시작합니다.\n잠시만 기다려주세요...")
        code, out = await self.pal.start()
        if code != 0:
            logger.error(out)
            await msg.edit(content="서버 시작에 실패했습니다. (로그 참조)")
            return
        self.member_open = ctx.message.author.display_name
        # 게임 서버가 응답할 때까지 대기 (모드 없는 서버라 보통 1~2분 내)
        for _ in range(30):
            if await self.pal.alive():
                break
            await asyncio.sleep(10)
        await self.send_status(ctx, msg)

    @commands.cooldown(1, 60, commands.BucketType.guild)  # 1분에 한 번만 가능
    @commands.command(aliases=["닫기", "서버닫기", "끄기", "서버끄기"])
    async def close_server(self, ctx):
        try:
            players = await self.pal.players()
            if players:
                names = ", ".join(p.get("name", "?") for p in players)
                await ctx.send(f"접속자가 있어 종료할 수 없습니다: {names}\n(강제 종료가 필요하면 접속자가 나간 뒤 다시 시도해주세요.)")
                return
        except Exception:
            pass  # API 응답이 없으면 접속자 없음으로 간주하고 종료 진행
        msg = await ctx.send("서버를 종료합니다.\n잠시만 기다려주세요...")
        code, out = await self.pal.stop()
        if code != 0:
            logger.error(out)
            await msg.edit(content="서버 종료에 실패했습니다. (로그 참조)")
            return
        self.member_close = ctx.message.author.display_name
        await self.send_status(ctx, msg)

    @commands.cooldown(1, 600, commands.BucketType.guild)  # 10분에 한 번만 가능
    @commands.command(aliases=["업데이트", "재시작"])
    async def update_server(self, ctx):
        '''컨테이너 재시작 = 스팀 업데이트 반영(UPDATE_ON_BOOT). 접속자에게 1분 예고 후 실행.'''
        try:
            if await self.pal.players():
                await self.pal.announce("[공지] 1분 뒤 서버가 재시작됩니다. 안전한 곳에서 대기해주세요!")
                await ctx.send("접속자에게 인게임 공지를 보냈습니다. 1분 뒤 재시작합니다...")
                await asyncio.sleep(60)
            await self.pal.save()
        except Exception:
            pass  # 서버가 꺼져 있어도 재시작(=시작+업데이트)은 진행
        msg = await ctx.send("재시작 + 업데이트 중입니다.\n잠시만 기다려주세요...")
        code, out = await self.pal.restart()
        if code != 0:
            logger.error(out)
            await msg.edit(content="재시작에 실패했습니다. (로그 참조)")
            return
        self.time_update = now_kst().strftime("%Y년 %m월 %d일 %p %I:%M:%S")
        self.member_update = ctx.message.author.display_name
        for _ in range(30):
            if await self.pal.alive():
                break
            await asyncio.sleep(10)
        await self.send_status(ctx, msg)

    @commands.command(aliases=["저장"])
    async def save_world(self, ctx):
        try:
            await self.pal.save()
            await ctx.send(":floppy_disk: 월드를 저장했습니다.")
        except Exception as error:
            logger.error("ERROR : log_detail_palserver.log 참조")
            logger_detail.error(error)
            await ctx.send("저장에 실패했습니다. 서버가 켜져 있는지 확인해주세요.")

    @commands.command(aliases=["공지"])
    async def announce(self, ctx, *, message):
        try:
            await self.pal.announce(f"[{ctx.author.display_name}] {message}")
            await ctx.send(":loudspeaker: 인게임에 공지했습니다.")
        except Exception as error:
            logger.error("ERROR : log_detail_palserver.log 참조")
            logger_detail.error(error)
            await ctx.send("공지에 실패했습니다. 서버가 켜져 있는지 확인해주세요.")

    # ── 자동 알림 워처 ────────────────────────────────────────
    @tasks.loop(seconds=60)
    async def watcher(self):
        '''서버 다운/복구·접속/퇴장을 감지해서 알림 채널에 보고한다.'''
        try:
            channel = self.bot.get_channel(self.notice_channel_id)
            if channel is None:
                return
            alive = await self.pal.alive()

            if self.prev_alive is not None and alive != self.prev_alive:
                if alive:
                    await channel.send(":green_circle: **팰월드 서버 복구됨** — 다시 접속할 수 있습니다.")
                else:
                    running = await self.pal.container_running()
                    detail = "컨테이너는 켜져 있는데 게임 서버가 응답하지 않습니다(재시작 중이거나 문제 발생)." if running else "컨테이너가 꺼졌습니다."
                    await channel.send(f":red_circle: **팰월드 서버 응답 없음** — {detail}")
            self.prev_alive = alive

            if alive:
                names = {p.get("name", "?") for p in await self.pal.players()}
                if self.prev_players is not None:
                    for name in sorted(names - self.prev_players):
                        await channel.send(f":wave: **{name}** 님이 접속했습니다.")
                    for name in sorted(self.prev_players - names):
                        await channel.send(f":door: **{name}** 님이 나갔습니다.")
                self.prev_players = names
            else:
                self.prev_players = None
        except Exception as error:
            logger_detail.error(error)

    @watcher.before_loop
    async def before_watcher(self):
        await self.bot.wait_until_ready()
