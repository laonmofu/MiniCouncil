# Python 3.10을 기반으로 하는 공식 이미지를 사용합니다.
FROM python:3.14-slim

# 파이썬이 로그를 버퍼링 없이 즉시 출력하도록 환경 변수를 설정합니다.
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 소스 코드를 복사합니다.
COPY . .

# 봇을 실행하는 기본 명령어를 설정합니다.
CMD ["python", "-u", "bot.py"]