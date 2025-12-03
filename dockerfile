# 베이스 이미지
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치 (MongoDB 클라이언트 포함)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add - \
    && echo "deb http://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list \
    && apt-get update \
    && apt-get install -y mongodb-mongosh \
    && rm -rf /var/lib/apt/lists/*

# 필요한 파일 복사
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 스크립트 실행 권한 부여
RUN chmod +x init-db.sh

# Flask 환경변수 설정
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080

# 컨테이너 시작 시 마이그레이션 후 Flask 실행
CMD ["./init-db.sh"]
