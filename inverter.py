from math import gcd


def inverse(value, modulus=11):
    """Return the modular inverse of ``value`` under ``modulus``."""
    if modulus <= 1:
        raise ValueError("modulus must be greater than 1")

    value %= modulus
    if gcd(value, modulus) != 1:
        raise ValueError(f"{value} has no inverse modulo {modulus}")

    return pow(value, -1, modulus)