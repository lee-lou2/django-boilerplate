import random
import string

CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
BASE = 62


def generate_random_key():
    """랜덤 키 생성"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=4))


def id_to_key(idx: int):
    """ShortId to ShortKey"""
    if idx < 1:
        return None
    key = []
    while idx > 0:
        idx -= 1
        digit = idx % BASE
        key.append(CHARS[digit])
        idx //= BASE
    key.reverse()
    return "".join(key)


def key_to_id(key: str):
    """ShotKey to ShortId"""
    result = 0
    for c in key:
        digit = CHARS.find(c)
        if digit == -1:
            return None
        result = result * BASE + (digit + 1)
    return result
