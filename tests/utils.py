import secrets
import string


def random_int(a: int = 1, b: int = 1000) -> int:
    return secrets.choice(range(a, b))


def random_word(length: int = 128) -> str:
    letters = string.ascii_lowercase
    return "".join(secrets.choice(letters) for _ in range(length))
