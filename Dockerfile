# Python 3.10을 기반으로 하는 공식 이미지를 사용합니다.
FROM python:3.14-slim

# 파이썬이 로그를 버퍼링 없이 즉시 출력하도록 환경 변수를 설정합니다.
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

# --- 폰트 설치 과정 추가 ---

# 1. 시스템 패키지 목록을 업데이트하고, 폰트 관리 도구(fontconfig)를 설치합니다.
#    설치 후에는 이미지 용량을 줄이기 위해 불필요한 캐시를 삭제합니다.
RUN apt-get update && \
    apt-get install -y fontconfig && \
    rm -rf /var/lib/apt/lists/*

# 2. 로컬에 준비한 fonts 폴더를 컨테이너의 시스템 폰트 폴더로 복사합니다.
COPY fonts/ /usr/share/fonts/truetype/malgun/

# 3. 시스템이 새 폰트를 인식하도록 폰트 캐시를 다시 빌드합니다.
RUN fc-cache -f -v

# --- 폰트 설치 종료 ---

# 의존성 파일을 복사하고 설치합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 소스 코드를 복사합니다.
COPY . .

# 봇을 실행하는 기본 명령어를 설정합니다.
CMD ["python", "-u", "bot.py"]