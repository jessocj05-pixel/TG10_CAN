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
    """Configure PLL2 for an external clock using the OEM N-selection procedure."""

    fext_hz = float(fext_hz)

    if not (20_000_000 <= fext_hz <= 100_000_000):
        raise SyError(
            f"Fext {fext_hz} Hz out of range [20e6, 100e6]"
        )

    osc_reg = round(fext_hz / 1_000_000)

    def _search(target_hz, lo, hi, vco_reg):
        # OEM: calculate N ~= target frequency / external clock
        target_n = target_hz / fext_hz

        # Choose the closest allowed N
        n = min(
            _N_TABLE,
            key=lambda candidate: abs(candidate - target_n)
        )

        # Actual system frequency
        f_calc = n * fext_hz

        # Check VCO/system-frequency window
        if lo <= f_calc <= hi:
            return ClockConfig(
                n,
                vco_reg,
                f_calc,
                osc_reg,
                1
            )

        return None

    # 3 GHz VCO
    if force_vco == 1:
        result = _search(
            3_000_000_000,
            _F3_LO,
            _F3_HI,
            1
        )

    # 2.5 GHz VCO
    elif force_vco == 0:
        result = _search(
            2_500_000_000,
            _F25_LO,
            _F25_HI,
            0
        )

    # Automatic: try 3 GHz first, then 2.5 GHz
    else:
        result = (
            _search(3_000_000_000, _F3_LO, _F3_HI, 1)
            or
            _search(2_500_000_000, _F25_LO, _F25_HI, 0)
        )

    if result is None:
        raise SyError(
            f"No PLL2 configuration for Fext={fext_hz} Hz"
        )

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
            "ratediv": check_range("rate_divider",ratediv),    
        }
    if mode == "external_dual_in":
        if period_s is None or ext_clk_hz is None or syncin_hz is None:
                    raise ValueError("external_dual_in needs period_s + ext_clk_hz + syncin_hz")
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

    # Mathematical coarse count before the TG10 +3 programming offset
    dc_float = math.floor(t_count)

    # Fractional part is calculated from the PRE-OFFSET coarse count
    frac28 = (f_hz * time_s) - (dc_float * 28.0)

    d_delay = int(frac28 + 4.0)

    a_delay = int(
        (frac28 - math.floor(frac28)) * 13.0
    )
    # TG10 hardware programming offset:
    # programmed DelayCounter = mathematical coarse count + 3
    delay_counter = int(dc_float) + 3

    clamped = False

    if delay_counter < 3:
        delay_counter, clamped = 3, True
    elif delay_counter > 16777218:
        delay_counter, clamped = 16777218, True

    if d_delay < 4:
        d_delay, clamped = 4, True
    elif d_delay > 31:
        d_delay, clamped = 31, True

    if a_delay > 23:
        a_delay, clamped = 23, True
    elif a_delay < 0:
        a_delay, clamped = 0, True

    return DelayRegs(
        delay_counter,
        d_delay,
        a_delay,
        clamped
    )

# def delay_calc_ch4(time_s):
#     """CH4: 100 MHz / 10 ns DelayCounter only — no A/D registers (datasheet text).
#     HARDWARE-MAP DEPENDENT: do not add A-delay until register map confirms it.
#     """
#     cnt = int(round(time_s / 10e-9))
#     clamped = False
#     if cnt < 3:
#         cnt, clamped = 3, True
#     elif cnt > 16777218:
#         cnt, clamped = 16777218, True
#     return DelayRegs(cnt, None, None, clamped)
# @ch4adelay channel4 uses adelay
def delay_calc_ch4(f_hz, time_s):
    """CH4: DelayCounter + A-delay.
    A-delay usage confirmed by hardware log.
    """

    t_count = f28_hz(f_hz) * time_s

    delay_counter = math.floor(t_count)

    frac28 = (t_count - delay_counter) * 28.0

    a_delay = int(
        (frac28 - math.floor(frac28)) * 13.0
    )

    clamped = False

    if delay_counter < 3:
        delay_counter, clamped = 3, True
    elif delay_counter > 16777218:
        delay_counter, clamped = 16777218, True

    if a_delay < 0:
        a_delay, clamped = 0, True
    elif a_delay > 23:
        a_delay, clamped = 23, True

    return DelayRegs(
        delay_counter,
        None,       # D-delay not confirmed for CH4
        a_delay,
        clamped
    )

def delay_calc_ch67(f_hz, time_s):
    """Same math as fullres. Shared physical A/D is a sequence-layer concern."""
    return delay_calc_fullres(f_hz, time_s)


def post_delay_calc(channel, f_hz, pulse_width_s):
    """
    Calculate PostDel counter and actual representable time.

    Channels 0,1,2,3,5,6,7:
        PostCnt = round((F/28) * width)

    Channel 4:
        PostCnt = round(100 MHz * width)

    Counter range: 3..258.
    """

    if channel == 4:
        tick_hz = 100_000_000.0
    else:
        tick_hz = f28_hz(f_hz)

    post_count = int(round(tick_hz * pulse_width_s))
    post_count = max(3, min(post_count, 258))

    actual_width_s = post_count / tick_hz

    return post_count, actual_width_s

# count, actual_s = post_delay_calc(0, 3e9, 100e-9)

def calc_delay(time_s, f_hz, channel):
    if channel == 4:
        r = delay_calc_ch4(f_hz, time_s)

        out = {
            "delay_counter": r.delay_counter,
        }

        if r.a_delay is not None:
            out["a_delay"] = r.a_delay
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


def calc_post_delay_checked(width_s, f_hz,channel):
    return post_delay_calc(channel,f_hz, width_s)


def calc_post_delay_clamped(width_s, f_hz,channel):
    return post_delay_calc(channel,f_hz, width_s)

# count = calc_post_delay_checked(width_s, f_hz, channel)
def min_post_delay_s(f_hz, channel=None):
    lo = RANGES["post_delay"][0]

    if channel == 4:
        return lo / 100_000_000.0

    return lo * 28 / float(f_hz)


def max_post_delay_s(f_hz, channel=None):
    hi = RANGES["post_delay"][1]

    if channel == 4:
        return hi / 100_000_000.0

    return hi * 28 / float(f_hz)


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
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    
    # for vco in [None, 0, 1]:
    #     try:
    #         c = clock_external(25e6, force_vco=vco)
    #         print(
    #             f"force_vco={vco} -> "
    #             f"N={c.n_divider}, "
    #             f"VCO={c.vco2_reg}, "
    #             f"Fsys={c.f_hz/1e9:.6f} GHz"
    #         )
    #     except SyError as e:
    #         print(f"force_vco={vco} -> ERROR: {e}")
    # print(system_clock_hz("internal"))
    # print(system_clock_hz("external", n_div=120, ext_clk_hz=25e6))
    # print(clock_external(20e6))
    # print(rate_divider_from_period_ext(50e-6, 20e6))
    # print(rate_divider_from_period_ext(50e-6, 25e6))
    # print(rate_divider_from_period_ext(100e-6, 20e6))
    # print(period_ext_from_rate_divider(1000, 20e6))
    # print(period_ext_from_rate_divider(1250, 25e6))
    # print(rate_divider_from_period_100m(100))
    # print(rate_divider_from_period_100m(1000))
    # print(period_100m_from_rate_divider(10))
    # print(period_100m_from_rate_divider(1000))
    

    # cfg = calc_trigger_config(
    #     "external_dual_in",
    #     period_s=10e-6,     # 10 us
    #     ext_clk_hz=20e6,    # CLK IN = 20 MHz
    #     syncin_hz=20e6      # SYNC IN = 20 MHz
    # )

    # print(cfg)
    # cfg = calc_trigger_config(
    # "external_dual_in",
    # period_s=10e-6,
    # ext_clk_hz=100e6,
    # syncin_hz=20e6
    # )

    # print(cfg)
    # print(delay_calc_fullres(3_000_000_000, 100e-9))
    # print(delay_calc_fullres(3_000_000_000, 1e-6))
    # print(delay_calc_fullres(3_000_000_000, 10e-6))   
    # print(delay_calc_ch4(100e-9))
    # print(delay_calc_ch4(1e-6))
    # print(delay_calc_ch4(10e-6)) 
    # print(delay_calc_fullres(3_000_000_000, 0))
    # print(delay_calc_fullres(3_000_000_000, 1e-12))
    # print(delay_calc_fullres(3_000_000_000, 1e-9))
    # print(delay_calc_ch4(0))
    # print(delay_calc_ch4(1e-12))
    # print(delay_calc_ch4(1e-9))
    # print(post_delay_calc(3_000_000_000, 100e-9))
    # print(post_delay_calc(3_000_000_000, 1e-6))
    # print(post_delay_calc(3_000_000_000, 10e-6))
    # print(post_delay_calc(100_000_000, 100e-9))
    # print(post_delay_calc(100_000_000, 1e-6))
    # print(calc_f_div(1))
    # print(calc_f_div(2))
    # print(calc_f_div(100))
    # print(calc_f_div(65535))
    # print(calc_f_div(0))
    # print(calc_f_div(70000))
    # print(calc_f_div(-10))
    # print("\n" + "=" * 70)
    # print("SY4000 CALCULATION SOFTWARE TEST")
    # print("=" * 70)


    # # ============================================================
    # # 1. WATCHDOG
    # # ============================================================

    # print("\n[1] WATCHDOG")
    # print("-" * 70)

    # tests = [
    #     ("20 ns, 100 ns", watchdog_calc(20e-9, 100e-9)),
    #     ("1 us, 10 us", watchdog_calc(1e-6, 10e-6)),
    #     ("0 s, 0 s", watchdog_calc(0, 0)),
    # ]

    # for name, result in tests:
    #     print(f"{name:20s} -> {result}")

    # print("\ncalc_watchdog_period()")

    # print("20 ns  ->", calc_watchdog_period(period_s=20e-9))
    # print("1 us   ->", calc_watchdog_period(period_s=1e-6))
    # print("1 MHz   ->", calc_watchdog_period(freq_hz=1e6))
    # print("10 MHz  ->", calc_watchdog_period(freq_hz=10e6))

    # print("\nInvalid watchdog tests:")

    # try:
    #     calc_watchdog_period()
    # except Exception as e:
    #     print("No arguments       ->", type(e).__name__, e)

    # try:
    #     calc_watchdog_period(freq_hz=1e6, period_s=1e-6)
    # except Exception as e:
    #     print("Both arguments     ->", type(e).__name__, e)


    # # ============================================================
    # # 2. DAC
    # # ============================================================

    # print("\n[2] DAC")
    # print("-" * 70)

    # print("dac_code()")
    # print("0 V          ->", dac_code(0))
    # print("0.5 V        ->", dac_code(0.5))
    # print("1.0 V        ->", dac_code(1.0))
    # print("-1 V         ->", dac_code(-1))
    # print("2 V          ->", dac_code(2))

    # print("\ndac_voltage()")
    # print("Code 0       ->", dac_voltage(0))
    # print("Code 2048    ->", dac_voltage(2048))
    # print("Code 4095    ->", dac_voltage(4095))

    # print("\n2.5 V full-scale tests:")
    # print("1.25 V       -> code", dac_code(1.25, 2.5))
    # print("2.5 V        -> code", dac_code(2.5, 2.5))
    # print("Code 2048    -> voltage", dac_voltage(2048, 2.5))
    # print("Code 4095    -> voltage", dac_voltage(4095, 2.5))

    # print("\nDAC configuration:")
    # print(
    #     calc_dac_config(
    #         dac1_voltage=0.5,
    #         dac2_voltage=0.75,
    #         vmax=1.0
    #     )
    # )


    # # ============================================================
    # # 3. BURST COUNT
    # # ============================================================

    # print("\n[3] BURST COUNT")
    # print("-" * 70)

    # for value in [1, 10, 65535, 0, -10, 70000]:
    #     print(f"Input {value:6d} -> {calc_burst_count(value)}")


    # # ============================================================
    # # 4. FDIV
    # # ============================================================

    # print("\n[4] FDIV")
    # print("-" * 70)

    # for value in [1, 2, 100, 65535, 0, 70000, -10]:
    #     print(f"Input {value:6d} -> {calc_f_div(value)}")


    # # ============================================================
    # # 5. FDIV ACQ
    # # ============================================================

    # print("\n[5] FDIV ACQ")
    # print("-" * 70)

    # for value in [1, 2, 100, 32767, 0, 50000, -5]:
    #     print(f"Input {value:6d} -> {calc_f_div_acq(value)}")


    # # ============================================================
    # # 6. EXTERNAL CLOCK
    # # ============================================================

    # print("\n[6] EXTERNAL CLOCK")
    # print("-" * 70)

    # external_clock_tests = [
    #     20e6,
    #     21e6,
    #     22e6,
    #     24e6,
    #     25e6,
    #     30e6,
    #     40e6,
    #     50e6,
    #     60e6,
    #     75e6,
    #     100e6,
    # ]

    # for fext in external_clock_tests:
    #     try:
    #         cfg = clock_external(fext)

    #         print(
    #             f"{fext / 1e6:7.3f} MHz -> "
    #             f"N={cfg.n_divider:3d}, "
    #             f"VCO={cfg.vco2_reg}, "
    #             f"Fsys={cfg.f_hz / 1e9:.6f} GHz, "
    #             f"OscClock={cfg.oscillator_clock_reg} MHz, "
    #             f"OscClkMux={cfg.optical_clock_mux}"
    #         )

    #     except Exception as e:
    #         print(
    #             f"{fext / 1e6:7.3f} MHz -> ERROR: "
    #             f"{type(e).__name__}: {e}"
    #         )


    # print("\nExternal clock invalid-input tests:")

    # for fext in [
    #     19.999e6,
    #     100.001e6,
    #     0,
    #     -10e6,
    # ]:
    #     try:
    #         cfg = clock_external(fext)
    #         print(
    #             f"{fext / 1e6:10.3f} MHz -> "
    #             "UNEXPECTED SUCCESS:", cfg
    #         )

    #     except Exception as e:
    #         print(
    #             f"{fext / 1e6:10.3f} MHz -> "
    #             f"{type(e).__name__}: {e}"
    #         )


    # # ============================================================
    # # 7. RATE DIVIDER
    # # ============================================================

    # print("\n[7] RATE DIVIDER")
    # print("-" * 70)

    # print("External CLKIN:")
    # print(
    #     "20 MHz, 50 us   ->",
    #     rate_divider_from_period_ext(50e-6, 20e6)
    # )

    # print(
    #     "20 MHz, 100 us  ->",
    #     rate_divider_from_period_ext(100e-6, 20e6)
    # )

    # print(
    #     "25 MHz, 50 us   ->",
    #     rate_divider_from_period_ext(50e-6, 25e6)
    # )

    # print("\nReverse external CLKIN:")

    # print(
    #     "20 MHz, RD=1000  ->",
    #     period_ext_from_rate_divider(1000, 20e6),
    #     "seconds"
    # )

    # print(
    #     "20 MHz, RD=2000  ->",
    #     period_ext_from_rate_divider(2000, 20e6),
    #     "seconds"
    # )

    # print("\nInternal 100 MHz:")

    # print(
    #     "100 ns  ->",
    #     rate_divider_from_period_100m(100)
    # )

    # print(
    #     "1000 ns ->",
    #     rate_divider_from_period_100m(1000)
    # )

    # print("\nReverse internal 100 MHz:")

    # print(
    #     "RD=10  ->",
    #     period_100m_from_rate_divider(10),
    #     "ns"
    # )

    # print(
    #     "RD=100 ->",
    #     period_100m_from_rate_divider(100),
    #     "ns"
    # )


    # # ============================================================
    # # 8. FREQUENCY <-> PERIOD
    # # ============================================================

    # print("\n[8] FREQUENCY <-> PERIOD")
    # print("-" * 70)

    # print("Frequency -> Period:")

    # for freq in [1e3, 1e6, 10e6]:
    #     period = freq_to_period_s(freq)

    #     print(
    #         f"{freq / 1e3:g} kHz -> "
    #         f"{period:.12g} s"
    #     )

    # print("\nPeriod -> Frequency:")

    # for period in [1e-3, 1e-6, 100e-9]:
    #     freq = period_to_freq_hz(period)

    #     print(
    #         f"{period:.12g} s -> "
    #         f"{freq:.12g} Hz"
    #     )


    # # ============================================================
    # # 9. DELAY CALCULATION
    # # ============================================================

    # print("\n[9] DELAY CALCULATION")
    # print("-" * 70)

    # delay_tests = [
    #     (3e9, 0),
    #     (3e9, 1e-12),
    #     (3e9, 1e-9),
    #     (3e9, 100e-9),
    #     (3e9, 1e-6),
    #     (3e9, 10e-6),
    #     (2.48e9, 100e-9),
    #     (3.04e9, 100e-9),
    # ]

    # for freq, time_s in delay_tests:

    #     result = delay_calc_fullres(freq, time_s)

    #     print(
    #         f"F={freq / 1e9:.3f} GHz, "
    #         f"T={time_s:.12g} s -> "
    #         f"Counter={result.delay_counter}, "
    #         f"D={result.d_delay}, "
    #         f"A={result.a_delay}, "
    #         f"clamped={result.clamped}"
    #     )


    # # ============================================================
    # # 10. CH4 DELAY
    # # ============================================================

    # print("\n[10] CH4 DELAY")
    # print("-" * 70)

    # for time_s in [
    #     0,
    #     1e-12,
    #     1e-9,
    #     100e-9,
    #     1e-6,
    #     10e-6,
    # ]:

    #     result = delay_calc_ch4(time_s)

    #     print(
    #         f"T={time_s:.12g} s -> "
    #         f"Counter={result.delay_counter}, "
    #         f"D={result.d_delay}, "
    #         f"A={result.a_delay}, "
    #         f"clamped={result.clamped}"
    #     )


    # # ============================================================
    # # 11. POST DELAY
    # # ============================================================

    # print("\n[11] POST DELAY")
    # print("-" * 70)

    # postdelay_tests = [
    #     (3e9, 100e-9),
    #     (3e9, 1e-6),
    #     (3e9, 10e-6),
    #     (100e6, 100e-9),
    #     (100e6, 1e-6),
    # ]

    # for freq, width in postdelay_tests:

    #     result = post_delay_calc(freq, width)

    #     print(
    #         f"F={freq / 1e9:.3f} GHz, "
    #         f"Width={width:.12g} s -> "
    #         f"PostDelay={result}"
    #     )


    # # ============================================================
    # # 12. TRIGGER CONFIGURATION
    # # ============================================================

    # print("\n[12] TRIGGER CONFIGURATION")
    # print("-" * 70)

    # print("\nInternal 100 MHz:")
    # try:
    #     result = calc_trigger_config(
    #         "internal_100mhz",
    #         period_s=1e-6
    #     )
    #     print(result)
    # except Exception as e:
    #     print(type(e).__name__, e)


    # print("\nExternal CLKIN:")
    # try:
    #     result = calc_trigger_config(
    #         "external_clkin",
    #         period_s=50e-6,
    #         ext_clk_hz=20e6
    #     )
    #     print(result)
    # except Exception as e:
    #     print(type(e).__name__, e)


    # print("\nExternal SYNCIN:")
    # try:
    #     result = calc_trigger_config(
    #         "external_syncin",
    #         ratediv=100
    #     )
    #     print(result)
    # except Exception as e:
    #     print(type(e).__name__, e)


    # print("\nExternal DUAL:")
    # try:
    #     result = calc_trigger_config(
    #         "external_dual_in",
    #         period_s=10e-6,
    #         ext_clk_hz=100e6,
    #         syncin_hz=20e6
    #     )
    #     print(result)
    # except Exception as e:
    #     print(type(e).__name__, e)


    # # ============================================================
    # # 13. INVALID TRIGGER CONFIGURATION
    # # ============================================================

    # print("\n[13] INVALID TRIGGER CONFIGURATION")
    # print("-" * 70)

    # invalid_trigger_tests = [
    #     (
    #         "Internal without period",
    #         lambda: calc_trigger_config(
    #             "internal_100mhz"
    #         )
    #     ),
    #     (
    #         "CLKIN without ext clock",
    #         lambda: calc_trigger_config(
    #             "external_clkin",
    #             period_s=50e-6
    #         )
    #     ),
    #     (
    #         "DUAL without SYNCIN",
    #         lambda: calc_trigger_config(
    #             "external_dual_in",
    #             period_s=10e-6,
    #             ext_clk_hz=100e6
    #         )
    #     ),
    #     (
    #         "Unknown mode",
    #         lambda: calc_trigger_config(
    #             "something_else"
    #         )
    #     ),
    # ]

    # for name, test in invalid_trigger_tests:

    #     try:
    #         result = test()

    #         print(
    #             f"{name:30s} -> "
    #             f"UNEXPECTED SUCCESS: {result}"
    #         )

    #     except Exception as e:

    #         print(
    #             f"{name:30s} -> "
    #             f"{type(e).__name__}: {e}"
    #         )


    # # ============================================================
    # # 14. BURST MODE
    # # ============================================================

    # print("\n[14] BURST MODE")
    # print("-" * 70)

    # burst_tests = [
    #     (1, 1),
    #     (10, 2),
    #     (100, 10),
    #     (65535, 65535),
    #     (0, 0),
    #     (70000, 70000),
    # ]

    # for burst_n, fdiv_n in burst_tests:

    #     result = calc_burst_mode(
    #         burst_n,
    #         fdiv_n
    #     )

    #     print(
    #         f"Burst={burst_n:6d}, "
    #         f"Fdiv={fdiv_n:6d} -> "
    #         f"{result}"
    #     )


    # # ============================================================
    # # END
    # # ============================================================

    # print("\n" + "=" * 70)
    # print("ALL SOFTWARE CALCULATION TESTS COMPLETED")
    # print("=" * 70)
    import math


    # def f28_hz(f_hz):
    #     return f_hz / 28.0


    # def delay_calc_fullres(f_hz, time_s):
    #     """
    #     Datasheet:
    #         TCount = (F / 28) * t
    #         DelayCounter = floor(TCount)

    #         Ddelay = int((fractional_part * 28) + 4)
    #         Adelay = int((fractional_part_of_28 * 13))
    #     """

    #     t_count = f28_hz(f_hz) * time_s

    #     dc_float = math.floor(t_count)

    #     frac28 = (t_count - dc_float) * 28.0

    #     d_delay = int(frac28 + 4.0)

    #     a_delay = int(
    #         (frac28 - math.floor(frac28)) * 13.0
    #     )

    #     return dc_float, frac28, d_delay, a_delay


    # # ============================================================
    # # TEST ONLY THE PROBLEMATIC CASES
    # # ============================================================

    # tests = [
    #     ("2.48 GHz / 100 ns", 2.48e9, 100e-9),
    #     ("3.04 GHz / 100 ns", 3.04e9, 100e-9),
    #     ("3.00 GHz / 100 ns", 3.00e9, 100e-9),
    # ]

    # print("=" * 70)
    # print("DELAY CALCULATION FLOATING-POINT TEST")
    # print("=" * 70)

    # for name, f_hz, time_s in tests:

    #     t_count, frac28, d_delay, a_delay = delay_calc_fullres(
    #         f_hz, time_s
    #     )

    #     print(f"\n{name}")
    #     print("-" * 70)

    #     print(f"F             = {f_hz:.12f} Hz")
    #     print(f"T             = {time_s:.12e} s")

    #     print(f"TCount        = {t_count:.17f}")
    #     print(f"floor(TCount) = {math.floor(t_count)}")

    #     print(f"frac28        = {frac28:.17f}")
    #     print(f"frac28 + 4    = {frac28 + 4.0:.17f}")

    #     print(f"D-delay       = {d_delay}")
    #     print(f"A-delay       = {a_delay}")
    # import math


    # def f28_hz(f_hz):
    #     return f_hz / 28.0


    # for f_hz in [2.48e9, 3.04e9, 3.00e9]:

    #     time_s = 100e-9

    #     t_count = f28_hz(f_hz) * time_s
    #     dc_float = math.floor(t_count)

    #     difference = t_count - dc_float
    #     frac28 = difference * 28.0

    #     print("\nF =", f_hz)

    #     print("repr(t_count)      =", repr(t_count))
    #     print("repr(dc_float)     =", repr(dc_float))
    #     print("repr(difference)   =", repr(difference))
    #     print("repr(frac28)       =", repr(frac28))

    #     print("hex(t_count)       =", t_count.hex())
    #     print("hex(difference)    =", difference.hex())
    #     print("hex(frac28)        =", frac28.hex())
    # import math


    # def f28_hz(f_hz):
    #     return f_hz / 28.0


    # def delay_calc_test(f_hz, time_s):
    #     t_count = f28_hz(f_hz) * time_s
    #     dc = math.floor(t_count)

    #     frac28 = (f_hz * time_s) - (dc * 28.0)

    #     d_delay = int(frac28 + 4.0)

    #     a_delay = int(
    #         (frac28 - math.floor(frac28)) * 13.0
    #     )

    #     return t_count, dc, frac28, d_delay, a_delay


    # tests = [
    #     ("3 GHz / 105.5 ns", 3.0e9, 105.5e-9),
    #     ("3 GHz / 106.0 ns", 3.0e9, 106.0e-9),
    #     ("3 GHz / 106.5 ns", 3.0e9, 106.5e-9),
    #     ("3 GHz / 107.0 ns", 3.0e9, 107.0e-9),

    #     ("2.48 GHz / 100.5 ns", 2.48e9, 100.5e-9),
    # ]


    # print("=" * 70)
    # print("DELAY CALCULATION — FRACTIONAL A-DELAY TEST")
    # print("=" * 70)

    # for name, f_hz, time_s in tests:

    #     t_count, dc, frac28, d_delay, a_delay = \
    #         delay_calc_test(f_hz, time_s)

    #     print(f"\n{name}")
    #     print("-" * 70)
    #     print("TCount        =", repr(t_count))
    #     print("Counter       =", dc)
    #     print("frac28        =", repr(frac28))
    #     print("D-delay       =", d_delay)
    #     print("A-delay       =", a_delay)