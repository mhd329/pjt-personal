import os
import asyncio

import aiohttp


class PalServer:
    '''
    팰월드 서버 제어 클래스.
    도커 컨테이너(시작/종료/재시작)와 팰월드 공식 REST API(상태/접속자/공지/저장)를 감싼다.
    예전 screen + PID 파일 방식은 도커 전환으로 대체됨.
    '''
    def __init__(self):
        self.container = os.getenv("PAL_CONTAINER", "palworld")
        self.api_url = os.getenv("PAL_API_URL", "http://palworld:8212").rstrip("/")
        self.api_auth = aiohttp.BasicAuth(
            os.getenv("PAL_API_USER", "admin"),
            os.getenv("PAL_API_PASSWORD", ""),
        )
        self.address = os.getenv("PAL_ADDRESS", "pal.moon-core.com:8211")

    # ── 도커 제어 ──────────────────────────────────────────
    async def _docker(self, *args):
        proc = await asyncio.create_subprocess_exec(
            "docker", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
        return proc.returncode, out.decode().strip()

    async def container_running(self):
        '''컨테이너가 실행 중이면 True, 꺼져 있으면 False, 존재하지 않으면 None.'''
        code, out = await self._docker("inspect", "-f", "{{.State.Running}}", self.container)
        if code != 0:
            return None
        return out == "true"

    async def start(self):
        return await self._docker("start", self.container)

    async def stop(self):
        return await self._docker("stop", self.container)

    async def restart(self):
        return await self._docker("restart", self.container)

    # ── REST API ──────────────────────────────────────────
    async def _api(self, method, path, payload=None):
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout, auth=self.api_auth) as session:
            async with session.request(method, f"{self.api_url}{path}", json=payload) as resp:
                resp.raise_for_status()
                if "application/json" in resp.headers.get("Content-Type", ""):
                    return await resp.json()
                return await resp.text()

    async def info(self):
        '''서버 이름, 게임 버전 등.'''
        return await self._api("GET", "/v1/api/info")

    async def metrics(self):
        '''FPS, 접속자 수, 업타임(초) 등.'''
        return await self._api("GET", "/v1/api/metrics")

    async def players(self):
        '''현재 접속자 목록. [{name, level, ping, ...}]'''
        data = await self._api("GET", "/v1/api/players")
        return data.get("players", [])

    async def announce(self, message):
        '''인게임 전체 공지.'''
        return await self._api("POST", "/v1/api/announce", {"message": message})

    async def save(self):
        '''월드 수동 저장.'''
        return await self._api("POST", "/v1/api/save")

    async def alive(self):
        '''게임 서버가 실제로 응답하는지 (컨테이너 생존과 별개).'''
        try:
            await self.metrics()
            return True
        except Exception:
            return False

    @staticmethod
    def format_uptime(seconds):
        seconds = int(seconds)
        hours, rest = divmod(seconds, 3600)
        minutes = rest // 60
        if hours:
            return f"{hours}시간 {minutes}분"
        return f"{minutes}분 {seconds % 60}초"
