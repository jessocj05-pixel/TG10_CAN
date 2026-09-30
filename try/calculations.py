"""Pure calc fns for SY4000. No reg I/O, no CAN calls — in/out only."""

# ---------- PARSING (for GUI/text input) ----------

def parse_time(t) -> float:
    """ '250ns' / '1us' / '10ms' / '2s' -> seconds. Raw number = assumed seconds. """
    if isinstance(t, (int, float)):
        return float(t)
    t = str(t).strip().lower().replace(" ", "")
    if t.endswith("ns"): return float(t[:-2]) * 1e-9
    if t.endswith(("us", "µs")): return float(t[:-2]) * 1e-6
    if t.endswith("ms"): return float(t[:-2]) * 1e-3
    if t.endswith("s"): return float(t[:-1])
    raise ValueError(f"cannot parse time: {t!r}")


def parse_freq(f) -> float:
    """ '20MHz' / '100kHz' / '1Hz' -> Hz. Raw number = assumed Hz. """
    if isinstance(f, (int, float)):
        return float(f)
    f = str(f).strip().lower().replace(" ", "")
    if f.endswith("ghz"): return float(f[:-3]) * 1e9
    if f.endswith("mhz"): return float(f[:-3]) * 1e6
    if f.endswith("khz"): return float(f[:-3]) * 1e3
    if f.endswith("hz"): return float(f[:-2])
    raise ValueError(f"cannot parse freq: {f!r}")


# ---------- CENTRAL REGISTER RANGES (Table 20 / Table 1, doc-verified) ----------

RANGES = {
    "ext_clock_hz":     (20e6, 100e6),
    "osc_clock_mhz":    (10, 100),
    "sysclk_3ghz_hz":   (2920e6, 3080e6),
    "sysclk_2_5ghz_hz": (2370e6, 2630e6),
    "rate_divider":     (1, 2147483647),
    "watchdog_ticks":   (2, 2147483647),
    "delay_counter":    (3, 16777218),
    "d_delay":          (4, 32),
    "a_delay":          (0, 23),
    "post_delay":       (3, 258),
    "burst_count":      (1, 65535),
    "f_div":            (1, 65535),
    "f_div_acq":        (1, 32767),
    "dac_value":        (0, 4095),
    "photodiode_bias":  (0, 660),
    "lag_pll":          (-8, 8),
}

# ch4 = own 100MHz clk, delay counter in DIRECT 10ns units (not F/28), has A-delay only, no D-delay.
# ch7 shares ch6's D+A delay regs (no own reg).
NO_D_DELAY_CH = (4, 7)
NO_A_DELAY_CH = (7,)


def check_range(name, value):
    lo, hi = RANGES[name]
    if not (lo <= value <= hi):
        raise ValueError(f"{name}={value} out of range [{lo},{hi}]")
    return True


# ---------- CLOCK ----------

ALLOWED_N = [30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60,
             62, 64, 66, 68, 70, 72, 76, 78, 80, 84, 88, 90, 92, 96, 98, 100,
             102, 104, 108, 110, 112, 116, 120, 124]


def calc_pll2_n(ext_clk_mhz, target_mhz=3000):
    ideal = target_mhz / ext_clk_mhz
    n = min(ALLOWED_N, key=lambda x: abs(x - ideal))
    sysclk = n * ext_clk_mhz
    return n, sysclk


def resolve_vco_mode(ext_clk_mhz):
    check_range("ext_clock_hz", ext_clk_mhz * 1e6)
    n, sysclk = calc_pll2_n(ext_clk_mhz, 3000)
    if 2920 <= sysclk <= 3080:
        return {"ndiv": n, "sysclk_mhz": sysclk, "vco2": "3GHz"}
    n, sysclk = calc_pll2_n(ext_clk_mhz, 2500)
    check_range("sysclk_2_5ghz_hz", sysclk * 1e6)
    return {"ndiv": n, "sysclk_mhz": sysclk, "vco2": "2.5GHz"}


def system_clock_hz(mode, n_div=None, ext_clk_hz=None):
    if mode == "internal":
        return 3_000_000_000
    if n_div is None or ext_clk_hz is None:
        raise ValueError("external mode needs n_div + ext_clk_hz")
    return n_div * ext_clk_hz


# ---------- DELAY ----------

def calc_delay(time_s, f_hz, channel):
    """
    channel 4: SPECIAL CASE. Own 100MHz clock, delay counter in DIRECT 10ns
    units (not F/28 formula). Has A-delay (25ps trim), NO D-delay.
    f_hz param ignored for ch4.

    channel 7: shares ch6's D-delay + A-delay regs. Only delay_counter is own.

    all other channels (0,1,2,3,5,6): full F/28-based formula.
    """
    if channel == 4:
        cnt10 = int(time_s / 10e-9)  # floor, direct 10ns ticks
        remainder_s = time_s - cnt10 * 10e-9
        a_delay = int(round(remainder_s / 25e-12))  # 25ps fine trim
        a_delay = max(0, min(23, a_delay))
        return {"delay_counter": cnt10, "a_delay": a_delay}

    f28 = f_hz / 28
    tcount = f28 * time_s
    delay_counter = int(tcount)  # floor
    frac = tcount - delay_counter

    result = {"delay_counter": delay_counter}
    if channel not in NO_D_DELAY_CH:
        result["d_delay"] = int(frac * 28 + 4)
    if channel not in NO_A_DELAY_CH:
        result["a_delay"] = int((frac * 28 - int(frac * 28)) * 13)
    if channel in (6, 7):
        result["shared_ad"] = True
    return result


def validate_delay(result, channel):
    check_range("delay_counter", result["delay_counter"])
    if "d_delay" in result:
        check_range("d_delay", result["d_delay"])
    if "a_delay" in result:
        check_range("a_delay", result["a_delay"])
    return True


def min_delay_time_s(f_hz, channel=None):
    """Floor of representable delay time. ch4 uses direct 10ns units."""
    lo, _ = RANGES["delay_counter"]
    if channel == 4:
        return lo * 10e-9
    return lo * 28 / f_hz


def max_delay_time_s(f_hz, channel=None):
    """Ceiling of representable delay time. ch4 uses direct 10ns units."""
    _, hi = RANGES["delay_counter"]
    if channel == 4:
        return hi * 10e-9
    return hi * 28 / f_hz


def calc_post_delay_checked(width_s, f_hz):
    """Raises if out of range — no silent clamp."""
    f28 = f_hz / 28
    count = int(round(width_s * f28))
    check_range("post_delay", count)
    return count


def calc_post_delay_clamped(width_s, f_hz):
    """Silently clamps to valid range — use only if caller reports the clamp."""
    f28 = f_hz / 28
    count = int(round(width_s * f28))
    return max(3, min(258, count))


def min_post_delay_s(f_hz):
    lo, _ = RANGES["post_delay"]
    return lo * 28 / f_hz


def max_post_delay_s(f_hz):
    _, hi = RANGES["post_delay"]
    return hi * 28 / f_hz


# ---------- TRIGGER / RATE ----------

def calc_rate_divider(period_s, source_period_s):
    n = round(period_s / source_period_s)
    check_range("rate_divider", n)
    return n


def calc_burst_count(n):
    n = int(n)
    check_range("burst_count", n)
    return n


def calc_f_div(n):
    n = int(n)
    check_range("f_div", n)
    return n


def calc_f_div_acq(n):
    n = int(n)
    check_range("f_div_acq", n)
    return n


def calc_freq_div_mode(divider_n):
    """MuxConfSw = F div (0x52=4); returns validated F div for 0x69."""
    return calc_f_div(divider_n)


def calc_burst_mode(burst_n, fdiv_n=1):
    """Burst count (0x74) + fdiv (0x69) pair."""
    return {
        "burst_count": calc_burst_count(burst_n),
        "f_div": calc_f_div(fdiv_n),
    }


# ---------- WATCHDOG ----------

def calc_watchdog_period(freq_hz=None, period_s=None):
    if (freq_hz is None) == (period_s is None):
        raise ValueError("pass exactly one of freq_hz / period_s")
    if freq_hz:
        period_s = 1 / freq_hz
    ticks = round(period_s / 10e-9)
    check_range("watchdog_ticks", ticks)
    return ticks


# ---------- DAC ----------

def calc_dac_value(voltage, vmax=1.0):
    val = round((voltage / vmax) * 4095)
    check_range("dac_value", val)
    return val


def calc_dac_config(dac1_voltage, dac2_voltage, vmax=1.0):
    """DAC1 -> Config1 (0x6B), DAC2 -> Config2 (0x6C)."""
    return {
        "dac1": calc_dac_value(dac1_voltage, vmax),
        "dac2": calc_dac_value(dac2_voltage, vmax),
    }