# 베이스 이미지 (python 최신 버전)
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Flask 환경변수 설정
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0

# 컨테이너 시작 시 실행할 명령
CMD ["flask", "run"]
