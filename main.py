# main.py
# OTA로 갱신되는 실제 작업 파일 (GitHub에도 이 내용 그대로 push)
# 실행 시작하자마자 텔레그램 1회 발송 + 이후 5분마다 반복 발송 (테스트용)

import time
import wifi
import ota
from telegram import send_telegram_message

HEARTBEAT_INTERVAL = 300        # 하트비트 주기 (초) - 테스트용, 5분
UPDATE_CHECK_INTERVAL = 1800    # 깃허브 업데이트 재확인 주기 (초) - 30분
LOOP_TICK = 5                   # 메인 루프 체크 간격 (초)


def main():
    wlan = wifi.connect_wifi()  # 이미 연결돼 있으면 바로 통과됨

    print("main.py 실행 시작")
    send_telegram_message("🚀 main.py 실행 시작 (다운로드+기동 정상)")

    last_heartbeat = time.time()
    last_update_check = time.time()

    while True:
        if not wlan.isconnected():
            wlan = wifi.connect_wifi()

        now = time.time()

        if now - last_heartbeat >= HEARTBEAT_INTERVAL:
            if send_telegram_message("나 살아있어요! 🟢 (테스트 하트비트)"):
                print("하트비트 전송 완료 ✅")
            else:
                print("하트비트 전송 실패")
            last_heartbeat = now

        if now - last_update_check >= UPDATE_CHECK_INTERVAL:
            ota.check_update()   # 새 버전 있으면 여기서 알아서 재부팅됨
            last_update_check = now

        time.sleep(LOOP_TICK)


main()
