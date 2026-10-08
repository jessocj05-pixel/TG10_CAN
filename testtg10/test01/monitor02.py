# sy4000_status.py
import time
import serial

MODE_NAMES = {
    "internal":  "Internal",
    "ext_clk":   "External SINGLE IN - CLK IN",
    "ext_sync":  "External SINGLE IN - SYNC IN",
    "ext_dual":  "External DUAL IN",
    "oneshot":   "One shot trigger (software)",
    "smart":     "One shot trigger  (smart)",
}


# ---------- low level ----------
def _parse_frames(raw: bytes):
    """Split Waveshare stream: AA type ID0..ID3 data.. 55 -> (can_id, rtr, data)"""
    out, i = [], 0
    while i < len(raw) - 6:
        if raw[i] == 0xAA and (raw[i + 1] & 0xE0) == 0xE0 or \
           (raw[i] == 0xAA and (raw[i + 1] & 0xE0) == 0xC0):
            t = raw[i + 1]
            dlc = t & 0x0F
            n = 2 + 4 + dlc + 1
            if i + n <= len(raw) and raw[i + n - 1] == 0x55:
                can_id = int.from_bytes(raw[i + 2:i + 6], "little")
                data = raw[i + 6:i + 6 + dlc]
                out.append((can_id, bool(t & 0x10), data))
                i += n
                continue
        i += 1
    return out


def _rd(ser, reg_id: int, wait=0.08) -> int:
    """Read any register, return little-endian int. Length-agnostic."""
    from main import read_register            # lazy import, avoids circular import
    ser.reset_input_buffer()                # drop stale bytes
    raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=wait) or b""
    for can_id, rtr, data in reversed(_parse_frames(raw)):
        if not rtr and (can_id & 0xFF) == reg_id and len(data) > 0:
            return int.from_bytes(data, "little")
    raise RuntimeError(f"No reply for reg 0x{reg_id:02X}")


def _freq_hz(ser, reg_id):
    """0x76 / 0x77 store kHz x100  -> Hz = value * 10"""
    return _rd(ser, reg_id) * 10.0


def fmt_freq(f):
    if f is None:
        return "n/a"
    if f >= 1e6:
        return f"{f/1e6:.6f} MHz"
    if f >= 1e3:
        return f"{f/1e3:.3f} kHz"
    return f"{f:.3f} Hz"


def fmt_period(p):
    if p is None:
        return "n/a"
    if p < 1e-6:
        return f"{p*1e9:.3f} ns"
    if p < 1e-3:
        return f"{p*1e6:.3f} us"
    if p < 1:
        return f"{p*1e3:.3f} ms"
    return f"{p:.6f} s"


def fmt_delay(total_s: float, F: float) -> str:
    """Pick display granularity like TG10 does: full/D+A/A-only."""
    coarse_step = 28.0 / F      # ~9.33 ns
    fine_step   = 1.0 / F       # ~0.333 ns

    if total_s >= coarse_step:
        return fmt_period(total_s)
    elif total_s >= fine_step:
        return f"{total_s*1e12:.2f} ps"
    else:
        return f"{total_s*1e12:.2f} ps"


# ---------- main ----------
def read_status(ser: serial.Serial, show: bool = True) -> dict:
    osc_mux   = _rd(ser, 0x75)   # 0 internal, 1 external
    rate_clk  = _rd(ser, 0x55)   # 0 int, 1 OPTCLK, 2 OPTCLK/2, 3 SYNCIN
    start_trg = _rd(ser, 0x54)   # 0 rate div, 1 div@OPTCLK, 2 SYNCIN, 3 SYNCIN@OPTCLK, 4 one shot, 5 smart

    # ----- 1. detect mode (start_trg first, it overrides) -----
    if start_trg == 4:
        mode = "oneshot"
    elif start_trg == 5:
        mode = "smart"
    elif osc_mux == 1 and rate_clk == 3:
        mode = "ext_dual"
    elif osc_mux == 1:
        mode = "ext_clk"
    elif rate_clk == 3 or start_trg in (2, 3):
        mode = "ext_sync"
    else:
        mode = "internal"

    # ----- 2. live frequencies, only what mode needs -----
    clk_in_hz = sync_in_hz = None
    clk_label = "CLK IN"

    if mode in ("internal", "ext_sync"):
        clk_in_hz = _rd(ser, 0x11) * 1e6          # internal OscClock (MHz)
        clk_label = "CLK (internal)"
    elif mode in ("ext_clk", "ext_dual"):
        clk_in_hz = _freq_hz(ser, 0x76)
    elif mode in ("oneshot", "smart"):
        if osc_mux == 1:
            clk_in_hz = _freq_hz(ser, 0x76)
        else:
            clk_in_hz = _rd(ser, 0x11) * 1e6
            clk_label = "CLK (internal)"

    if mode in ("ext_sync", "ext_dual"):
        sync_in_hz = _freq_hz(ser, 0x77)


    # ----- 3. output frequency / period -----
    out_hz = out_t = ratediv = rate_clock_hz = None

    if start_trg in (2, 3):                         # trigger = SYNC IN directly
        rate_clock_hz = sync_in_hz if sync_in_hz is not None else _freq_hz(ser, 0x77)
        out_hz = rate_clock_hz
    else:                                           # rate divider path (also oneshot/smart)
        ratediv = max(1, _rd(ser, 0x20))
        if rate_clk == 0:
            rate_clock_hz = 100e6                   # internal rate clock, 10 ns
        elif rate_clk == 1:
            rate_clock_hz = _freq_hz(ser, 0x76)
        elif rate_clk == 2:
            rate_clock_hz = _freq_hz(ser, 0x76) / 2
        else:
            rate_clock_hz = _freq_hz(ser, 0x77)
        out_hz = rate_clock_hz / ratediv if rate_clock_hz else 0.0

    if out_hz:
        out_t = 1.0 / out_hz
    
    res = dict(mode=MODE_NAMES[mode], mode_key=mode,
               osc_clk_mux=osc_mux, rate_clk=rate_clk, start_trg=start_trg,
               clk_in_hz=clk_in_hz, sync_in_hz=sync_in_hz,
               rate_clock_hz=rate_clock_hz, ratediv=ratediv,
               out_hz=out_hz, out_period_s=out_t)

    if show:
        oneshot = mode in ("oneshot", "smart")
        print("=" * 36)
        print(f"Mode          : {res['mode']}")
        tag = "  (rate setting, trigger is manual)" if oneshot else ""
        print(f"Output freq   : {fmt_freq(out_hz)}{tag}")
        print(f"Output period : {fmt_period(out_t)}")
        if ratediv is not None:
            print(f"Ratediv       : {ratediv}")
        if clk_in_hz is not None:
            print(f"{clk_label:<14}: {fmt_freq(clk_in_hz)}")
        if sync_in_hz is not None:
            print(f"SYNC IN       : {fmt_freq(sync_in_hz)}")
        print("=" * 36)
    
    return res



def read_config(ser: serial.Serial, show: bool = True) -> dict:
    conf = _rd(ser, 0x52)          # MuxConfSw

    BURST_SRC = {0: "SYNCIN", 1: "GATE", 2: "nGATE", 3: "Software"}

    mode = trig = count = None

    if conf == 0:
        text = "Idle (fixed config 1)"
    elif conf == 1:
        mode = "NORMAL"
        text = "NORMAL"
    elif conf in (2, 3):
        mode = "BURST" if conf == 2 else "nBURST"
        src = _rd(ser, 0x53)                       # MuxBurstT
        trig = BURST_SRC.get(src, f"Unknown({src})")
        count = _rd(ser, 0x74) & 0xFFFF            # Burst count
        text = f"{mode} -> {trig} -> {count}"
    elif conf == 4:
        mode = "FREQ_DIV"
        count = _rd(ser, 0x69) & 0xFFFF            # F div
        text = f"FREQ_DIV -> {count}"
    elif conf in (5, 6):
        mode = "GATE"
        trig = "GATE" if conf == 5 else "nGATE"
        text = f"GATE -> {trig}"
    else:
        text = f"Unknown (0x52 = {conf})"

    res = dict(conf_raw=conf, mode=mode, trigger=trig, count=count, text=text)

    if show:
        print("=" * 36)
        print(f"Config : {text}")
        print("=" * 36)
    return res


def read_live(ser: serial.Serial, show: bool = True) -> dict:
    """Live input frequencies, always both, straight from hardware counters."""
    clk_hz = _freq_hz(ser, 0x76)      # CLK IN  (CLC IN connector)
    sync_hz = _freq_hz(ser, 0x77)     # SYNC IN

    res = dict(clk_in_hz=clk_hz, sync_in_hz=sync_hz)

    if show:
        print("=" * 36)
        print(f"Live CLK IN  : {fmt_freq(clk_hz)}")
        print(f"Live SYNC IN : {fmt_freq(sync_hz)}")
        print("=" * 36)
    return res

def snap(ser):
    return {r: _rd(ser, r) for r in (0x75, 0x55, 0x54, 0x20, 0x52, 0x10)}



MUX_SET = ["0", "1", "Post-count", "Fine del0", "Fine del1", "Fine del2",
           "Fine del3", "Fine del4", "Fine del5", "Coarse del6",
           "Coarse del7", "Trigger", "Latch SET", "GATE", "nGATE",
           "Delayed res"]
MUX_RES = MUX_SET[:12] + ["Latch RES", "GATE", "nGATE", "Delayed set"]


LOGIC_OUT_REG = {2: 0x7A, 3: 0x7B, 4: 0x7C, 5: 0x7D}

LOGIC_OUT_NAMES = {
    2: ["OUT2", "OUT2 and OUT1", "OUT2 or OUT1", "not OUT1"],
    3: ["OUT3", "OUT3 and OUT2", "OUT3 or OUT2", "not OUT2"],
    4: ["OUT4", "OUT4 and OUT3", "OUT4 or OUT3", "not OUT3"],
    5: ["OUT5", "OUT5 and OUT4", "OUT5 or OUT4", "not OUT4"],
}


# delay source -> counter regs (Delay counter, D delay, A delay, Post counter)
# delay channel n: DelayCnt, Ddly, Adly, PostCnt
DEL_REGS = {
    0: dict(cnt=0x80, d=0x5D, a=0x56, post=0x26),
    1: dict(cnt=0x16, d=0x5E, a=0x57, post=0x27),
    2: dict(cnt=0x19, d=0x5F, a=0x58, post=0x28),
    3: dict(cnt=0x1A, d=0x60, a=0x59, post=0x29),
    4: dict(cnt=0x1B, d=None, a=0x5A, post=0x2A),   # 100 MHz channel, no D delay
    5: dict(cnt=0x1C, d=0x62, a=0x5B, post=0x2B),
    6: dict(cnt=0x1D, d=0x63, a=0x5C, post=0x2C),
    7: dict(cnt=0x1E, d=0x63, a=None, post=0x2D),   # ch 6/7 share A,D regs
}


def _sys_clock_hz(ser):
    """System clock F = OscClock * PLL2 N (0x11 MHz * 0x12)."""
    return _rd(ser, 0x11) * 1e6 * _rd(ser, 0x12)


def _delay_seconds(ser, ch, F):
    r = DEL_REGS[ch]
    cnt = _rd(ser, r["cnt"])
    if ch == 4:
        a = _rd(ser, r["a"]) if r["a"] else 0
        # return (cnt - 3) * 10e-9 + a * 25e-12     # ch4: 10ns/count, offset -3
        return max((cnt - 3) * 10e-9 + a * 25e-12, 0.0)
    t = (cnt - 3) * 28.0 / F                       # <-- offset -3 added
    if r["d"]:
        t += (_rd(ser, r["d"]) - 4) / F
    if r["a"]:
        t += _rd(ser, r["a"]) * 25e-12
        # t += _rd(ser, r["a"]) * 25.64e-12
    return max(t, 0.0)                             # clamp, avoid tiny negative float noise

def _src_text(ser, name, F, cache, block, kind):
    """kind = 'rise' or 'fall'"""
    if name == "0":
        return "NC"
    if name == "1":
        return "Force SET" if kind == "rise" else "Force RESET"
    if name == "Post-count":
        key = ("post", block)
        if key not in cache:
            cnt = _rd(ser, 0x26 + block)        # PostCnt of the same block
            if block == 4:
                cache[key] = cnt * 10e-9          # ch4 domain: 100MHz, 10ns/count
            else:
                cache[key] = cnt * 28.0 / F        # reverted: no offset
        #     cache[key] = cnt * 28.0 / F         # post counter unit = 28/F
        return f"Post-count ({fmt_period(cache[key])})"
        #     cache[key] = max((cnt - 3) * 28.0 / F, 0.0)      # <-- offset -3 added
        # return f"Post-count ({fmt_delay(cache[key], F)})"     # <-- also switch to fmt_delay for ps range
    if name.startswith(("Fine del", "Coarse del")):
        ch = int(name[-1])
        if ch not in cache:
            cache[ch] = _delay_seconds(ser, ch, F)
        return f"{name} ({fmt_delay(cache[ch], F)})"
    # for b in range(8):
    #     print(f"block{b} PostCnt(0x{0x26+b:02X}) = {_rd(ser, 0x26+b)}")
    return name


def read_mux_delay(ser: serial.Serial, blocks=range(8), show: bool = True, fast: bool = False) -> dict:
    F = _sys_clock_hz(ser)
    cache = {}
    res = {}

    for b in blocks:
        base = 0x2E + 4 * b
        raw = {
            "set1": _rd(ser, base),
            "set2": _rd(ser, base + 1),
            "res1": _rd(ser, base + 2),
            "res2": _rd(ser, base + 3),
        }
        block = {
            "conf1_rise": MUX_SET[raw["set1"] & 0x0F],
            "conf2_rise": MUX_SET[raw["set2"] & 0x0F],
            "conf1_fall": MUX_RES[raw["res1"] & 0x0F],
            "conf2_fall": MUX_RES[raw["res2"] & 0x0F],
        }

        if fast:
            rise1, rise2 = block["conf1_rise"], block["conf2_rise"]
            fall1, fall2 = block["conf1_fall"], block["conf2_fall"]
        else:
            rise1 = _src_text(ser, block["conf1_rise"], F, cache, b, "rise")
            rise2 = _src_text(ser, block["conf2_rise"], F, cache, b, "rise")
            fall1 = _src_text(ser, block["conf1_fall"], F, cache, b, "fall")
            fall2 = _src_text(ser, block["conf2_fall"], F, cache, b, "fall")
        # rise1 = _src_text(ser, block["conf1_rise"], F, cache, b, "rise")
        # rise2 = _src_text(ser, block["conf2_rise"], F, cache, b, "rise")
        # fall1 = _src_text(ser, block["conf1_fall"], F, cache, b, "fall")
        # fall2 = _src_text(ser, block["conf2_fall"], F, cache, b, "fall")

        entry = {
            "block": b,"conf1": {"rise": rise1, "fall": fall1},
            "conf2": {"rise": rise2, "fall": fall2},
        }

        if b in LOGIC_OUT_REG:
            reg = LOGIC_OUT_REG[b]
            val = _rd(ser, reg) & 0x03
            entry["logic_out"] = {"reg": reg, "raw": val, "text": LOGIC_OUT_NAMES[b][val]}

        res[b] = entry

        if show:
            print(f"--- OUT block {b} ---")
            print(f"  Config 1: RISE = {rise1:<28} FALL = {fall1}")
            print(f"  Config 2: RISE = {rise2:<28} FALL = {fall2}")
            if "logic_out" in entry:
                lo = entry["logic_out"]
                print(f"  Logic OUT: {lo['text']}")
    return res



def read_run_status(ser: serial.Serial) -> str:
    """Reg 0x10 Command: 0=OFF, 1=ON, 2=FAULT"""
    val = _rd(ser, 0x10)
    return {0: "OFF", 1: "ON", 2: "FAULT"}.get(val, f"UNKNOWN({val})")



def dump_delay_regs(ser, ch: int):
    r = DEL_REGS[ch]
    cnt = _rd(ser, r["cnt"])
    d = _rd(ser, r["d"]) if r["d"] else None
    a = _rd(ser, r["a"]) if r["a"] else None
    print(f"ch{ch}: DelayCnt(0x{r['cnt']:02X})={cnt}  Ddly={d}  Adly={a}")




def read_logic_out(ser: serial.Serial, outs=(2, 3, 4, 5), show: bool = True) -> dict:
    """Read OUT2..OUT5 logic mux (AND/OR/NOT with neighbor). Only these 4 have it."""
    res = {}
    for n in outs:
        if n not in LOGIC_OUT_REG:
            continue
        reg = LOGIC_OUT_REG[n]
        val = _rd(ser, reg) & 0x03
        name = LOGIC_OUT_NAMES[n][val]
        res[n] = dict(reg=reg, raw=val, text=name)

        if show:
            print(f"OUT{n} Logic (0x{reg:02X}) : {val} -> {name}")
    return res

