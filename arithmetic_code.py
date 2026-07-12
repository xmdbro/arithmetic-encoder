from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import ceil, log
from string import ascii_lowercase
from typing import Final, Iterable


ALPHABET: Final[tuple[str, ...]] = tuple(ascii_lowercase)
HALF: Final = 0.5
FLOAT_TOLERANCE: Final = 1e-9


@dataclass
class AdaptiveModel:
    """Laplace-smoothed character model over lowercase ASCII letters."""

    counts: Counter[str]
    total_symbols: int = 0

    @classmethod
    def empty(cls) -> "AdaptiveModel":
        return cls(Counter())

    def observe(self, symbol: str) -> None:
        validate_symbol(symbol)
        self.counts[symbol] += 1
        self.total_symbols += 1

    def probability(self, symbol: str) -> float:
        validate_symbol(symbol)
        return (self.counts[symbol] + 1) / (self.total_symbols + len(ALPHABET))

    def intervals(self) -> Iterable[tuple[str, "Interval"]]:
        lower_bound = 0.0

        for symbol in ALPHABET:
            upper_bound = lower_bound + self.probability(symbol)
            if upper_bound - 1.0 > FLOAT_TOLERANCE:
                raise ArithmeticError(f"probability interval exceeded 1.0: {upper_bound}")

            yield symbol, Interval(lower_bound, min(1.0, upper_bound))
            lower_bound = upper_bound


@dataclass(frozen=True, slots=True)
class Interval:
    """A half-open numeric interval used by the arithmetic coder."""

    start: float
    end: float

    def __post_init__(self) -> None:
        if not 0 <= self.start <= self.end <= 1:
            raise ValueError(f"invalid interval bounds: {self.start}, {self.end}")

    @property
    def size(self) -> float:
        return self.end - self.start

    def contains(self, other: "Interval") -> bool:
        return self.start <= other.start and self.end >= other.end

    def scale(self, subinterval: "Interval") -> "Interval":
        start = self.start + self.size * subinterval.start
        end = start + self.size * subinterval.size
        return Interval(start, end)

    def unscale(self, interval: "Interval") -> "Interval":
        if not self.contains(interval):
            raise ValueError(f"{interval} is not contained by {self}")

        start = (interval.start - self.start) / self.size
        end = start + interval.size / self.size
        return Interval(start, end)

    def normalized(self) -> tuple[str, "Interval"]:
        """Extract stable leading bits and return the remaining interval."""
        bits = ""
        interval = self

        while interval.start >= HALF or interval.end <= HALF:
            if interval.start >= HALF:
                bits += "1"
                interval = ONE_BIT_INTERVAL.unscale(interval)
            else:
                bits += "0"
                interval = ZERO_BIT_INTERVAL.unscale(interval)

        return bits, interval

    def to_bits(self) -> str:
        """Return finite bits whose binary interval fits inside this interval."""
        bits, interval = self.normalized()

        if interval.size == 1:
            return bits

        distance_to_upper_half = interval.end - HALF
        distance_to_lower_half = HALF - interval.start

        if distance_to_upper_half > distance_to_lower_half:
            bits += "1"
            bits += "0" * (ceil(-log(distance_to_upper_half, 2)) - 1)
            return bits

        bits += "0"
        added_value = 0.0
        bit_position = 2

        while added_value < interval.start:
            added_value += 2**-bit_position
            bits += "1"
            bit_position += 1

        return bits

    @classmethod
    def from_bits(cls, bits: str) -> "Interval":
        validate_bits(bits)
        start = sum(int(bit) * 2 ** -(index + 1) for index, bit in enumerate(bits))
        return cls(start, start + 2 ** -len(bits))


def compress(text: str) -> str:
    """Compress lowercase ASCII text into a binary string."""
    validate_text(text)

    model = AdaptiveModel.empty()
    encoded_bits = ""
    pending_interval = Interval(0, 1)

    for symbol in text:
        symbol_interval = interval_for_symbol(symbol, model)
        pending_interval = pending_interval.scale(symbol_interval)
        stable_bits, pending_interval = pending_interval.normalized()
        encoded_bits += stable_bits
        model.observe(symbol)

    return encoded_bits + pending_interval.to_bits()


def decompress(bits: str) -> str:
    """Decompress a binary string produced by ``compress``."""
    validate_bits(bits)

    model = AdaptiveModel.empty()
    decoded_text = ""
    pending_interval = Interval(0, 1)
    remaining_bits_start = 0
    remaining_interval = Interval.from_bits(bits)

    while True:
        decoded_symbol = None

        for symbol, symbol_interval in model.intervals():
            candidate_interval = pending_interval.scale(symbol_interval)
            if candidate_interval.contains(remaining_interval):
                decoded_symbol = symbol
                stable_bits, pending_interval = candidate_interval.normalized()
                remaining_bits_start += len(stable_bits)
                remaining_interval = Interval.from_bits(bits[remaining_bits_start:])
                break

        if decoded_symbol is None:
            return decoded_text

        decoded_text += decoded_symbol
        model.observe(decoded_symbol)


def interval_for_symbol(symbol: str, model: AdaptiveModel) -> Interval:
    validate_symbol(symbol)

    for candidate_symbol, interval in model.intervals():
        if candidate_symbol == symbol:
            return interval

    raise ValueError(f"unsupported symbol: {symbol!r}")


def validate_text(text: str) -> None:
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    unsupported_symbols = sorted(set(text) - set(ALPHABET))
    if unsupported_symbols:
        raise ValueError(
            f"text can only contain lowercase a-z characters; found {unsupported_symbols!r}"
        )


def validate_symbol(symbol: str) -> None:
    if symbol not in ALPHABET:
        raise ValueError(f"symbol must be one lowercase a-z character: {symbol!r}")


def validate_bits(bits: str) -> None:
    if not isinstance(bits, str):
        raise TypeError("bits must be a string")

    unsupported_bits = sorted(set(bits) - {"0", "1"})
    if unsupported_bits:
        raise ValueError(f"bits can only contain '0' and '1'; found {unsupported_bits!r}")


ZERO_BIT_INTERVAL: Final = Interval.from_bits("0")
ONE_BIT_INTERVAL: Final = Interval.from_bits("1")