"""
SY4000 register value calculators.

Formulas sourced from SY4000_v1809_EKSMA_OPTICS.pdf:
  - PLL2 N divider selection: Chapter 5.1.2 (External Clock configuration)
  - Delay/A-delay/D-delay:    Chapter 5.5 (Delay Generator Configuration)
"""

import math

ALLOWED_NDIV = [
    30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60,
    62, 64, 66, 68, 70, 72, 76, 78, 80, 84, 88, 90, 92, 96, 98, 100,
    102, 104, 108, 110, 112, 116, 120, 124,
]


def calc_pll2_ndiv(ext_freq_mhz: float):
    """
    Manual 5.1.2, steps 1-2.
    Returns (ndiv, f_sys_mhz, vco2_code) where vco2_code: 1=3GHz, 0=2.5GHz.
    Raises ValueError if no allowed Ndiv lands system clock in either
    valid band (2920..3080 MHz or 2370..2630 MHz).
    """
    # Step 1: try to hit 3000 MHz band
    ndiv_3g = min(ALLOWED_NDIV, key=lambda n: abs(n * ext_freq_mhz - 3000))
    f_3g = ndiv_3g * ext_freq_mhz
    if 2920 <= f_3g <= 3080:
        return ndiv_3g, f_3g, 1  # VCO2 = 3GHz

    # Step 2: fall back, try to hit 2500 MHz band
    ndiv_25g = min(ALLOWED_NDIV, key=lambda n: abs(n * ext_freq_mhz - 2500))
    f_25g = ndiv_25g * ext_freq_mhz
    if 2370 <= f_25g <= 2630:
        return ndiv_25g, f_25g, 0  # VCO2 = 2.5GHz

    raise ValueError(
        f"No allowed Ndiv puts system clock in a valid band for "
        f"{ext_freq_mhz} MHz external clock. "
        f"Closest attempts: Ndiv={ndiv_3g} -> {f_3g} MHz (3GHz band), "
        f"Ndiv={ndiv_25g} -> {f_25g} MHz (2.5GHz band)."
    )


def calc_delay_registers(time_s: float, f_sys_hz: float):
    """
    Manual 5.5 general formula. Returns (delay_counter, d_delay, a_delay)
    for one full-featured delay channel (0,1,2,3,5).

    Valid ranges (Table 20 / Table 16):
      delay_counter: 3 .. 16777218
      d_delay:       4 .. 32
      a_delay:       0 .. 23   (25 ps steps, 0..575 ps)
    """
    f28 = f_sys_hz / 28.0
    tcount = f28 * time_s

    delay_counter = math.floor(tcount)
    frac = tcount - delay_counter
    d_delay = int(frac * 28 + 4)
    a_delay = int((frac * 28 - math.floor(frac * 28)) * 13)

    if not (3 <= delay_counter <= 16777218):
        raise ValueError(f"delay_counter={delay_counter} out of range 3..16777218")
    if not (4 <= d_delay <= 32):
        raise ValueError(f"d_delay={d_delay} out of range 4..32")
    if not (0 <= a_delay <= 23):
        raise ValueError(f"a_delay={a_delay} out of range 0..23")

    return delay_counter, d_delay, a_delay


def calc_post_delay_counter(width_s: float, f_sys_hz: float):
    """
    Post-counter (Table 16 'Post delay counter X') is a plain cascade
    counter ticking at the same F/28 rate as the main delay counter --
    it starts once the delay counter finishes, and its count sets the
    generated pulse width.

    Valid range: 3 .. 258
    """
    f28 = f_sys_hz / 28.0
    postcnt = round(width_s * f28)
    if not (3 <= postcnt <= 258):
        raise ValueError(f"post_delay_counter={postcnt} out of range 3..258")
    return postcnt


def calc_ratediv(period_s: float, source_freq_hz: float):
    """
    Rate divider = desired trigger period / clock source period.
    source_freq_hz = 100e6 for Internal, or your external/SYNC IN freq
    depending on Mux Rate divider source register setting.

    Valid range: 1 .. 2147483647
    """
    source_period = 1.0 / source_freq_hz
    ratediv = round(period_s / source_period)
    if not (1 <= ratediv <= 2147483647):
        raise ValueError(f"ratediv={ratediv} out of range 1..2147483647")
    return ratediv

