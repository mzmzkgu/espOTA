# main.py
# OTA로 갱신되는 실제 작업 파일 (GitHub에도 이 내용 그대로 push)
#
# ============================================================
# ▼▼▼ OTA 필수 헤더 (앞으로 이 블록은 절대 지우거나 순서 바꾸지 말 것) ▼▼▼
# ============================================================
import time
import random
import ntptime
import wifi
import ota
import urequests
from telegram import send_telegram_message

HEARTBEAT_INTERVAL = 300     # 하트비트 주기 (초)
LOOP_TICK = 5                # 메인 루프 체크 간격 (초)

# ── 포트폴리오 랜덤 순회 체크 설정 ──
BASE_URL = "https://harna0910.tistory.com"  # /1 ~ /50 붙여서 접속
CYCLE_START = 1
CYCLE_END = 50
INTERVAL_MIN = 60     # 다음 체크까지 최소 간격 (초) - 1분
INTERVAL_MAX = 300    # 다음 체크까지 최대 간격 (초) - 5분
REST_INTERVAL = 3000  # 한 사이클(1~50) 다 돌고 난 뒤 쉬는 시간 (초) - 1시간


def sync_time():
    # ntptime은 UTC 기준으로 ESP32의 내부 시계(RTC)를 맞춰줌
    # 한국시간(KST)은 UTC+9라서 "분(minute)"은 그대로 같이 쓸 수 있음 (분 단위 오프셋 없음)
    try:
        ntptime.settime()
        print("NTP 시간 동기화 완료:", time.localtime())
    except Exception as e:
        print("NTP 동기화 실패:", e)


def check_portfolio(url):
    # 포트폴리오 페이지 하나에 접속해보고 확인
    # 성공은 조용히 로그만 남기고(텔레그램 스팸 방지), 실패했을 때만 알림
    try:
        res = urequests.get(url)
        status = res.status_code
        res.close()
        if 200 <= status < 400:
            print("정상 ({}) - {}".format(status, url))
        else:
            send_telegram_message("⚠️ 상태코드 이상 ({}) - {}".format(status, url))
            print("상태코드 이상 - status:", status, url)
    except Exception as e:
        send_telegram_message("❌ 접속 실패! - {}".format(url))
        print("접속 실패:", e, url)


wlan = wifi.connect_wifi()
sync_time()

print("main.py 실행 시작")
send_telegram_message("🚀 main.py 실행 시작 (다운로드+기동 정상)")

last_heartbeat = time.time()
last_checked_hour = -1   # 이번에 이미 체크한 "시(hour)"를 기억해서 정각마다 딱 한 번만 실행

# 포트폴리오 순회 체크용 상태값
current_portfolio = CYCLE_START
next_portfolio_check = time.time()   # 부팅하면 1번부터 바로 시작
resting = False
rest_until = 0
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

    # 5분마다 하트비트
    if now - last_heartbeat >= HEARTBEAT_INTERVAL:
        if send_telegram_message("나 잘 살아있어! 🟢"):
            print("하트비트 전송 완료 ✅")
        else:
            print("하트비트 전송 실패")
        last_heartbeat = now

"""
    # 포트폴리오 1~50 랜덤 간격(1~5분) 순회 체크
    if resting:
        if now >= rest_until:
            resting = False
            current_portfolio = CYCLE_START
            next_portfolio_check = now  # 쉬고 나서 바로 1번부터 재시작
    else:
        if now >= next_portfolio_check:
            url = "{}/{}".format(BASE_URL, current_portfolio)
            check_portfolio(url)
            if current_portfolio >= CYCLE_END:
                send_telegram_message("🎉 1사이클 다 돌렸어! (1시간 쉬었다가 다시 시작할게)")
                resting = True
                rest_until = now + REST_INTERVAL
            else:
                current_portfolio += 1
                next_portfolio_check = now + random.randint(INTERVAL_MIN, INTERVAL_MAX)
"""

    # 매 정각(N시 00분)마다 딱 한 번 - GitHub 업데이트 확인
    t = time.localtime()
    current_hour = t[3]
    current_minute = t[4]
    if current_minute == 0 and current_hour != last_checked_hour:
        print("정각 도달 - OTA 업데이트 확인")
        ota.check_update()   # 새 버전 있으면 여기서 알아서 다운로드+재부팅됨
        last_checked_hour = current_hour

    user_task()
    time.sleep(LOOP_TICK)
