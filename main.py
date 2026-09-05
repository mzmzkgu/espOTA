# main.py
# OTA로 갱신되는 실제 작업 파일 (GitHub에도 이 내용 그대로 push)
#
# ============================================================
# ▼▼▼ OTA 필수 헤더 (앞으로 이 블록은 절대 지우거나 순서 바꾸지 말 것) ▼▼▼
# ============================================================
import time
import ntptime
import wifi
import ota
from telegram import send_telegram_message

HEARTBEAT_INTERVAL = 300   # 테스트용 하트비트 주기 (초) - 필요 없어지면 지워도 됨
LOOP_TICK = 5              # 메인 루프 체크 간격 (초) - 너무 크면 정각 체크를 놓칠 수 있음


def sync_time():
    # ntptime은 UTC 기준으로 ESP32의 내부 시계(RTC)를 맞춰줌
    # 한국시간(KST)은 UTC+9라서 "분(minute)"은 그대로 같이 쓸 수 있음 (분 단위 오프셋 없음)
    try:
        ntptime.settime()
        print("NTP 시간 동기화 완료:", time.localtime())
    except Exception as e:
        print("NTP 동기화 실패:", e)


wlan = wifi.connect_wifi()
sync_time()

print("main.py 실행 시작")
send_telegram_message("🚀 main.py 실행 시작 (다운로드+기동 정상)")

last_heartbeat = time.time()
last_checked_hour = -1   # 이번에 이미 체크한 "시(hour)"를 기억해서 정각마다 딱 한 번만 실행
# ============================================================
# ▲▲▲ 필수 헤더 끝 ▲▲▲
# ============================================================


def user_task():
    # ------------------------------------------------------
    # 여기 아래에 실제 하고 싶은 작업(매매 로직, 센서 읽기 등) 작성
    # 이 함수 안쪽은 자유롭게 고쳐도 OTA 동작에는 영향 없음
    # ------------------------------------------------------
    pass


while True:
    if not wlan.isconnected():
        wlan = wifi.connect_wifi()

    now = time.time()

    # 5분마다 테스트 하트비트
    if now - last_heartbeat >= HEARTBEAT_INTERVAL:
        if send_telegram_message("나 살아있어요! 🟢 (테스트 하트비트)"):
            print("하트비트 전송 완료 ✅")
        else:
            print("하트비트 전송 실패")
        last_heartbeat = now

    # 매 정각(N시 00분)마다 딱 한 번 GitHub 업데이트 확인
    t = time.localtime()
    current_hour = t[3]
    current_minute = t[4]
    if current_minute == 0 and current_hour != last_checked_hour:
        print("정각 도달 - OTA 업데이트 확인")
        ota.check_update()   # 새 버전 있으면 여기서 알아서 다운로드+재부팅됨
        last_checked_hour = current_hour

    user_task()
    time.sleep(LOOP_TICK)
