import time


def time_str(timestamp: int = None) -> str:
    if timestamp is None:
        timestamp = time.time()
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def timezone_str() -> str:
    return "UTC" + ("-" if time.timezone > 0 else "+") + str(abs(time.timezone) // 3600)
