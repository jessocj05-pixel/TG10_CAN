# sy4000_calc.py
import math

ALLOWED_NDIV = [
    30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60,
    62, 64, 66, 68, 70, 72, 76, 78, 80, 84, 88, 90, 92, 96, 98, 100,
    102, 104, 108, 110, 112, 116, 120, 124
]

def parse_time(t: str) -> float:
    t = str(t).strip().lower().replace(" ", "")
    if t.endswith("ns"): return float(t[:-2]) * 1e-9
    if t.endswith(("us", "µs")): return float(t[:-2]) * 1e-6
    if t.endswith("ms"): return float(t[:-2]) * 1e-3
    if t.endswith("s"): return float(t[:-1])
    return float(t) * 1e-9

def parse_freq(f: str) -> float:
    f = str(f).strip().lower().replace(" ", "")
    if f.endswith("mhz"): return float(f[:-3]) * 1e6
    if f.endswith("khz"): return float(f[:-3]) * 1e3
    if f.endswith("hz"): return float(f[:-2])
    return float(f)

def calc_pll2(ext_freq_mhz: float):
    osc_clock = round(ext_freq_mhz)
    target = 3000 / ext_freq_mhz
    ndiv = min(ALLOWED_NDIV, key=lambda x: abs(x - target))
    if 2920 <= ext_freq_mhz * ndiv <= 3080:
        return ndiv, 1, osc_clock          # 3 GHz
    target = 2500 / ext_freq_mhz
    ndiv = min(ALLOWED_NDIV, key=lambda x: abs(x - target))
    return ndiv, 0, osc_clock              # 2.5 GHz

def calc_ratediv(period_s: float, source_freq_hz: float) -> int:
    return max(1, round(source_freq_hz * period_s))

def calc_delay(time_s: float, f_sys_hz: float):
    tcount = (f_sys_hz / 28.0) * time_s
    delay_cnt = math.floor(tcount)
    frac = tcount - delay_cnt
    d_delay = int(frac * 28 + 4)
    a_delay = int((frac * 28 - math.floor(frac * 28)) * 13)
    return delay_cnt, max(4, min(32, d_delay)), max(0, min(23, a_delay))

def calc_postcnt(width_s: float, f_sys_hz: float) -> int:
    return max(1, round(width_s * f_sys_hz))