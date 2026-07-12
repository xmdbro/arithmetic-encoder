import random
import unittest

from arithmetic_code import ALPHABET, Interval, compress, decompress
from inverter import inverse
from prefix import prefix_code_for_lengths


RANDOM_SEED = 20260712


def make_rand_interval(rng):
    return make_rand_subinterval(rng, Interval(0, 1))


def make_rand_subinterval(rng, interval):
    start = rng.uniform(interval.start, interval.end)
    return Interval(start, rng.uniform(start, interval.end))


class ArithmeticCodeTest(unittest.TestCase):
    def check_txt(self, txt):
        compressed = compress(txt)
        self.assertEqual(
            decompress(compressed),
            txt,
            f"did not work for {txt!r}, which compressed to {compressed!r}",
        )

    def test_known_interval_bits(self):
        second_quarter = Interval(0.25, 0.5)
        self.assertEqual(second_quarter.to_bits(), "01")
        self.assertEqual(Interval.from_bits("01"), second_quarter)

    def test_empty_text(self):
        self.check_txt("")

    def test_single_letters_round_trip(self):
        for letter in ALPHABET:
            compressed = compress(letter)
            length = len(compressed)
            self.assertTrue(
                2 ** -length <= 1 / len(ALPHABET) <= 2 ** -(length - 2),
                f"{letter!r} compressed to {compressed!r}, which has length {length}",
            )
            self.assertEqual(decompress(compressed), letter)

    def test_random_text_round_trips(self):
        rng = random.Random(RANDOM_SEED)

        for _ in range(12):
            txt = "".join(rng.choice(ALPHABET) for _ in range(rng.randint(2, 300)))
            self.check_txt(txt)

    def test_bits_and_interval_properties(self):
        rng = random.Random(RANDOM_SEED)

        for _ in range(25):
            bits = "".join(rng.choice(["0", "1"]) for _ in range(rng.randint(2, 40)))
            self.assertEqual(bits, Interval.from_bits(bits).to_bits())

            interval = make_rand_interval(rng)
            interval_after_conversion = Interval.from_bits(interval.to_bits())
            self.assertTrue(interval.contains(interval_after_conversion))

            bits_for_interval, subinterval = interval.normalized()
            self.assertEqual(
                interval,
                Interval.from_bits(bits_for_interval).scale(subinterval),
            )

            other_interval = make_rand_subinterval(rng, interval)
            x = interval.unscale(other_interval)
            reconstructed_interval = interval.scale(x)
            self.assertAlmostEqual(other_interval.start, reconstructed_interval.start, places=5)
            self.assertAlmostEqual(other_interval.end, reconstructed_interval.end, places=5)

    def test_rejects_unsupported_text(self):
        with self.assertRaises(ValueError):
            compress("Hello")

    def test_rejects_non_binary_bits(self):
        with self.assertRaises(ValueError):
            decompress("01012")


class HelperModuleTest(unittest.TestCase):
    def test_modular_inverse(self):
        self.assertEqual(inverse(3), 4)
        self.assertEqual(inverse(3, 7), 5)

    def test_modular_inverse_rejects_non_coprime_value(self):
        with self.assertRaises(ValueError):
            inverse(2, 4)

    def test_prefix_code_does_not_mutate_lengths(self):
        lengths = [1, 2, 2]
        self.assertEqual(prefix_code_for_lengths(lengths), [(0, None), (0, (1, None)), (1, (1, None))])
        self.assertEqual(lengths, [1, 2, 2])

    def test_prefix_code_rejects_invalid_lengths(self):
        with self.assertRaises(ValueError):
            prefix_code_for_lengths([1, 1, 1])

        with self.assertRaises(ValueError):
            prefix_code_for_lengths([0])


if __name__ == "__main__":
    unittest.main()