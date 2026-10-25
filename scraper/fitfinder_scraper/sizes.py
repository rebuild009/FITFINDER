"""Size labels: normalise what stores write ("XX-Large", "2XL", "32/34") into one vocabulary."""

from __future__ import annotations

import re

WORDS = {
    "xxs": "XXS", "xs": "XS", "s": "S", "small": "S", "m": "M", "medium": "M", "l": "L", "large": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL",
}


def normalise(label: str) -> str:
    raw = label.strip()
    low = raw.lower().replace("–", "-")
    if low in WORDS:
        return WORDS[low]
    m = re.fullmatch(r"(x+)-?(?:l|large)", low)
    if m:
        n = len(m.group(1))
        return "XL" if n == 1 else f"{n}XL"
    m = re.fullmatch(r"(\d)\s*-?\s*x\s*-?\s*(?:l|large)", low)
    if m:
        return f"{m.group(1)}XL"
    m = re.fullmatch(r"uk\s*-?\s*(\d{1,2})", low)
    if m:
        return f"UK {m.group(1)}"
    return raw.upper()


def waist_inseam(label: str) -> tuple[int | None, int | None]:
    """'32', '32/34', 'W32 L34', '32x34' -> (waist, inseam) in inches."""
    nums = [int(n) for n in re.findall(r"\d{2}", label)]
    if not nums or not 22 <= nums[0] <= 64:
        return None, None
    inseam = nums[1] if len(nums) > 1 and 24 <= nums[1] <= 40 else None
    return nums[0], inseam
