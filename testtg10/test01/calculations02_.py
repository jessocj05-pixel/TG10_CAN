"""Register calculation API for EKSMA SY4000 / TG10.

Pure math, no I/O. Datasheet-oriented with clamping (GUI-friendly).

Verification status (see module bottom docstring summary):
  VERIFIED — clock, F/28, rate divider, full-res delay core, DAC, burst, fdiv, watchdog
  NEEDS SOURCE CONFIRM — post-delay formula, trigger mux enum values
  HARDWARE-MAP DEPENDENT — CH4 (counter-only per datasheet text), CH6/7 shared A/D ownership
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from enum import IntEnum


class SyError(ValueError):
    pass

class OscclkMux(IntEnum):
    Internal_100Mhz = 0
    External = 1



class RateSource(IntEnum):
    """MuxRateClk — verify labels against register map before live use."""
    INTERNAL_100M = 0
    OPTCLK = 1
    OPTCLK_DIV2 = 2
    SYNCIN = 3


class StartTrigger(IntEnum):
    """MuxStartTrg — verify labels against register map before live use."""
    RATE_DIVIDER = 0
    RATE_DIV_OPTCLK = 1
    SYNCIN = 2
    SYNCIN_OPTCLK = 3
    ONE_SHOT_TRIG = 4
    ONE_SHOT_SMART = 5


_N_TABLE = (
    30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 62, 64,
    66, 68, 70, 72, 76, 78, 80, 84, 88, 90, 92, 96, 98, 100, 102, 104, 108,
    110, 112, 116, 120, 124,
)
_F3_LO, _F3_HI = 2_920_000_000, 3_080_000_000        #3GHz VCO LIMIT
_F25_LO, _F25_HI = 2_370_000_000, 2_630_000_000      #2.5GHz VCO LIMIT
_U32_MAX = 2_147_483_647
ALLOWED_N = list(_N_TABLE)
#-------------------------------------------------------------------------
#@RANGES
#-------------------------------------------------------------------------
RANGES = {
    "ext_clock_hz": (20e6, 100e6), "osc_clock_mhz": (10, 100),
    "sysclk_3ghz_hz": (2920e6, 3080e6), "sysclk_2_5ghz_hz": (2370e6, 2630e6),
    "rate_divider": (1, _U32_MAX), "watchdog_ticks": (2, _U32_MAX),
    "delay_counter": (3, 16777218), "d_delay": (4, 32), "a_delay": (0, 23),
    "post_delay": (3, 258), "burst_count": (1, 65535), "f_div": (1, 65535),
    "f_div_acq": (1, 32767), "dac_value": (0, 4095),
    "photodiode_bias": (0, 660), "lag_pll": (-8, 8),
}

# Datasheet text: CH4 lacks A/D; CH7 shares CH6 physical A/D pair.
NO_D_DELAY_CH = (4, 7)
NO_A_DELAY_CH = (4, 7)

#HELPS TO CHECK RANGE BASED ON @RANGES
def check_range(name, value):
    lo, hi = RANGES[name]
    if not (lo <= value <= hi):
        raise ValueError(f"{name}={value} out of range [{lo},{hi}]")
    return True

#time in seconds
def parse_time(t):
    """Parse time string → seconds.

    Accepts: ps, ns, us/µs, ms, s
    Examples: 500ps, 25ns, 1.5us, 10ms, 0.001s

    Longer unit suffixes are matched first so "25ps" is not
    mis-read as seconds ("25p" + "s").
    """
    if isinstance(t, (int, float)):
        return float(t)
    s = str(t).strip().lower().replace(" ", "")
    # (suffix, scale) – longest first is critical
    units = (
        ("ps", 1e-12),
        ("ns", 1e-9),
        ("us", 1e-6),
        ("µs", 1e-6),
        ("ms", 1e-3),
        ("s",  1.0),
    )
    for suf, scale in units:
        if s.endswith(suf):
            num = s[: -len(suf)]
            if not num:
                raise ValueError(f"missing number in time {t!r}")
            try:
                return float(num) * scale
            except ValueError as e:
                raise ValueError(f"cannot parse time: {t!r}") from e
    # bare number → assume seconds
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"cannot parse time: {t!r}  (use ps/ns/us/ms/s)")

#freq in Hz
def parse_freq(f):
    if isinstance(f, (int, float)):
        return float(f)
    f = str(f).strip().lower().replace(" ", "")
    if f.endswith("ghz"):
        return float(f[:-3]) * 1e9
    if f.endswith("mhz"):
        return float(f[:-3]) * 1e6
    if f.endswith("khz"):
        return float(f[:-3]) * 1e3
    if f.endswith("hz"):
        return float(f[:-2])
    raise ValueError(f"cannot parse freq: {f!r}")


# ---------------------------------------------------------------------------
# Clock — authoritative selector is clock_external / clock_internal_100mhz
# ---------------------------------------------------------------------------
#@clockconfig->helps iin configuration of clk stored in class
#----------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class ClockConfig:
    n_divider: int
    vco2_reg: int
    f_hz: int
    oscillator_clock_reg: int
    optical_clock_mux: int


def clock_internal_100mhz():
    """N=30, VCO 3 GHz, F=3e9. VERIFIED."""
    return ClockConfig(30, 1, 3_000_000_000, 100, 0)


def clock_external(fext_hz, *, force_vco=None):
    """First N in table that lands in preferred VCO window. VERIFIED ranges."""
    fext_hz = int(round(fext_hz))
    if not (20_000_000 <= fext_hz <= 100_000_000):
        raise SyError(f"Fext {fext_hz} Hz out of range [20e6, 100e6]")
    osc_reg = round(fext_hz / 1_000_000)

    def _search(lo, hi, vco_reg):
        for n in _N_TABLE:
            f_calc = n * fext_hz
            if lo <= f_calc <= hi:
                return ClockConfig(n, vco_reg, f_calc, osc_reg, 1)
        return None

    if force_vco == 0:
        result = _search(_F25_LO, _F25_HI, 0)
    elif force_vco == 1:
        result = _search(_F3_LO, _F3_HI, 1)
    else:
        result = _search(_F3_LO, _F3_HI, 1) or _search(_F25_LO, _F25_HI, 0)
    if result is None:
        raise SyError(f"No PLL2 N for Fext={fext_hz} Hz")
    return result

#@degub_ndiv
def calc_pll2_n(ext_clk_mhz, target_mhz=3000):
    """Nearest N to ideal — diagnostic only. Prefer clock_external() for config."""
    ideal = target_mhz / ext_clk_mhz
    n = min(_N_TABLE, key=lambda x: abs(x - ideal))
    return n, n * ext_clk_mhz
# print(calc_pll2_n(20,3000))
#@debug_vco_mode
def resolve_vco_mode(ext_clk_mhz):
    """Legacy dict API — uses authoritative clock_external()."""
    cfg = clock_external(ext_clk_mhz * 1e6)
    return {
        "ndiv": cfg.n_divider,
        "sysclk_mhz": cfg.f_hz / 1e6,
        "vco2": "3GHz" if cfg.vco2_reg == 1 else "2.5GHz",
    }

# print(resolve_vco_mode(20))
def system_clock_hz(mode, n_div=None, ext_clk_hz=None):
    if mode == "internal":
        return 3_000_000_000
    if n_div is None or ext_clk_hz is None:
        raise ValueError("external mode needs n_div + ext_clk_hz")
    return int(n_div * ext_clk_hz)
# print(system_clock_hz(0,124,20))

def f28_hz(f_hz):
    """F/28 time base. VERIFIED."""
    return float(f_hz) / 28.0
# f = 60*50e6
# print(f)

# print(f28_hz(f))
# print(f28_hz(20))
def f28_s(f_hz):
    return 28.0/float(f_hz)
# print(f28_s(3000e6))

# ---------------------------------------------------------------------------
# Rate divider
# | RATEDIV | Period @ 100 MHz |
# | ------: | ---------------: |
# |       1 |            10 ns |
# |       2 |            20 ns |
# |      10 |           100 ns |
# |      50 |           500 ns |
# |     100 |   1000 ns = 1 µs |
# |    1000 | 10000 ns = 10 µs |

# ---------------------------------------------------------------------------

def rate_divider_from_period_100m(period_ns):
    """Internal 100 MHz source: T = RateDivider * 10 ns. VERIFIED."""
    return max(1, min(int(round(period_ns / 10.0)), _U32_MAX))


def period_100m_from_rate_divider(rate_divider):
    return rate_divider * 10.0

# rd=(rate_divider_from_period_100m(100))
# print(rd)
# print(period_100m_from_rate_divider(rd))
#-----------------------------------------------------------
# T = RateDivider / Fclock
# RateDivider = T × Fclock
#-----------------------------------------------------------
def rate_divider_from_period_ext(period_s, fext_hz):
    """OPTCLK source: RateDivider = T * Fext. VERIFIED."""
    return max(1, min(int(round(period_s * float(fext_hz))), _U32_MAX))
# print(rate_divider_from_period_ext(100e-6,100e6))   #100us x 100MHz=10000

def period_ext_from_rate_divider(rate_divider, fext_hz):
    return 0.0 if not fext_hz else rate_divider / float(fext_hz)
# print(period_ext_from_rate_divider(10000,100e6))


def freq_to_period_s(freq_hz):
    return 0.0 if freq_hz <= 0 else 1.0 / freq_hz
# print(freq_to_period_s(100e6))  

def period_to_freq_hz(period_s):
    return 0.0 if period_s <= 0 else 1.0 / period_s
# print(period_to_freq_hz(1e-08))

def calc_rate_divider(period_s, source_period_s):
    """Compatibility wrapper around period / source_tick."""
    return max(1, min(int(round(period_s / source_period_s)), _U32_MAX))
# print(calc_rate_divider(100e-9,10e-9))

def calc_trigger_config(mode, period_s=None, ext_clk_hz=None,syncin_hz=None,ratediv = None):
    """Mux + ratediv package. Mux enum values = REGISTER-MAP DEPENDENT."""
    if mode == "internal_100mhz":
        if period_s is None:
            raise ValueError("internal_100mhz needs period_s")
        return {
            "mux_rateclk": int(RateSource.INTERNAL_100M),
            "mux_trigger": int(StartTrigger.RATE_DIVIDER),
            "ratediv": rate_divider_from_period_100m(period_s * 1e9),
        }
    if mode == "external_clkin":
        if period_s is None or ext_clk_hz is None:
            raise ValueError("external_clkin needs period_s + ext_clk_hz")
        return {
            "mux_rateclk": int(RateSource.OPTCLK),
            "mux_trigger": int(StartTrigger.RATE_DIV_OPTCLK),
            "ratediv": rate_divider_from_period_ext(period_s, ext_clk_hz),
        }
    if mode == "external_syncin":
        return {
            "mux_rateclk": int(RateSource.SYNCIN),
            "mux_trigger": int(StartTrigger.RATE_DIVIDER),
            "ratediv": check_range(ratediv, "rate_divider"),    
        }
    if mode == "external_dual_in":
        if period_s is None or ext_clk_hz is None:
                    raise ValueError("external_clkin needs period_s + ext_clk_hz")
        return {
            "mux_rateclk": int(RateSource.SYNCIN),
            "mux_trigger": int(StartTrigger.RATE_DIV_OPTCLK),
            "ratediv": calc_rate_divider(period_s,1.0/syncin_hz,),
        }
        
    raise ValueError(f"unknown trigger mode: {mode!r}")


# ---------------------------------------------------------------------------
# Delay
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class DelayRegs:
    delay_counter: int
    d_delay: int | None
    a_delay: int | None
    clamped: bool


def delay_calc_fullres(f_hz, time_s):
    """Datasheet: DelayCounter = floor(TCount), TCount = (F/28)*t.
    D/A from fractional part. VERIFIED formula; clamps for GUI.
    """
    t_count = f28_hz(f_hz) * time_s
    dc_float = math.floor(t_count)  # exact datasheet floor — no epsilon nudge
    frac28 = (t_count - dc_float) * 28.0
    d_delay = int(frac28 + 4.0)
    a_delay = int((frac28 - math.floor(frac28)) * 13.0)
    delay_counter = int(dc_float)
    clamped = False
    if delay_counter < 3:
        delay_counter, clamped = 3, True
    elif delay_counter > 16777218:
        delay_counter, clamped = 16777218, True
    if d_delay < 4:
        d_delay, clamped = 4, True
    elif d_delay > 32:
        d_delay, clamped = 32, True
    if a_delay > 23:
        a_delay, clamped = 23, True
    elif a_delay < 0:
        a_delay, clamped = 0, True
    return DelayRegs(delay_counter, d_delay, a_delay, clamped)


def delay_calc_ch4(time_s):
    """CH4: 100 MHz / 10 ns DelayCounter only — no A/D registers (datasheet text).
    HARDWARE-MAP DEPENDENT: do not add A-delay until register map confirms it.
    """
    cnt = int(round(time_s / 10e-9))
    clamped = False
    if cnt < 3:
        cnt, clamped = 3, True
    elif cnt > 16777218:
        cnt, clamped = 16777218, True
    return DelayRegs(cnt, None, None, clamped)
#@ch4adelay channel4 uses adelay
# def delay_calc_ch4(f_hz, time_s):
#     """CH4: DelayCounter + A-delay.
#     A-delay usage confirmed by hardware log.
#     """

#     t_count = f28_hz(f_hz) * time_s

#     delay_counter = math.floor(t_count)

#     frac28 = (t_count - delay_counter) * 28.0

#     a_delay = int(
#         (frac28 - math.floor(frac28)) * 13.0
#     )

#     clamped = False

#     if delay_counter < 3:
#         delay_counter, clamped = 3, True
#     elif delay_counter > 16777218:
#         delay_counter, clamped = 16777218, True

#     if a_delay < 0:
#         a_delay, clamped = 0, True
#     elif a_delay > 23:
#         a_delay, clamped = 23, True

#     return DelayRegs(
#         delay_counter,
#         None,       # D-delay not confirmed for CH4
#         a_delay,
#         clamped
#     )

def delay_calc_ch67(f_hz, time_s):
    """Same math as fullres. Shared physical A/D is a sequence-layer concern."""
    return delay_calc_fullres(f_hz, time_s)


def post_delay_calc(f_hz, pulse_width_s):
    """round((F/28)*width), clamp [3,258]. NEEDS SOURCE CONFIRM on equation."""
    return max(3, min(int(round(f28_hz(f_hz) * pulse_width_s)), 258))


def calc_delay(time_s, f_hz, channel):
    if channel == 4:
        r = delay_calc_ch4(time_s)
        out = {"delay_counter": r.delay_counter}
        # r = delay_calc_ch4(f_hz, time_s)

        # out = {
        #     "delay_counter": r.delay_counter,
        # }

        # if r.a_delay is not None:
        #     out["a_delay"] = r.a_delay
    else:
        r = delay_calc_fullres(f_hz, time_s)
        out = {"delay_counter": r.delay_counter}
        if channel not in NO_D_DELAY_CH:
            out["d_delay"] = r.d_delay
        if channel not in NO_A_DELAY_CH:
            out["a_delay"] = r.a_delay
        if channel in (6, 7):
            out["shared_ad"] = True
    if r.clamped:
        out["clamped"] = True
    return out


def validate_delay(result, channel):
    check_range("delay_counter", result["delay_counter"])
    if "d_delay" in result and result["d_delay"] is not None:
        check_range("d_delay", result["d_delay"])
    if "a_delay" in result and result["a_delay"] is not None:
        check_range("a_delay", result["a_delay"])
    return True


def min_delay_time_s(f_hz, channel=None):
    lo = RANGES["delay_counter"][0]
    return lo * 10e-9 if channel == 4 else lo * 28 / float(f_hz)


def max_delay_time_s(f_hz, channel=None):
    hi = RANGES["delay_counter"][1]
    return hi * 10e-9 if channel == 4 else hi * 28 / float(f_hz)


def calc_post_delay_checked(width_s, f_hz):
    return post_delay_calc(f_hz, width_s)


def calc_post_delay_clamped(width_s, f_hz):
    return post_delay_calc(f_hz, width_s)


def min_post_delay_s(f_hz):
    return RANGES["post_delay"][0] * 28 / float(f_hz)


def max_post_delay_s(f_hz):
    return RANGES["post_delay"][1] * 28 / float(f_hz)


# ---------------------------------------------------------------------------
# Watchdog / DAC / burst
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class WatchdogRegs:
    tmin_reg: int
    tmax_reg: int


def watchdog_calc(tmin_period_s, tmax_period_s):
    def _reg(p):
        return max(2, min(int(round((p * 1e9) / 10.0)), _U32_MAX))
    return WatchdogRegs(_reg(tmin_period_s), _reg(tmax_period_s))


def calc_watchdog_period(freq_hz=None, period_s=None):
    if (freq_hz is None) == (period_s is None):
        raise ValueError("pass exactly one of freq_hz / period_s")
    if freq_hz:
        period_s = 1.0 / float(freq_hz)
    return max(2, min(int(round(float(period_s) / 10e-9)), _U32_MAX))


def dac_code(v_target, v_full_scale=1.0):
    if v_full_scale <= 0:
        v_full_scale = 1.0
    return max(0, min(int(round((v_target / v_full_scale) * 4095.0)), 4095))


def dac_voltage(code, v_full_scale=1.0):
    if v_full_scale <= 0:
        v_full_scale = 1.0
    return (code / 4095.0) * v_full_scale


def calc_dac_value(voltage, vmax=1.0):
    return dac_code(voltage, vmax)


def calc_dac_config(dac1_voltage, dac2_voltage, vmax=1.0):
    return {"dac1": dac_code(dac1_voltage, vmax), "dac2": dac_code(dac2_voltage, vmax)}


def burst_count_clamp(n):
    return max(1, min(int(n), 65535))


def fdiv_clamp(n):
    return max(1, min(int(n), 65535))


def fdiv_acq_clamp(n):
    return max(1, min(int(n), 32767))


def calc_burst_count(n):
    return burst_count_clamp(n)


def calc_f_div(n):
    return fdiv_clamp(n)


def calc_f_div_acq(n):
    return fdiv_acq_clamp(n)


def calc_freq_div_mode(divider_n):
    return fdiv_clamp(divider_n)


def calc_burst_mode(burst_n, fdiv_n=1):
    return {"burst_count": burst_count_clamp(burst_n), "f_div": fdiv_clamp(fdiv_n)}


CLKVALID_STATES = {
    0: "NOCLOCK-NOLOCK", 1: "NOCLOCK-LOCKOK",
    2: "CLOCKOK-NOLOCK", 3: "CLOCKOK-LOCKOK",
}
PLL1_STATES = {0: "NOLOCK", 1: "LOCKOK"}


def check_clock_lock(clkvalid_byte):
    if clkvalid_byte != 0x03:
        state = CLKVALID_STATES.get(clkvalid_byte, f"UNKNOWN(0x{clkvalid_byte:02X})")
        raise RuntimeError(f"clock not ready: {state} - refuse Command=ON")
    return True


def check_pll1_lock(pll1_byte, required=False):
    ok = pll1_byte == 0x01
    if not ok and required:
        state = PLL1_STATES.get(pll1_byte, f"UNKNOWN(0x{pll1_byte:02X})")
        raise RuntimeError(f"PLL1 not locked: {state} - refuse Command=ON")
    return ok
