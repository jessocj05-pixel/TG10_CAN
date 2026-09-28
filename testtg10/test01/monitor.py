"""
monitor.py – Live parameter reader for SY4000 / TG10
Based 100% on the tested & working sy4000_status.py logic.
"""

from __future__ import annotations
import time
import serial
from typing import Any

# ---------------------------------------------------------------------------
# Mode names (same as your working file)
# ---------------------------------------------------------------------------
MODE_NAMES = {
    "internal":  "Internal",
    "ext_clk":   "External SINGLE IN - CLK IN",
    "ext_sync":  "External SINGLE IN - SYNC IN",
    "ext_dual":  "External DUAL IN",
    "oneshot":   "One shot trigger (software)",
    "smart":     "One shot trigger  (smart)",
}

# ---------------------------------------------------------------------------
# Low-level helpers (taken directly from your working file)
# ---------------------------------------------------------------------------
def _parse_frames(raw: bytes):
    """Split Waveshare stream: AA type ID0..ID3 data.. 55 -> (can_id, rtr, data)"""
    out, i = [], 0
    while i < len(raw) - 6:
        if raw[i] == 0xAA and ((raw[i + 1] & 0xE0) == 0xE0 or (raw[i + 1] & 0xE0) == 0xC0):
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


def _rd(ser: serial.Serial, reg_id: int, wait: float = 0.3) -> int:
    """Read any register, return little-endian int. Length-agnostic."""
    # Build and send a remote frame ourselves (no dependency on v5)
    from main import make_id, send_remote_frame, read_echo   # reuse from main.py

    ser.reset_input_buffer()
    can_id = make_id(reg_id, code=0x10)          # CODE_REQ
    send_remote_frame(ser, can_id, dlc=0)
    raw = read_echo(ser, timeout=wait) or b""

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
    coarse_step = 28.0 / F
    fine_step   = 1.0 / F
    if total_s >= coarse_step:
        return fmt_period(total_s)
    return f"{total_s*1e12:.2f} ps"


# ---------------------------------------------------------------------------
# Status / Config / Live (exact logic from your working file)
# ---------------------------------------------------------------------------
def read_status(ser: serial.Serial, show: bool = True) -> dict:
    osc_mux   = _rd(ser, 0x75)
    rate_clk  = _rd(ser, 0x55)
    start_trg = _rd(ser, 0x54)

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

    clk_in_hz = sync_in_hz = None
    clk_label = "CLK IN"

    if mode in ("internal", "ext_sync"):
        clk_in_hz = _rd(ser, 0x11) * 1e6
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

    out_hz = out_t = ratediv = rate_clock_hz = None

    if start_trg in (2, 3):
        rate_clock_hz = sync_in_hz if sync_in_hz is not None else _freq_hz(ser, 0x77)
        out_hz = rate_clock_hz
    else:
        ratediv = max(1, _rd(ser, 0x20))
        if rate_clk == 0:
            rate_clock_hz = 100e6
        elif rate_clk == 1:
            rate_clock_hz = _freq_hz(ser, 0x76)
        elif rate_clk == 2:
            rate_clock_hz = _freq_hz(ser, 0x76) / 2
        else:
            rate_clock_hz = _freq_hz(ser, 0x77)
        out_hz = rate_clock_hz / ratediv if rate_clock_hz else 0.0

    if out_hz:
        out_t = 1.0 / out_hz

    res = dict(
        mode=MODE_NAMES[mode], mode_key=mode,
        osc_clk_mux=osc_mux, rate_clk=rate_clk, start_trg=start_trg,
        clk_in_hz=clk_in_hz, sync_in_hz=sync_in_hz,
        rate_clock_hz=rate_clock_hz, ratediv=ratediv,
        out_hz=out_hz, out_period_s=out_t
    )

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
    conf = _rd(ser, 0x52)
    BURST_SRC = {0: "SYNCIN", 1: "GATE", 2: "nGATE", 3: "Software"}

    mode = trig = count = None

    if conf == 0:
        text = "Idle (fixed config 1)"
    elif conf == 1:
        mode = "NORMAL"
        text = "NORMAL"
    elif conf in (2, 3):
        mode = "BURST" if conf == 2 else "nBURST"
        src = _rd(ser, 0x53)
        trig = BURST_SRC.get(src, f"Unknown({src})")
        count = _rd(ser, 0x74) & 0xFFFF
        text = f"{mode} -> {trig} -> {count}"
    elif conf == 4:
        mode = "FREQ_DIV"
        count = _rd(ser, 0x69) & 0xFFFF
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
    clk_hz  = _freq_hz(ser, 0x76)
    sync_hz = _freq_hz(ser, 0x77)
    res = dict(clk_in_hz=clk_hz, sync_in_hz=sync_hz)

    if show:
        print("=" * 36)
        print(f"Live CLK IN  : {fmt_freq(clk_hz)}")
        print(f"Live SYNC IN : {fmt_freq(sync_hz)}")
        print("=" * 36)
    return res


def read_run_status(ser: serial.Serial) -> str:
    val = _rd(ser, 0x10)
    return {0: "OFF", 1: "ON", 2: "FAULT"}.get(val, f"UNKNOWN({val})")


# ---------------------------------------------------------------------------
# Live loop (simple version that matches your working style)
# ---------------------------------------------------------------------------
def live_monitor(ser: serial.Serial, interval: float = 1.0, full: bool = False):
    """Simple live refresh – same logic as your tested file."""
    print("Live monitor started (Ctrl-C to stop)\n")
    try:
        while True:
            print("\033[2J\033[H", end="")          # clear screen
            print(f"SY4000 Live Monitor  {time.strftime('%H:%M:%S')}")
            print("-" * 40)

            print(f"Run status : {read_run_status(ser)}")
            read_status(ser, show=True)
            read_config(ser, show=True)
            read_live(ser, show=True)

            if full:
                # You can later add read_mux_delay here if you want
                pass

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n(monitor stopped)")


# ---------------------------------------------------------------------------
# Convenience entry
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("port", help="COM port")
    ap.add_argument("--baud", type=int, default=2000000)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()

    with serial.Serial(args.port, args.baud, timeout=0.5) as ser:
        live_monitor(ser, interval=args.interval, full=args.full)