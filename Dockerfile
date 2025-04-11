# 1단계: 베이스 이미지 설정
FROM python:3.12-slim

# 2단계: 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3단계: 작업 디렉토리 설정
WORKDIR /app

# 4단계: 시스템 의존성 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 5단계: Python 의존성 설치
COPY requirements.txt .

# pip를 최신 버전으로 업그레이드하고 requirements.txt에 명시된 패키지를 설치합니다.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6단계: 애플리케이션 코드 복사
COPY src .

# 7단계: (선택 사항) 정적 파일 수집 (필요한 경우)
# RUN python manage.py collectstatic --noinput

# 8단계: (선택 사항) 데이터베이스 마이그레이션
# RUN python manage.py migrate

# 9단계: 보안 강화를 위해 non-root 사용자 생성 및 사용
RUN addgroup --system app && adduser --system --ingroup app app
# 코드 디렉토리 소유권 변경
RUN chown -R app:app /app
# 사용자를 app으로 전환
USER app

# 10단계: 노출할 포트 설정
EXPOSE 8000

# 11단계: 컨테이너 실행 시 애플리케이션 서버 실행
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "conf.wsgi:application", "--workers", "3", "--threads", "2"]