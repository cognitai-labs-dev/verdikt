import secrets


def random_int(a: int = 1, b: int = 1000) -> int:
    return secrets.choice(range(a, b))
