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


def _rd(ser, reg_id: int, wait=0.3) -> int:
    """Read any register, return little-endian int. Length-agnostic."""
    from v5 import read_register            # lazy import, avoids circular import
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

    if mode in ("oneshot", "smart"):
        pass                                        # no repetition rate
    elif start_trg in (2, 3):                       # trigger = SYNC IN directly
        rate_clock_hz = sync_in_hz
        out_hz = sync_in_hz
    else:
        ratediv = max(1, _rd(ser, 0x20))
        if rate_clk == 0:
            rate_clock_hz = 100e6                   # internal rate clock fixed 10 ns
        elif rate_clk == 1:
            rate_clock_hz = _freq_hz(ser, 0x76)
        elif rate_clk == 2:
            rate_clock_hz = _freq_hz(ser, 0x76) / 2
        else:
            rate_clock_hz = _freq_hz(ser, 0x77)
        out_hz = rate_clock_hz / ratediv

    if out_hz:
        out_t = 1.0 / out_hz

    res = dict(mode=MODE_NAMES[mode], mode_key=mode,
               osc_clk_mux=osc_mux, rate_clk=rate_clk, start_trg=start_trg,
               clk_in_hz=clk_in_hz, sync_in_hz=sync_in_hz,
               rate_clock_hz=rate_clock_hz, ratediv=ratediv,
               out_hz=out_hz, out_period_s=out_t)

    if show:
        print("=" * 36)
        print(f"Mode          : {res['mode']}")
        print(f"Output freq   : {fmt_freq(out_hz)}")
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