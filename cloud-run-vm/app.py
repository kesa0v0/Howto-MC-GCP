from flask import Flask, request
import google.auth
from googleapiclient.discovery import build

app = Flask(__name__)

# GCP 프로젝트 정보
PROJECT_ID = "noble-cubist-452902-i2"
ZONE = "asia-northeast3-c"
INSTANCE_NAME = "minecraft"

# GCP 인증
credentials, _ = google.auth.default()
compute = build('compute', 'v1', credentials=credentials)

@app.route("/", methods=["GET"])
def start_vm():
    try:
        # Compute Engine VM 시작
        compute.instances().start(
            project=PROJECT_ID,
            zone=ZONE,
            instance=INSTANCE_NAME
        ).execute()
        
        return "<h1>✅ VM이 시작되었습니다!</h1><p>잠시만 기다려 주세요.</p>", 200
    except Exception as e:
        return f"<h1>❌ 오류 발생!</h1><p>{str(e)}</p>", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)