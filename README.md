# arithmetic-encoder
 - Fully bayesian algorithm for lowercase text compression as described in Mackay's "Information Theory, Inference, and Learning Algorithms".

# Usage
```python
from arithmetic_code import compress, decompress

bits = compress("hello")
text = decompress(bits)
```

## Tests
```powershell
python -m unittest
```

Test suite uses deterministic random cases so failures are repeatable.

## Notes
- `prefix.py` contains a small prefix-code helper.
- `inverter.py` contains a modular inverse helper.