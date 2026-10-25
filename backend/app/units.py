"""Unit helpers. Everything is stored and compared in centimetres."""

CM_PER_INCH = 2.54


def to_cm(value: float | None, unit: str = "cm") -> float | None:
    if value is None:
        return None
    return round(value * CM_PER_INCH, 2) if unit == "in" else float(value)


def body_to_cm(measurements: dict, unit: str = "cm") -> dict:
    return {k: to_cm(v, unit) for k, v in measurements.items() if v is not None and v > 0}
