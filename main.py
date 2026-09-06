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

HEARTBEAT_INTERVAL = 1800   # 테스트용 하트비트 주기 (초) - 필요 없어지면 지워도 됨
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


def is_prime(n):
    # 시행 나눗셈(trial division) 방식 소수 판별 - sqrt(n)까지만 확인
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def kst_timestamp():
    # ntptime이 맞춘 RTC는 UTC 기준이라, 표시용으로 +9시간 해서 KST로 변환
    t = time.localtime(time.time() + 9 * 3600)
    return "%02d%02d%02d %02d:%02d" % (t[0] % 100, t[1], t[2], t[3], t[4])


def lucas_lehmer(p):
    # p가 소수일 때만 의미 있는 테스트 (p가 합성수면 2^p-1은 항상 합성수라 애초에 호출 안 함)
    # M = 2^p - 1 이 소수인지 뤼카-레머 방식으로 판별
    if p == 2:
        return True   # 2^2-1 = 3 은 예외적으로 소수 (테스트 공식이 p>=3부터 적용됨)
    m = (1 << p) - 1
    s = 4
    for _ in range(p - 2):
        s = (s * s - 2) % m
    return s == 0


_next_candidate = 2       # 다음에 검사할 숫자 (2부터 시작, 재부팅/OTA 갱신되면 다시 2부터)
_prime_count = 0          # 지금까지 찾은 소수 누적 개수 (재부팅/OTA 갱신되면 다시 0부터)
_mersenne_count = 0       # 지금까지 찾은 메르센 소수 누적 개수 (재부팅/OTA 갱신되면 다시 0부터)
_CHECKS_PER_TICK = 300    # user_task() 한 번 호출당 검사할 후보 개수
                          # (너무 크게 잡으면 하트비트/OTA 체크가 밀릴 수 있어서 적당히 제한)


def user_task():
    # ------------------------------------------------------
    # 여기 아래에 실제 하고 싶은 작업(매매 로직, 센서 읽기 등) 작성
    # 이 함수 안쪽은 자유롭게 고쳐도 OTA 동작에는 영향 없음
    # ------------------------------------------------------
    global _next_candidate, _prime_count, _mersenne_count

    checked = 0
    while checked < _CHECKS_PER_TICK:
        if is_prime(_next_candidate):
            _prime_count += 1
            # 일반 소수는 텔레그램 전송 없이 콘솔에만 출력 (메르센 소수처럼 특별한 경우만 알림)
            print("(%s) 소수 : %d (%d번째)" % (kst_timestamp(), _next_candidate, _prime_count))

            # p가 소수로 확인된 경우에만 2^p-1(메르센 수)도 소수인지 뤼카-레머 테스트로 확인
            if lucas_lehmer(_next_candidate):
                _mersenne_count += 1
                exp = _next_candidate
                if exp <= 200:
                    value_str = str((1 << exp) - 1)
                else:
                    # 자릿수가 너무 길어지면(텔레그램 메시지가 지저분해짐) 값 대신 자릿수만 표시
                    digit_count = int(exp * 0.30103) + 1
                    value_str = "(%d자리 숫자, 생략)" % digit_count
                mmsg = "(%s) 메르센 소수 발견 : 2^%d-1 = %s (%d번째 메르센 소수)" % (
                    kst_timestamp(), exp, value_str, _mersenne_count)
                send_telegram_message(mmsg)
                print(mmsg)
                time.sleep(0.3)
        _next_candidate += 1
        checked += 1


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
