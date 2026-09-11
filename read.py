import serial
from typing import Dict, Any
from v5 import read_register

def read_osc_clk(ser: serial.Serial) -> float:
    """
    Read OscClock (Reg 0x11) from the SY4000.
    Works with Waveshare USB-CAN-A variable-length protocol.
    Returns frequency in MHz.
    """
    raw = read_register(ser, reg_id=0x11, subscribe=False, wait=0.5)

    if not raw:
        raise RuntimeError("No data received from device")

    # Search for the frame that answers register 0x11
    # Pattern: AA E1 11 .... 64 55   (or any DLC=1 frame for reg 0x11)
    i = 0
    while i < len(raw) - 6:
        if (raw[i] == 0xAA and
            raw[i+1] == 0xE1 and          # extended + data + DLC=1
            raw[i+2] == 0x11):            # RegID = 0x11

            # Find the end marker 0x55
            end = raw.find(b'\x55', i + 3)
            if end != -1:
                data_byte = raw[end - 1]  # byte just before 0x55
                osc_mhz = data_byte
                print(f"Device OscClock = {osc_mhz} MHz")
                return float(osc_mhz)
        i += 1

    raise RuntimeError("OscClock (Reg 0x11) frame not found in the reply")


def get_current_rate_clock_freq(ser: serial.Serial) -> dict:
    """
    Detects the current clock configuration and returns the relevant frequencies.

    Special case – External dual-in:
        Reg 0x75 == 0x01  (Optical clock mux = External)
        Reg 0x55 == 0x03  (MuxRateClk      = SYNCIN)
        → read BOTH 0x76 (OscInF) and 0x77 (SYNCINF)

    Returns a dictionary with all useful information.
    """
    # ----------------------------------------------------------
    # Helper to read a single-byte register
    # ----------------------------------------------------------
    def read_u8(reg_id: int) -> int:
        raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
        i = 0
        while i < len(raw) - 5:
            if (raw[i] == 0xAA and
                raw[i+1] in (0xE1, 0xC1) and   # DLC = 1
                raw[i+2] == reg_id):
                end = raw.find(b'\x55', i + 3)
                if end != -1:
                    return raw[end - 1]
            i += 1
        raise RuntimeError(f"Could not read register 0x{reg_id:02X}")

    # ----------------------------------------------------------
    # 1. Read the two control registers
    # ----------------------------------------------------------
    osc_clk_mux = read_u8(0x75)   # Optical clock mux
    rate_clk    = read_u8(0x55)   # MuxRateClk

    print(f"Optical clock mux (0x75) = 0x{osc_clk_mux:02X}")
    print(f"MuxRateClk        (0x55) = 0x{rate_clk:02X}")

    result = {
        "osc_clk_mux": osc_clk_mux,
        "rate_clk": rate_clk,
        "mode": None,
        "freq_hz": None,          # main frequency for Ratediv calculation
        "osc_inf_hz": None,       # 0x76
        "sync_inf_hz": None,      # 0x77
    }

    # ----------------------------------------------------------
    # 2. Decide the mode
    # ----------------------------------------------------------
    if osc_clk_mux == 0x01 and rate_clk == 0x03:
        # ===== External dual-in =====
        result["mode"] = "External dual-in"
        print("→ Mode: External dual-in  (reading both 0x76 and 0x77)")

        osc_inf  = _read_u32_freq(ser, 0x76)   # CLK IN frequency
        sync_inf = _read_u32_freq(ser, 0x77)   # SYNC IN frequency

        result["osc_inf_hz"]  = osc_inf
        result["sync_inf_hz"] = sync_inf
        result["freq_hz"]     = sync_inf       # SYNCIN is the rate source

    elif rate_clk == 0x00:
        result["mode"] = "Internal"
        osc_mhz = read_osc_clk(ser)
        result["freq_hz"] = osc_mhz * 1e6

    elif rate_clk == 0x01:
        result["mode"] = "OPTCLK"
        result["osc_inf_hz"] = _read_u32_freq(ser, 0x76)
        result["freq_hz"] = result["osc_inf_hz"]

    elif rate_clk == 0x02:
        result["mode"] = "OPTCLK/2"
        result["osc_inf_hz"] = _read_u32_freq(ser, 0x76)
        result["freq_hz"] = result["osc_inf_hz"] / 2.0

    elif rate_clk == 0x03:
        result["mode"] = "SYNCIN"
        result["sync_inf_hz"] = _read_u32_freq(ser, 0x77)
        result["freq_hz"] = result["sync_inf_hz"]

    else:
        raise RuntimeError(f"Unknown combination: 0x75={osc_clk_mux}, 0x55={rate_clk}")

    return result


def _read_u32_freq(ser: serial.Serial, reg_id: int) -> float:
    """Read u32 frequency register and return Hz (device stores value ×100 as kHz)."""
    raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
    i = 0
    while i < len(raw) - 8:
        if (raw[i] == 0xAA and
            raw[i+1] in (0xE4, 0xC4) and   # DLC = 4
            raw[i+2] == reg_id):
            end = raw.find(b'\x55', i + 3)
            if end != -1 and end >= i + 7:
                data = raw[end-4:end]
                value = int.from_bytes(data, 'little')
                freq_khz = value / 100.0
                print(f"  Reg 0x{reg_id:02X} = {freq_khz:.2f} kHz")
                return freq_khz * 1000.0
        i += 1
    raise RuntimeError(f"Could not read frequency register 0x{reg_id:02X}")



def get_current_rate_clock_freq(ser: serial.Serial) -> dict:
    """
    Detects the current Sync / Trigger mode of the SY4000
    and returns the frequencies needed for Ratediv calculation.
    """
    def read_u8(reg_id: int) -> int:
        raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
        i = 0
        while i < len(raw) - 5:
            if (raw[i] == 0xAA and raw[i+1] in (0xE1, 0xC1) and raw[i+2] == reg_id):
                end = raw.find(b'\x55', i + 3)
                if end != -1:
                    return raw[end - 1]
            i += 1
        raise RuntimeError(f"Could not read register 0x{reg_id:02X}")

    # ---- read the three key registers ----
    osc_clk_mux = read_u8(0x75)   # Optical clock mux
    rate_clk    = read_u8(0x55)   # MuxRateClk
    start_trg   = read_u8(0x54)   # MuxStartTrg

    print(f"0x75 Optical clock mux = {osc_clk_mux}")
    print(f"0x55 MuxRateClk        = {rate_clk}")
    print(f"0x54 MuxStartTrg       = {start_trg}")

    result = {
        "osc_clk_mux": osc_clk_mux,
        "rate_clk": rate_clk,
        "start_trg": start_trg,
        "mode": None,
        "freq_hz": None,
        "osc_inf_hz": None,
        "sync_inf_hz": None,
    }

    # ------------------------------------------------------------------
    # Mode detection according to official description + register map
    # ------------------------------------------------------------------
    if start_trg in (4, 5):
        result["mode"] = "One shot trigger" if start_trg == 4 else "One shot smart"
        # still give a usable clock
        result["freq_hz"] = read_osc_clk(ser) * 1e6

    elif osc_clk_mux == 0 and rate_clk == 0:
        result["mode"] = "Internal"
        result["freq_hz"] = read_osc_clk(ser) * 1e6

    elif osc_clk_mux == 1 and rate_clk == 1:
        result["mode"] = "External SINGLE IN – CLK IN"
        result["osc_inf_hz"] = _read_u32_freq(ser, 0x76)
        result["freq_hz"] = result["osc_inf_hz"]

    elif rate_clk == 3 and osc_clk_mux != 1:
        result["mode"] = "External SINGLE IN – SYNC IN"
        result["sync_inf_hz"] = _read_u32_freq(ser, 0x77)
        result["freq_hz"] = result["sync_inf_hz"]

    elif osc_clk_mux == 1 and rate_clk == 3:
        # ===== External DUAL IN =====
        result["mode"] = "External DUAL IN"
        print("→ External DUAL IN – reading both CLK IN (0x76) and SYNC IN (0x77)")
        result["osc_inf_hz"]  = _read_u32_freq(ser, 0x76)
        result["sync_inf_hz"] = _read_u32_freq(ser, 0x77)
        result["freq_hz"]     = result["sync_inf_hz"]   # rate divider is driven by SYNC IN

    else:
        result["mode"] = f"Unknown combination (0x75={osc_clk_mux}, 0x55={rate_clk}, 0x54={start_trg})"
        # fallback
        if rate_clk == 0:
            result["freq_hz"] = read_osc_clk(ser) * 1e6
        elif rate_clk in (1, 2):
            result["osc_inf_hz"] = _read_u32_freq(ser, 0x76)
            result["freq_hz"] = result["osc_inf_hz"] / (2 if rate_clk == 2 else 1)
        elif rate_clk == 3:
            result["sync_inf_hz"] = _read_u32_freq(ser, 0x77)
            result["freq_hz"] = result["sync_inf_hz"]

    return result


def _read_u32_freq(ser: serial.Serial, reg_id: int) -> float:
    """Read u32 frequency register → Hz (device stores value × 100 as kHz)."""
    raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
    i = 0
    while i < len(raw) - 8:
        if (raw[i] == 0xAA and raw[i+1] in (0xE4, 0xC4) and raw[i+2] == reg_id):
            end = raw.find(b'\x55', i + 3)
            if end != -1 and end >= i + 7:
                value = int.from_bytes(raw[end-4:end], 'little')
                freq_khz = value / 100.0
                print(f"  Reg 0x{reg_id:02X} = {freq_khz:.2f} kHz")
                return freq_khz * 1000.0
        i += 1
    raise RuntimeError(f"Could not read frequency register 0x{reg_id:02X}")


def read_output_frequency(ser: serial.Serial) -> dict:
    """
    Reads the current output frequency / period of the rate generator
    (the value shown when the user presses the Freq button).

    Returns
    -------
    dict
        {
            "mode"          : str,
            "rate_clock_hz" : float,   # frequency that clocks the rate divider
            "ratediv"       : int,     # register 0x20
            "freq_hz"       : float,   # actual output frequency
            "period_s"      : float,   # actual output period in seconds
        }
    """
    # 1. Get the current rate-clock frequency and mode
    info = get_current_rate_clock_freq(ser)
    rate_clock_hz = info["freq_hz"]

    if rate_clock_hz is None or rate_clock_hz <= 0:
        raise RuntimeError("Could not determine rate-clock frequency")

    # 2. Read Ratediv (register 0x20) – u32
    ratediv = _read_u32(ser, 0x20)

    if ratediv < 1:
        ratediv = 1          # safety

    # 3. Calculate output frequency and period
    out_freq_hz = rate_clock_hz / ratediv
    out_period_s = 1.0 / out_freq_hz

    result = {
        "mode":          info["mode"],
        "rate_clock_hz": rate_clock_hz,
        "ratediv":       ratediv,
        "freq_hz":       out_freq_hz,
        "period_s":      out_period_s,
    }

    # Nice print-out
    print("\n=== Output Frequency (Freq button) ===")
    print(f"Mode            : {result['mode']}")
    print(f"Rate-clock      : {result['rate_clock_hz']:,.3f} Hz")
    print(f"Ratediv (0x20)  : {result['ratediv']}")
    print(f"Output Frequency: {result['freq_hz']:,.6f} Hz")
    print(f"Output Period   : {result['period_s']*1e9:,.3f} ns "
          f"({result['period_s']*1e6:,.3f} µs)")
    print("=" * 40)

    return result


def _read_u32(ser: serial.Serial, reg_id: int) -> int:
    """Read a plain u32 register (little-endian)."""
    raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
    i = 0
    while i < len(raw) - 8:
        if (raw[i] == 0xAA and
            raw[i+1] in (0xE4, 0xC4) and          # DLC = 4
            raw[i+2] == reg_id):
            end = raw.find(b'\x55', i + 3)
            if end != -1 and end >= i + 7:
                data = raw[end-4:end]
                return int.from_bytes(data, 'little')
        i += 1
    raise RuntimeError(f"Could not read u32 register 0x{reg_id:02X}")

def _read_u8(ser: serial.Serial, reg_id: int) -> int:
    """Read a single-byte (u8) register."""
    raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
    i = 0
    while i < len(raw) - 5:
        if (raw[i] == 0xAA and
            raw[i+1] in (0xE1, 0xC1) and
            raw[i+2] == reg_id):
            end = raw.find(b'\x55', i + 3)
            if end != -1:
                return raw[end - 1]
        i += 1
    raise RuntimeError(f"Could not read u8 register 0x{reg_id:02X}")


def _read_u16(ser: serial.Serial, reg_id: int) -> int:
    """Read a u16 register (little-endian)."""
    raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
    i = 0
    while i < len(raw) - 6:
        if (raw[i] == 0xAA and
            raw[i+1] in (0xE2, 0xC2) and          # DLC = 2
            raw[i+2] == reg_id):
            end = raw.find(b'\x55', i + 3)
            if end != -1 and end >= i + 5:
                return int.from_bytes(raw[end-2:end], 'little')
        i += 1
    raise RuntimeError(f"Could not read u16 register 0x{reg_id:02X}")


def _read_u32(ser: serial.Serial, reg_id: int) -> int:
    """Read a u32 register (little-endian).  (kept for compatibility)"""
    raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
    i = 0
    while i < len(raw) - 8:
        if (raw[i] == 0xAA and
            raw[i+1] in (0xE4, 0xC4) and
            raw[i+2] == reg_id):
            end = raw.find(b'\x55', i + 3)
            if end != -1 and end >= i + 7:
                return int.from_bytes(raw[end-4:end], 'little')
        i += 1
    raise RuntimeError(f"Could not read u32 register 0x{reg_id:02X}")


def get_burst_config(ser: serial.Serial) -> Dict[str, Any]:
    """
    Read the current burst / configuration mode of the SY4000.

    Registers used
    --------------
    0x52  MuxConfSw   → main mode selector
    0x53  MuxBurstT   → burst trigger source (only meaningful when MuxConfSw == Burst)
    0x74  BatchC      → burst count
    0x69  Fdiv        → frequency divider

    Returns
    -------
    dict with keys:
        mode            – human readable string
        mux_conf_sw     – raw value of 0x52
        mux_burst_t     – raw value of 0x53 (or None)
        burst_count     – value of 0x74
        fdiv            – value of 0x69
        description     – short explanation
    """
    # ------------------------------------------------------------------
    # 1. Read the key registers
    # ------------------------------------------------------------------
    mux_conf_sw = _read_u8(ser, 0x52)          # MuxConfSw
    mux_burst_t = None
    burst_count = None
    fdiv        = None

    # Always try to read the supporting registers (they are cheap)
    try:
        mux_burst_t = _read_u8(ser, 0x53)      # MuxBurstT
    except Exception:
        pass

    try:
        # BatchC is u16 according to the menu file
        burst_count = _read_u16(ser, 0x74)
    except Exception:
        # fallback in case firmware returns 4 bytes
        try:
            burst_count = _read_u32(ser, 0x74) & 0xFFFF
        except Exception:
            burst_count = None

    try:
        fdiv = _read_u16(ser, 0x69)
    except Exception:
        fdiv = None

    # ------------------------------------------------------------------
    # 2. Decode the mode
    # ------------------------------------------------------------------
    # MuxConfSw lookup (from register map)
    conf_names = {
        0: "0 (fixed)",
        1: "1 (fixed / Normal)",
        2: "Burst",
        3: "nBurst",
        4: "F div",
        5: "GATE",
        6: "nGATE",
        7: "GATE and SYNCIN1",
    }

    mode = conf_names.get(mux_conf_sw, f"Unknown (0x{mux_conf_sw:02X})")
    description = ""

    if mux_conf_sw == 1:
        mode = "CONFIG_NORMAL_SEQUENCE"
        description = "Normal continuous operation (MuxConfSw = 1)"

    elif mux_conf_sw == 5:
        mode = "CONFIG_GATE_GATE_SEQUENCE"
        description = "Gated by GATE input (MuxConfSw = GATE)"

    elif mux_conf_sw == 6:
        mode = "CONFIG_N_GATE_SEQUENCE"
        description = "Gated by inverted GATE (MuxConfSw = nGATE)"

    elif mux_conf_sw == 4:
        mode = "CONFIG_FREQ_DIV_xxx"
        description = f"Frequency divider mode (Fdiv = {fdiv})"

    elif mux_conf_sw == 2:                       # Burst mode
        burst_src = {
            0: "SYNCIN",
            1: "GATE",
            2: "nGATE",
            3: "SOFTWARE / One-shot",
        }.get(mux_burst_t, f"Unknown source ({mux_burst_t})")

        if mux_burst_t == 0:
            mode = "CONFIG_BURST_SYNCIN"
        elif mux_burst_t == 1:
            mode = "CONFIG_BURST_GATE"
        elif mux_burst_t == 2:
            mode = "CONFIG_BURST_NGATE"
        elif mux_burst_t == 3:
            mode = "CONFIG_BURST_SOFTWARE"
        else:
            mode = f"CONFIG_BURST_UNKNOWN (src={mux_burst_t})"

        description = (f"Burst mode – trigger source = {burst_src}, "
                       f"count = {burst_count}, Fdiv = {fdiv}")

    else:
        description = f"Raw MuxConfSw = {mux_conf_sw}"

    # ------------------------------------------------------------------
    # 3. Build result
    # ------------------------------------------------------------------
    result = {
        "mode":          mode,
        "mux_conf_sw":   mux_conf_sw,
        "mux_burst_t":   mux_burst_t,
        "burst_count":   burst_count,
        "fdiv":          fdiv,
        "description":   description,
    }

    # Nice printout
    print("\n=== Current Burst / Config Mode ===")
    print(f"Mode            : {result['mode']}")
    print(f"MuxConfSw (0x52): {result['mux_conf_sw']}  "
          f"({conf_names.get(mux_conf_sw, '?')})")
    if result['mux_burst_t'] is not None:
        print(f"MuxBurstT (0x53): {result['mux_burst_t']}")
    if result['burst_count'] is not None:
        print(f"Burst count     : {result['burst_count']}")
    if result['fdiv'] is not None:
        print(f"Fdiv (0x69)     : {result['fdiv']}")
    print(f"Description     : {result['description']}")
    print("=" * 40)

    return result

