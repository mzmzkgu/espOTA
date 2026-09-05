import time
import ota

last_check = time.ticks_ms()
CHECK_INTERVAL = 3600_000  # 1시간마다 (밀리초 단위)

while True:
    # ... 평소 하던 작업 (매매 로직 등) ...

    if time.ticks_diff(time.ticks_ms(), last_check) > CHECK_INTERVAL:
        ota.check_update()  # 업데이트 있으면 여기서 알아서 재부팅됨
        last_check = time.ticks_ms()
