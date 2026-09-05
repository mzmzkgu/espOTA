import network
import time
import urequests
import machine

# ===== Wi-Fi 설정 (직접 입력) =====
WIFI_SSID = "U+Net85A4"
WIFI_PASSWORD = "#1B5D8K7C5"

# ===== 텔레그램 설정 (직접 입력) =====
TELEGRAM_TOKEN = "7374884684:AAFOml2hv_OH7i28Wb9YfH7e0sYM8LMyftQ"
CHAT_ID = "5111593257"

# ===== 주기 설정 (초 단위) =====
HEARTBEAT_INTERVAL = 300        # 생존 신고 주기 (기본 5분)
UPDATE_CHECK_INTERVAL = 1800    # 깃허브 업데이트 확인 주기 (기본 30분)
LOOP_TICK = 5                   # 메인 루프 체크 간격

# ===== 깃허브 OTA 설정 (직접 입력) =====
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/mzmzkgu/espOTA/main/version.txt"
GITHUB_MAIN_URL = "https://raw.githubusercontent.com/mzmzkgu/espOTA/main/main.py"
LOCAL_VERSION_FILE = "version.txt"


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Wi-Fi 연결 중...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        print("Wi-Fi 연결됨:", wlan.ifconfig())
    return wlan


def send_telegram_message(text):
    url = "https://api.telegram.org/bot{}/sendMessage".format(TELEGRAM_TOKEN)
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        res = urequests.post(url, json=payload)
        res.close()
        return True
    except Exception as e:
        print("메시지 전송 실패:", e)
        return False


def get_local_version():
    try:
        with open(LOCAL_VERSION_FILE) as f:
            return f.read().strip()
    except Exception:
        return "0"


def check_for_update():
    print("깃허브 업데이트 확인 중...")
    try:
        res = urequests.get(GITHUB_VERSION_URL)
        remote_version = res.text.strip()
        res.close()
    except Exception as e:
        print("버전 확인 실패:", e)
        return

    local_version = get_local_version()

    if remote_version == local_version:
        print("최신 버전입니다. (현재: {})".format(local_version))
        return

    print("새 버전 발견: {} -> {}".format(local_version, remote_version))
    try:
        res = urequests.get(GITHUB_MAIN_URL)
        new_code = res.text
        res.close()

        with open("main.py", "w") as f:
            f.write(new_code)
        with open(LOCAL_VERSION_FILE, "w") as f:
            f.write(remote_version)

        send_telegram_message(
            "업데이트 완료! {} -> {} 재부팅합니다 🔄".format(local_version, remote_version)
        )
        time.sleep(2)
        machine.reset()
    except Exception as e:
        print("업데이트 다운로드/적용 실패:", e)


def main():
    wlan = connect_wifi()
    print("OTA 생존 신고 + 자동 업데이트 확인 시작")

    check_for_update()  # 부팅 직후 한 번 확인

    last_heartbeat = time.time()
    last_update_check = time.time()

    while True:
        if not wlan.isconnected():
            wlan = connect_wifi()

        now = time.time()

        if now - last_heartbeat >= HEARTBEAT_INTERVAL:
            if send_telegram_message("나 살아있어요! 🟢"):
                print("하트비트 전송 완료 ✅")
            else:
                print("하트비트 전송 실패")
            last_heartbeat = now

        if now - last_update_check >= UPDATE_CHECK_INTERVAL:
            check_for_update()
            last_update_check = now

        time.sleep(LOOP_TICK)


main()
