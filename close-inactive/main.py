import json
import time
from google.cloud import monitoring_v3, compute_v1
from mcstatus import JavaServer
from google.auth import compute_engine
import datetime



PROJECT_ID = "noble-cubist-452902-i2"
ZONE = "asia-northeast3-c"
INSTANCE_NAME = "minecraft"
METRIC_TYPE = "custom.googleapis.com/minecraft/players_count"

monitoring_client = monitoring_v3.MetricServiceClient()
compute_client = compute_v1.InstancesClient()

def get_server_uptime():
    """Compute Engine의 서버 가동 시간(초)을 가져온다"""
    try:
        # url = "http://metadata.google.internal/computeMetadata/v1/instance/uptime"
        # headers = {"Metadata-Flavor": "Google"}
        # response = requests.get(url, headers=headers)
        # return int(response.text)  # 초 단위 uptime 반환
    
        compute_client = compute_v1.InstancesClient(credentials=compute_engine.Credentials())
        # Get the instance details
        instance = compute_client.get(project=PROJECT_ID, zone=ZONE, instance=INSTANCE_NAME)
        # Extract the start time of the instance (this is the boot time)
        start_time_str = instance.creation_timestamp  # The creation timestamp is the start time of the instance
        # Convert the start time to a datetime object
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        # Get the current time in UTC
        current_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        # Calculate uptime
        uptime = current_time - start_time
        
        return uptime.total_seconds()

    except Exception as e:
        print(f"❌ 서버 가동 시간 가져오기 실패: {e}")
        return None

def check_players(request):
    """Cloud Function이 실행될 때 마인크래프트 서버의 플레이어 수를 확인하고 기록"""
    server = JavaServer.lookup("mc.catiscute.o-r.kr")

    try:
        status = server.status()
        player_count = status.players.online
    except:
        player_count = 0

    # Cloud Monitoring에 플레이어 수 기록
    record_metric(player_count)


    # 서버 가동 시간 확인
    uptime_seconds = get_server_uptime()
    if uptime_seconds is not None and uptime_seconds < 300:  # 5분(300초) 미만이면 종료하지 않음
        print(f"🚀 서버가 켜진 지 {uptime_seconds}초밖에 안 됨. 종료 로직 무시!")
        return "Ignoring shutdown, server just started.", 200

    # 15분 동안 접속자가 없으면 서버 종료
    if player_count == 0:
        stop_instance()

    return json.dumps({"players": player_count}), 200

def record_metric(player_count):
    """Cloud Monitoring에 Custom Metric을 기록"""
    
    # TimeSeries 객체 생성
    series = monitoring_v3.TimeSeries()
    series.metric.type = METRIC_TYPE
    series.resource.type = "global"

    # 측정값(Point) 추가 (수정된 코드)
    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10**9)
    interval = monitoring_v3.TimeInterval({"end_time": {"seconds": seconds, "nanos": nanos}})
    point = monitoring_v3.Point({"interval": interval, "value": {"int64_value": player_count}})

    series.points = [point]

    monitoring_client.create_time_series(name=f"projects/{PROJECT_ID}", time_series=[series])

    print(f"✅ Custom Metric '{METRIC_TYPE}' 기록 완료: {player_count}명 접속 중")

    monitoring_client.create_time_series(name=f"projects/{PROJECT_ID}", time_series=[series])

def stop_instance():
    """GCP VM 인스턴스를 종료"""
    compute_client.stop(project=PROJECT_ID, zone=ZONE, instance=INSTANCE_NAME)
    print(f"Stopping instance: {INSTANCE_NAME}")