import serial
from typing import Dict, Any, Optional
from v5 import read_register


# ============================================================
# Low-level helpers (silent)
# ============================================================

def _extract_payload(raw: bytes, reg_id: int, dlc: int) -> bytes:
    """
    Extract data from the real Waveshare frame format:
        aa <flags> <reg_id> 20 e0 1f <data...> 55
    """
    i = 0
    while i < len(raw) - (4 + dlc):
        if (raw[i] == 0xAA and
            raw[i+1] in (0xE1, 0xC1, 0xE2, 0xC2, 0xE4, 0xC4) and
            raw[i+2] == reg_id):
            end = raw.find(b'\x55', i + 3)
            if end != -1:
                payload = raw[end - dlc : end]
                if len(payload) == dlc:
                    return payload
        i += 1
    raise RuntimeError(f"Register 0x{reg_id:02X} (DLC={dlc}) not found")


def _read_u8(ser: serial.Serial, reg_id: int) -> int:
    raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.35)
    return _extract_payload(raw, reg_id, 1)[0]


def _read_u16(ser: serial.Serial, reg_id: int) -> int:
    raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.35)
    return int.from_bytes(_extract_payload(raw, reg_id, 2), 'little')


def _read_u32(ser: serial.Serial, reg_id: int) -> int:
    raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.35)
    return int.from_bytes(_extract_payload(raw, reg_id, 4), 'little')


def _read_freq_hz(ser: serial.Serial, reg_id: int) -> float:
    """Read frequency register that stores value ×100 as kHz → returns Hz"""
    value = _read_u32(ser, reg_id)
    return (value / 100.0) * 1000.0          # → Hz


# ============================================================
# 1. Output Frequency (the value shown by the Freq button)
# ============================================================

def read_output_frequency(ser: serial.Serial, show: bool = True) -> Dict[str, Any]:
    """
    Read current output frequency of the rate generator.
    Returns frequency in Hz + nice human string.
    """
    # --- detect rate clock source ---
    osc_clk_mux = _read_u8(ser, 0x75)   # 0=Internal, 1=External
    rate_clk    = _read_u8(ser, 0x55)   # 0=Int, 1=OPTCLK, 2=OPTCLK/2, 3=SYNCIN
    start_trg   = _read_u8(ser, 0x54)

    rate_clock_hz = None
    mode = "Unknown"

    if start_trg in (4, 5):
        mode = "One-shot"
        rate_clock_hz = _read_u8(ser, 0x11) * 1e6          # OscClock
    elif osc_clk_mux == 0 and rate_clk == 0:
        mode = "Internal"
        rate_clock_hz = _read_u8(ser, 0x11) * 1e6
    elif rate_clk == 1:
        mode = "OPTCLK"
        rate_clock_hz = _read_freq_hz(ser, 0x76)
    elif rate_clk == 2:
        mode = "OPTCLK/2"
        rate_clock_hz = _read_freq_hz(ser, 0x76) / 2.0
    elif rate_clk == 3:
        mode = "SYNCIN" if osc_clk_mux == 0 else "External DUAL-IN"
        rate_clock_hz = _read_freq_hz(ser, 0x77)
    else:
        # fallback
        rate_clock_hz = _read_u8(ser, 0x11) * 1e6
        mode = f"Fallback (0x75={osc_clk_mux}, 0x55={rate_clk})"

    # --- Ratediv ---
    ratediv = max(1, _read_u32(ser, 0x20))

    freq_hz = rate_clock_hz / ratediv
    period_s = 1.0 / freq_hz

    # human readable
    if freq_hz >= 1_000_000:
        freq_str = f"{freq_hz/1e6:.6f} MHz"
    elif freq_hz >= 1000:
        freq_str = f"{freq_hz/1000:.3f} kHz"
    else:
        freq_str = f"{freq_hz:.3f} Hz"

    result = {
        "mode": mode,
        "rate_clock_hz": rate_clock_hz,
        "ratediv": ratediv,
        "freq_hz": freq_hz,
        "period_s": period_s,
        "freq_str": freq_str,
    }

    if show:
        print("\n=== Output Frequency ===")
        print(f"Mode            : {mode}")
        print(f"Rate clock      : {rate_clock_hz:,.1f} Hz")
        print(f"Ratediv (0x20)  : {ratediv}")
        print(f"Output Frequency: {freq_str}")
        print(f"Period          : {period_s*1e9:.1f} ns")
        print("=" * 32)

    return result


# ============================================================
# 2. Sync / Trigger Mode
# ============================================================

def read_sync_mode(ser: serial.Serial, show: bool = True) -> Dict[str, Any]:
    """
    Read current synchronization / trigger mode.
    """
    osc_clk_mux = _read_u8(ser, 0x75)   # Optical clock mux
    rate_clk    = _read_u8(ser, 0x55)   # MuxRateClk
    start_trg   = _read_u8(ser, 0x54)   # MuxStartTrg

    if start_trg == 4:
        mode = "One-shot trigger"
    elif start_trg == 5:
        mode = "One-shot smart"
    elif osc_clk_mux == 0 and rate_clk == 0:
        mode = "Internal"
    elif osc_clk_mux == 1 and rate_clk == 1:
        mode = "External SINGLE – CLK IN"
    elif rate_clk == 3 and osc_clk_mux == 0:
        mode = "External SINGLE – SYNC IN"
    elif osc_clk_mux == 1 and rate_clk == 3:
        mode = "External DUAL-IN"
    elif rate_clk == 1:
        mode = "OPTCLK"
    elif rate_clk == 2:
        mode = "OPTCLK / 2"
    else:
        mode = f"Unknown (0x75={osc_clk_mux}, 0x55={rate_clk}, 0x54={start_trg})"

    result = {
        "mode": mode,
        "osc_clk_mux": osc_clk_mux,
        "rate_clk": rate_clk,
        "start_trg": start_trg,
    }

    if show:
        print("\n=== Sync / Trigger Mode ===")
        print(f"Mode            : {mode}")
        print(f"0x75 OscClkMux  : {osc_clk_mux}  ({'External' if osc_clk_mux else 'Internal'})")
        print(f"0x55 MuxRateClk : {rate_clk}")
        print(f"0x54 MuxStartTrg: {start_trg}")
        print("=" * 32)

    return result


# ============================================================
# 3. Live parameters (CLK IN / SYNC IN) – mode-aware
# ============================================================

def read_live_frequencies(ser: serial.Serial, show: bool = True) -> Dict[str, Any]:
    """
    Read live CLK IN and SYNC IN frequencies.
    Automatically decides what is valid according to current mode.
    """
    sync_info = read_sync_mode(ser, show=False)
    mode = sync_info["mode"]

    clk_in_hz  = None
    sync_in_hz = None

    # Always safe to try reading both (they just return 0 if not used)
    try:
        clk_in_hz = _read_freq_hz(ser, 0x76)
    except Exception:
        pass

    try:
        sync_in_hz = _read_freq_hz(ser, 0x77)
    except Exception:
        pass

    result = {
        "mode": mode,
        "clk_in_hz": clk_in_hz,
        "sync_in_hz": sync_in_hz,
    }

    if show:
        print("\n=== Live Frequencies ===")
        print(f"Current mode    : {mode}")
        if clk_in_hz is not None:
            print(f"CLK IN  (0x76)  : {clk_in_hz/1000:.2f} kHz")
        if sync_in_hz is not None:
            print(f"SYNC IN (0x77)  : {sync_in_hz/1000:.2f} kHz")
        print("=" * 32)

    return result


# ============================================================
# 4. Burst / Configuration Mode
# ============================================================

def read_burst_config(ser: serial.Serial, show: bool = True) -> Dict[str, Any]:
    """
    Read current burst / gate / frequency-divider configuration.
    """
    mux_conf_sw = _read_u8(ser, 0x52)
    mux_burst_t = _read_u8(ser, 0x53)
    burst_count = _read_u32(ser, 0x74) & 0xFFFF   # device returns 4 bytes
    fdiv        = _read_u16(ser, 0x69)

    if mux_conf_sw == 1:
        mode = "CONFIG_NORMAL_SEQUENCE"
        desc = "Normal continuous"
    elif mux_conf_sw == 5:
        mode = "CONFIG_GATE_GATE_SEQUENCE"
        desc = "Gated by GATE"
    elif mux_conf_sw == 6:
        mode = "CONFIG_N_GATE_SEQUENCE"
        desc = "Gated by nGATE"
    elif mux_conf_sw == 4:
        mode = "CONFIG_FREQ_DIV_xxx"
        desc = f"Frequency divider (Fdiv={fdiv})"
    elif mux_conf_sw == 2:
        src = {0: "SYNCIN", 1: "GATE", 2: "nGATE", 3: "SOFTWARE"}.get(mux_burst_t, "?")
        mode = {
            0: "CONFIG_BURST_SYNCIN",
            1: "CONFIG_BURST_GATE",
            2: "CONFIG_BURST_NGATE",
            3: "CONFIG_BURST_SOFTWARE",
        }.get(mux_burst_t, f"CONFIG_BURST_UNKNOWN_{mux_burst_t}")
        desc = f"Burst – source={src}, count={burst_count}, Fdiv={fdiv}"
    else:
        mode = f"UNKNOWN_0x{mux_conf_sw:02X}"
        desc = "Unknown configuration"

    result = {
        "mode": mode,
        "mux_conf_sw": mux_conf_sw,
        "mux_burst_t": mux_burst_t,
        "burst_count": burst_count,
        "fdiv": fdiv,
        "description": desc,
    }

    if show:
        print("\n=== Burst / Config Mode ===")
        print(f"Mode            : {mode}")
        print(f"MuxConfSw (0x52): {mux_conf_sw}")
        print(f"MuxBurstT (0x53): {mux_burst_t}")
        print(f"Burst count     : {burst_count}")
        print(f"Fdiv (0x69)     : {fdiv}")
        print(f"Description     : {desc}")
        print("=" * 32)

    return result