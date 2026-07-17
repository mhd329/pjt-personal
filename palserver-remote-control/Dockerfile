FROM python:3.12-alpine

# 팰월드 컨테이너 제어용 도커 CLI (데몬은 호스트 소켓 사용)
RUN apk add --no-cache docker-cli

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY Bot/ Bot/
COPY Log/ Log/
COPY images/ images/

CMD ["python", "-u", "main.py"]
