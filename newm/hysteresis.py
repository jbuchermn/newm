import math

class Hysteresis:
    def __init__(self, amount, initial_value):
        self._amount = amount
        self._at = round(initial_value)

    def __call__(self, value):
        i, j = math.floor(value), math.ceil(value)
        if self._at != i and self._at != j:
            self._at = round(value)

        di, dj = abs(value - i), abs(value - j)
        if di + self._amount < dj and self._at == j:
            self._at = i

        if dj + self._amount < di and self._at == i:
            self._at = j

        return self._at


if __name__ == '__main__':
    h = Hysteresis(0.2, 0)
    for v in [0.5, 0.7, 1.0, 1.2, 1.5, 1.3, 1.5, 1.7, 1.5]:
        print(v, h(v))
