# Python 기반 이미지 사용
FROM python:3.9

# 작업 디렉터리 설정
WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt requirements.txt
COPY app.py app.py

# 패키지 설치
RUN pip install -r requirements.txt

# 서버 실행
CMD ["python", "app.py"]
