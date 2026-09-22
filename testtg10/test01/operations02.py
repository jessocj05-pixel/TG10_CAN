
"""
operations.py – Register-sequence builders for EKSMA SY4000 / TG10.

Architecture
------------
    menu.py  →  operations.py  →  calculation.py + registers.py  →  v3.py (CAN)

Two levels of API
-----------------
    seq_*   – low-level: accept already-calculated register values
              (ndiv, osc_clock, ratediv, delay_counter, …)
              Sequences use explicit hex addresses + comments for easy debug.

    build_* – high-level: accept physical quantities
              (period_s, fext_hz, time_s, …)
              call calculation helpers, then call the matching seq_*.

No input() lives here.  All user interaction belongs in menu.py (or a GUI).
"""

from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any

from calculations02_ import (
    clock_internal_100mhz, clock_external,
    rate_divider_from_period_100m, rate_divider_from_period_ext,
    calc_delay, post_delay_calc,
    burst_count_clamp, fdiv_clamp,
)

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
SeqItem  = Tuple[int, Optional[bytes]]
Sequence = List[SeqItem]


# ===========================================================================
# Strict payload helpers – reject out-of-range values instead of wrapping
# ===========================================================================

def _u8(v: int) -> bytes:
    v = int(v)
    if not (0 <= v <= 0xFF):
        raise ValueError(f"u8 out of range: {v}")
    return bytes([v])

def _u16(v: int) -> bytes:
    v = int(v)
    if not (0 <= v <= 0xFFFF):
        raise ValueError(f"u16 out of range: {v}")
    return v.to_bytes(2, "little")

def _u32(v: int) -> bytes:
    v = int(v)
    if not (0 <= v <= 0xFFFFFFFF):
        raise ValueError(f"u32 out of range: {v}")
    return v.to_bytes(4, "little")


# ===========================================================================
# 1. Clock + Trigger  –  seq_*  (pre-calculated values)
#    Explicit hex addresses + comments for easy debugging
# ===========================================================================

def seq_internal_100mhz(
    osc_clock: int = 100,
    ndiv: int = 30,
    vco: int = 1,                 # 1 = 3 GHz, 0 = 2.5 GHz
    ratediv: int = 1000,
    *,
    command_on: bool = True,
) -> Sequence:
    """
    Internal 100 MHz oscillator path.
    All numeric arguments are already-calculated register values.
    """
    seq: Sequence = [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x75, _u8(0x00)),                          # OscClkMux = Internal 100MHz
        (0x11, _u8(osc_clock)),                     # OscClock = <user>
        (0x12, _u32(ndiv)),                         # Ndiv = <user>
        (0x6D, _u8(vco)),                           # VCO2 freq (0=2.5GHz, 1=3GHz)
        (0x55, _u8(0x00)),                          # MuxRateClk = internal
        (0x54, _u8(0x00)),                          # MuxStartTrg = Rate divider
        (0x20, _u32(ratediv)),                      # Ratediv = <user>
    ]
    if command_on:
        seq.append((0x10, _u8(0x01)))               # Command = ON
    return seq


def seq_external_clkin(
    osc_clock: int,
    ndiv: int,
    vco: int,
    ratediv: int,
    *,
    command_on: bool = False,
    include_readback: bool = True,
) -> Sequence:
    """
    External CLKIN (single-in) path.
    osc_clock / ndiv / vco / ratediv must already be calculated.
    """
    seq: Sequence = [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x75, _u8(0x01)),                          # OscClkMux = External
        (0x11, _u8(osc_clock)),                     # OscClock = <user>
        (0x12, _u32(ndiv)),                         # Ndiv = <user>
        (0x6D, _u8(vco)),                           # VCO2 freq (0=2.5GHz, 1=3GHz)
        (0x55, _u8(0x01)),                          # MuxRateClk = OPTCLK
        (0x54, _u8(0x01)),                          # MuxStartTrg = Rate div@OPTCLK
        (0x20, _u32(ratediv)),                      # Ratediv = <user>
    ]
    if include_readback:
        seq.append((0x76, None))                    # OscInF  = <READ>
        seq.append((0x77, None))                    # SYNCINF = <READ>
    if command_on:
        seq.append((0x10, _u8(0x01)))               # Command = ON
    return seq


def seq_external_syncin(
    osc_clock: int = 100,
    ndiv: int = 30,
    vco: int = 1,
    ratediv: int = 2,
    *,
    command_on: bool = True,
) -> Sequence:
    """
    External SYNCIN path.
    Output frequency ≈ SYNCIN_freq / ratediv.
    """
    seq: Sequence = [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x75, _u8(0x00)),                          # OscClkMux = Internal 100MHz
        (0x11, _u8(osc_clock)),                     # OscClock = <user>
        (0x12, _u32(ndiv)),                         # Ndiv = <user>
        (0x6D, _u8(vco)),                           # VCO2 freq (0=2.5GHz, 1=3GHz)
        (0x20, _u32(ratediv)),                      # Ratediv = <user>
        (0x55, _u8(0x03)),                          # MuxRateClk = SYNCIN
        (0x54, _u8(0x00)),                          # MuxStartTrg = Rate divider
    ]
    if command_on:
        seq.append((0x10, _u8(0x01)))               # Command = ON
    return seq


def seq_external_dual_in(
    osc_clock: int,
    ndiv: int,
    vco: int,
    ratediv: int,
    *,
    command_on: bool = False,
) -> Sequence:
    """
    Dual-in: CLKIN + SYNCIN.
    """
    seq: Sequence = [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x75, _u8(0x01)),                          # OscClkMux = External
        (0x11, _u8(osc_clock)),                     # OscClock = <user>
        (0x12, _u32(ndiv)),                         # Ndiv = <user>
        (0x6D, _u8(vco)),                           # VCO2 freq (0=2.5GHz, 1=3GHz)
        (0x55, _u8(0x03)),                          # MuxRateClk = SYNCIN
        (0x54, _u8(0x01)),                          # MuxStartTrg = Rate div@OPTCLK
        (0x20, _u32(ratediv)),                      # Ratediv = <user>
    ]
    if command_on:
        seq.append((0x10, _u8(0x01)))               # Command = ON
    return seq


def seq_oneshot_software(
    osc_clock: int = 100,
    ndiv: int = 30,
    vco: int = 1,
    ratediv: int = 10,
    *,
    command_on: bool = False,
) -> Sequence:
    """
    One-shot software trigger (OSTrig pulse).
    NOTE: original v3 used OscClkMux=External; kept for behavioural match.
    Verify against hardware before relying on it.
    """
    seq: Sequence = [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x75, _u8(0x01)),                          # OscClkMux = External
        (0x11, _u8(osc_clock)),                     # OscClock = <user>
        (0x12, _u32(ndiv)),                         # Ndiv = <user>
        (0x6D, _u8(vco)),                           # VCO2 freq (0=2.5GHz, 1=3GHz)
        (0x55, _u8(0x00)),                          # MuxRateClk = Internal
        (0x54, _u8(0x04)),                          # MuxStartTrg = One shot trig
        (0x20, _u32(ratediv)),                      # Ratediv = <user>
        (0x70, _u8(0x01)),                          # OSTrig = START
        (0x70, _u8(0x00)),                          # OSTrig = clear
    ]
    if command_on:
        seq.append((0x10, _u8(0x01)))               # Command = ON
    return seq


def seq_oneshot_smart(
    ndiv: int = 30,
    vco: int = 1,
    ratediv: int = 200,
    *,
    command_on: bool = False,
) -> Sequence:
    """
    One-shot smart trigger.
    WARNING: original v3 sequence contained a partial channel-0 preset.
    Those writes are retained as fixed literals for compatibility.
    """
    seq: Sequence = [
        (0x10, _u8(0x00)),                          # Command = OFF
        # --- legacy partial channel-0 preset (from v3) ---
        (0x80, _u32(3)),                            # DelayCnt0 = 3
        (0x5D, _u8(0x04)),                          # Ddly0 = 4
        (0x56, _u8(0x00)),                          # Adly0 = 0
        (0x26, _u16(0x20)),                         # PostCnt0 = 32
        (0x2E, _u8(0x03)),                          # MuxSetConf10 = Fine del0
        (0x56, _u8(0x00)),                          # Adly0 = 0 (repeat)
        (0x26, _u16(0x20)),                         # PostCnt0 = 32 (repeat)
        (0x2E, _u8(0x03)),                          # MuxSetConf10 = Fine del0 (repeat)
        # --- clock / trigger ---
        (0x12, _u32(ndiv)),                         # Ndiv = <user>
        (0x6D, _u8(vco)),                           # VCO2 freq (0=2.5GHz, 1=3GHz)
        (0x55, _u8(0x00)),                          # MuxRateClk = Internal
        (0x54, _u8(0x05)),                          # MuxStartTrg = One shot smart
        (0x20, _u32(ratediv)),                      # Ratediv = <user>
    ]
    if command_on:
        seq.append((0x10, _u8(0x01)))               # Command = ON
    return seq


# ===========================================================================
# 1b. Clock + Trigger  –  build_*  (physical quantities)
# ===========================================================================

def build_internal_100mhz_from_period(
    period_s: float,
    *,
    command_on: bool = True,
) -> Sequence:
    """
    High-level: user supplies desired period → everything else calculated.
    """
    cfg = clock_internal_100mhz()
    ratediv = rate_divider_from_period_100m(period_s * 1e9)
    return seq_internal_100mhz(
        osc_clock=cfg.oscillator_clock_reg,
        ndiv=cfg.n_divider,
        vco=cfg.vco2_reg,
        ratediv=ratediv,
        command_on=command_on,
    )


def build_external_clkin_from_period(
    period_s: float,
    fext_hz: float,
    *,
    force_vco: Optional[int] = None,
    command_on: bool = False,
    include_readback: bool = True,
) -> Sequence:
    """
    High-level: period + external clock frequency → full sequence.
    """
    cfg = clock_external(fext_hz, force_vco=force_vco)
    ratediv = rate_divider_from_period_ext(period_s, fext_hz)
    return seq_external_clkin(
        osc_clock=cfg.oscillator_clock_reg,
        ndiv=cfg.n_divider,
        vco=cfg.vco2_reg,
        ratediv=ratediv,
        command_on=command_on,
        include_readback=include_readback,
    )


def build_external_syncin(
    ratediv: int,
    *,
    osc_clock: int = 100,
    ndiv: int = 30,
    vco: int = 1,
    command_on: bool = True,
) -> Sequence:
    return seq_external_syncin(
        osc_clock=osc_clock,
        ndiv=ndiv,
        vco=vco,
        ratediv=ratediv,
        command_on=command_on,
    )

from calculations02_ import calc_rate_divider

def build_external_dual_in_from_period(
    period_s: float,
    fext_hz: float,
    syncin_hz: float,
    *,
    force_vco: Optional[int] = None,
    command_on: bool = False,
) -> Sequence:
    cfg = clock_external(fext_hz, force_vco=force_vco)
    if syncin_hz <= 0:
        raise ValueError("syncin_hz must be > 0")
    ratediv = calc_rate_divider(
        period_s,
        1.0 / syncin_hz,
    )
    return seq_external_dual_in(
        osc_clock=cfg.oscillator_clock_reg,
        ndiv=cfg.n_divider,
        vco=cfg.vco2_reg,
        ratediv=ratediv,
        command_on=command_on,
    )


# ===========================================================================
# 2. Simple ratediv write
# ===========================================================================

def seq_set_ratediv(ratediv: int) -> Sequence:
    return [
        (0x20, _u32(ratediv)),                      # Ratediv = <user>
    ]


# ===========================================================================
# 3. Delay / Post-delay / SR-mux
# ===========================================================================

# Hardware map (from registers.DELAY_REGS)
# CH : cnt_reg  d_reg  a_reg
_DELAY_MAP = {
    0: {"cnt": 0x80, "d": 0x5D, "a": 0x56},
    1: {"cnt": 0x16, "d": 0x5E, "a": 0x57},
    2: {"cnt": 0x19, "d": 0x5F, "a": 0x58},
    3: {"cnt": 0x1A, "d": 0x60, "a": 0x59},
    4: {"cnt": 0x1B, "d": None, "a": 0x5A},   # no D-delay
    5: {"cnt": 0x1C, "d": 0x62, "a": 0x5B},
    6: {"cnt": 0x1D, "d": 0x63, "a": 0x5C},
    7: {"cnt": 0x1E, "d": None, "a": None},   # counter only
}

_POST_MAP = {
    0: 0x26, 1: 0x27, 2: 0x28, 3: 0x29,
    4: 0x2A, 5: 0x2B, 6: 0x2C, 7: 0x2D,
}

# SR block: set1, set2, res1, res2
_SR_MAP = {
    0: {"set1": 0x2E, "set2": 0x2F, "res1": 0x30, "res2": 0x31},
    1: {"set1": 0x32, "set2": 0x33, "res1": 0x34, "res2": 0x35},
    2: {"set1": 0x36, "set2": 0x37, "res1": 0x38, "res2": 0x39},
    3: {"set1": 0x3A, "set2": 0x3B, "res1": 0x3C, "res2": 0x3D},
    4: {"set1": 0x3E, "set2": 0x3F, "res1": 0x40, "res2": 0x41},
    5: {"set1": 0x42, "set2": 0x43, "res1": 0x44, "res2": 0x45},
    6: {"set1": 0x46, "set2": 0x47, "res1": 0x48, "res2": 0x49},
    7: {"set1": 0x4A, "set2": 0x4B, "res1": 0x4C, "res2": 0x4D},
}

_LOGIC_MUX = {
    2: 0x7A,   # MuxOut2
    3: 0x7B,   # MuxOut3
    4: 0x7C,   # MuxOut4
    5: 0x7D,   # MuxOut5
}


def seq_delay_channel(
    channel: int,
    *,
    delay_counter: int,
    d_delay: Optional[int] = None,
    a_delay: Optional[int] = None,
) -> Sequence:
    """
    Write the register(s) for one delay channel.

    Hardware constraints:
        CH0-3,5,6 : Counter + D-delay + A-delay
        CH4       : Counter + A-delay only
        CH7       : Counter only
    """
    if channel not in _DELAY_MAP:
        raise ValueError(f"unknown delay channel {channel}")

    info = _DELAY_MAP[channel]
    seq: Sequence = [
        (info["cnt"], _u32(delay_counter)),         # DelayCntN
    ]

    if d_delay is not None:
        if info["d"] is None:
            raise ValueError(f"channel {channel} has no D-delay (CH4/CH7)")
        seq.append((info["d"], _u8(d_delay)))       # DdlyN

    if a_delay is not None:
        if info["a"] is None:
            raise ValueError(f"channel {channel} has no A-delay (CH7)")
        seq.append((info["a"], _u8(a_delay)))       # AdlyN

    return seq


def seq_post_delay_channel(channel: int, post_count: int) -> Sequence:
    if channel not in _POST_MAP:
        raise ValueError(f"unknown post-delay channel {channel}")
    return [
        (_POST_MAP[channel], _u16(post_count)),     # PostCntN
    ]


def seq_sr_block(
    block: int,
    *,
    set1: int = 0,
    set2: int = 0,
    res1: int = 0,
    res2: int = 0,
) -> Sequence:
    if block not in _SR_MAP:
        raise ValueError(f"unknown SR block {block}")
    r = _SR_MAP[block]
    return [
        (r["set1"], _u8(set1)),                     # MuxSetConf1N
        (r["set2"], _u8(set2)),                     # MuxSetConf2N
        (r["res1"], _u8(res1)),                     # MuxResConf1N
        (r["res2"], _u8(res2)),                     # MuxResConf2N
    ]


def seq_channels(
    channels: Dict[int, Dict[str, Any]],
    *,
    sr_blocks: Optional[Dict[int, Dict[str, int]]] = None,
) -> Sequence:
    """
    Preferred multi-channel interface.

    channels = {
        0: {"counter": 100, "d_delay": 7, "a_delay": 5, "post": 32},
        4: {"counter":  50, "a_delay": 0},
        7: {"counter":   3},
    }
    """
    seq: Sequence = []
    for ch, cfg in channels.items():
        seq.extend(seq_delay_channel(
            ch,
            delay_counter=cfg["counter"],
            d_delay=cfg.get("d_delay"),
            a_delay=cfg.get("a_delay"),
        ))
        if "post" in cfg:
            seq.extend(seq_post_delay_channel(ch, cfg["post"]))

    if sr_blocks:
        for blk, vals in sr_blocks.items():
            seq.extend(seq_sr_block(blk, **vals))
    return seq




def seq_delay_preset(channels: Dict[int, Dict[str, int]]) -> Sequence:
    return seq_channels(channels)


def seq_postdelay_preset(post_counts: Dict[int, int]) -> Sequence:
    seq: Sequence = []
    for ch, pc in post_counts.items():
        seq.extend(seq_post_delay_channel(ch, pc))
    return seq


def build_delay_channel(
    channel: int,
    time_s: float,
    f_hz: float,
) -> Sequence:
    result = calc_delay(time_s, f_hz, channel)
    return seq_delay_channel(
        channel,
        delay_counter=result["delay_counter"],
        d_delay=result.get("d_delay"),
        a_delay=result.get("a_delay"),
    )


def build_post_delay_channel(
    channel: int,
    pulse_width_s: float,
    f_hz: float,
) -> Sequence:
    pc = post_delay_calc(f_hz, pulse_width_s)
    return seq_post_delay_channel(channel, pc)


# ===========================================================================
# 4. Configuration modes (MuxConfSw / Burst / Fdiv)
# ===========================================================================

def seq_config_normal() -> Sequence:
    return [
        (0x52, _u8(0x01)),                          # MuxConfSw = 1 (normal)
    ]

def seq_config_gate() -> Sequence:
    return [
        (0x52, _u8(0x05)),                          # MuxConfSw = GATE
    ]

def seq_config_ngate() -> Sequence:
    return [
        (0x52, _u8(0x06)),                          # MuxConfSw = nGATE
    ]

def seq_config_burst(
    burst_trig_src: int,          # 0=SYNCIN, 1=GATE, 2=nGATE, 3=software
    burst_count: int = 100,
    f_div: int = 1,
) -> Sequence:
    return [
        (0x52, _u8(0x02)),                          # MuxConfSw = Burst
        (0x53, _u8(burst_trig_src)),                # MuxBurstT = <src>
        (0x74, _u32(burst_count_clamp(burst_count))),  # BatchC / BurstCount
        (0x69, _u16(fdiv_clamp(f_div))),            # Fdiv
    ]

def seq_config_burst_syncin(burst_count: int = 1, f_div: int = 1) -> Sequence:
    return seq_config_burst(0, burst_count, f_div)

def seq_config_burst_gate(burst_count: int = 100, f_div: int = 1) -> Sequence:
    return seq_config_burst(1, burst_count, f_div)

def seq_config_burst_ngate(burst_count: int = 100, f_div: int = 1) -> Sequence:
    return seq_config_burst(2, burst_count, f_div)

def seq_config_burst_software(burst_count: int = 100, f_div: int = 1) -> Sequence:
    return seq_config_burst(3, burst_count, f_div)

def seq_config_freq_div(f_div: int = 1) -> Sequence:
    return [
        (0x52, _u8(0x04)),                          # MuxConfSw = F div
        (0x69, _u16(fdiv_clamp(f_div))),            # Fdiv
    ]


# ===========================================================================
# 5. Output channel configuration (OUT0–OUT7)
# ===========================================================================

def seq_out_config_del(
    out_channel: int,
    *,
    set1_src: int = 0 ,         # 
    res1_src: int = 0,          # ""
    set2_src: int = 0,          # ""
    res2_src: int = 0,          # ""
        
    logic_mux: Optional[int] = None,
    command_on: bool = False,
) -> Sequence:
    if out_channel not in _SR_MAP:
        raise ValueError(f"out_channel must be 0-7, got {out_channel}")

    r = _SR_MAP[out_channel]
    seq: Sequence = [
        (0x10, _u8(0x00)),                          # Command = OFF
        (r["set1"], _u8(set1_src)),                     # Config1 rise = NC
        (r["res1"], _u8(res1_src)),                     # Config1 fall = NC
        (r["set2"], _u8(set2_src)),                  # Config2 rise
        (r["res2"], _u8(res2_src)),                  # Config2 fall
    ]
    if logic_mux is not None and out_channel in _LOGIC_MUX:
        seq.append((_LOGIC_MUX[out_channel], _u8(logic_mux)))
    if command_on:
        seq.append((0x10, _u8(0x01)))               # Command = ON
    return seq


def seq_out0_config2_del0_del1(command_on: bool = True) -> Sequence:
    seq: Sequence = [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x2E, _u8(0x00)),                          # MuxSetConf10 = NC
        (0x30, _u8(0x00)),                          # MuxResConf10 = NC
        (0x2F, _u8(0x03)),                          # MuxSetConf20 = Fine del0
        (0x31, _u8(0x04)),                          # MuxResConf20 = Fine del1
    ]
    if command_on:
        seq.append((0x10, _u8(0x01)))               # Command = ON
    return seq


def seq_out1_config2_del0_del1() -> Sequence:
    return [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x32, _u8(0x00)),                          # MuxSetConf11 = NC
        (0x34, _u8(0x00)),                          # MuxResConf11 = NC
        (0x33, _u8(0x03)),                          # MuxSetConf21 = Fine del0
        (0x35, _u8(0x04)),                          # MuxResConf21 = Fine del1
    ]


def seq_out2_config2_del0_del1(command_on: bool = True) -> Sequence:
    seq: Sequence = [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x36, _u8(0x00)),                          # MuxSetConf12 = NC
        (0x38, _u8(0x00)),                          # MuxResConf12 = NC
        (0x37, _u8(0x03)),                          # MuxSetConf22 = Fine del0
        (0x39, _u8(0x04)),                          # MuxResConf22 = Fine del1
        (0x7A, _u8(0x00)),                          # MuxOut2 = lOUT2
    ]
    if command_on:
        seq.append((0x10, _u8(0x01)))               # Command = ON
    return seq


def seq_out3_config2_del0_del1() -> Sequence:
    return [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x3A, _u8(0x00)),                          # MuxSetConf13 = NC
        (0x3C, _u8(0x00)),                          # MuxResConf13 = NC
        (0x3B, _u8(0x03)),                          # MuxSetConf23 = Fine del0
        (0x3D, _u8(0x04)),                          # MuxResConf23 = Fine del1
        (0x7B, _u8(0x01)),                          # MuxOut3 = lOUT3 and OUT2
    ]


def seq_out4_config2_del0_del1() -> Sequence:
    return [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x3E, _u8(0x00)),                          # MuxSetConf14 = NC
        (0x40, _u8(0x00)),                          # MuxResConf14 = NC
        (0x3F, _u8(0x03)),                          # MuxSetConf24 = Fine del0
        (0x41, _u8(0x04)),                          # MuxResConf24 = Fine del1
        (0x7C, _u8(0x02)),                          # MuxOut4 = lOUT4 or OUT3
    ]


def seq_out5_config2_del0_del1() -> Sequence:
    return [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x42, _u8(0x00)),                          # MuxSetConf15 = NC
        (0x44, _u8(0x00)),                          # MuxResConf15 = NC
        (0x43, _u8(0x03)),                          # MuxSetConf25 = Fine del0
        (0x45, _u8(0x04)),                          # MuxResConf25 = Fine del1
        (0x7D, _u8(0x03)),                          # MuxOut5 = not OUT4
    ]


def seq_out6_config2_del0_del1() -> Sequence:
    return [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x46, _u8(0x00)),                          # MuxSetConf16 = NC
        (0x48, _u8(0x00)),                          # MuxResConf16 = NC
        (0x47, _u8(0x03)),                          # MuxSetConf26 = Fine del0
        (0x49, _u8(0x04)),                          # MuxResConf26 = Fine del1
    ]


def seq_out7_config2_del0_del1() -> Sequence:
    return [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x4A, _u8(0x00)),                          # MuxSetConf17 = NC
        (0x4C, _u8(0x00)),                          # MuxResConf17 = NC
        (0x4B, _u8(0x03)),                          # MuxSetConf27 = Fine del0
        (0x4D, _u8(0x04)),                          # MuxResConf27 = Fine del1
    ]


def seq_out_anout_out7(
    dac1: int = 3,
    dac2: int = 4095,
    mux_dac_src: int = 0x07,      # OUT7
) -> Sequence:
    return [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x6B, _u16(dac1)),                         # DAC1
        (0x6C, _u16(dac2)),                         # DAC2
        (0x50, _u8(mux_dac_src)),                   # MuxDAC source
    ]


def seq_out_pret(src: int = 0x00) -> Sequence:
    return [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x4F, _u8(src)),                           # MuxPreT source
    ]


def seq_out_comt(src: int = 0x08) -> Sequence:
    return [
        (0x10, _u8(0x00)),                          # Command = OFF
        (0x4E, _u8(src)),                           # MuxTrg1Out source
    ]


# ===========================================================================
# 6. Run control
# ===========================================================================

def seq_run_on() -> Sequence:
    return [
        (0x10, _u8(0x01)),                          # Command = ON
    ]

def seq_run_off() -> Sequence:
    return [
        (0x10, _u8(0x00)),                          # Command = OFF
    ]


# ===========================================================================
# Coverage checklist vs original v3.py sequences
# ===========================================================================
#
# v3.py sequence                              → operations.py function
# -------------------------------------------------------------------------
# INTERNAL_100MHz_SEQUENCE                    → seq_internal_100mhz /
#                                               build_internal_100mhz_from_period
# EXTERNALSINGLEIN_CLKIN_100MHz_SEQUENCE      → seq_external_clkin /
#                                               build_external_clkin_from_period
# EXTERNALSINGLEIN_SYNCIN_SEQUENCE            → seq_external_syncin
# EXTERNALDUALIN_…_SEQUENCE                   → seq_external_dual_in
# ONESHOT_TRIGGER_SOFTWARETRIG                → seq_oneshot_software
# ONESHOT_TRIGGER_SMARTTRIG                   → seq_oneshot_smart   (legacy)
# FREQ_10KHZ                                  → seq_set_ratediv
# PRESET1_CHANNEL_SEQUENCE                    → inside saved presets
# CONFIG_NORMAL / GATE / N_GATE / BURST_*     → seq_config_*
# CONFIG_FREQ_DIV                             → seq_config_freq_div
# DELAY_PRESET_DEL / POSTDELAY_PRESET         → seq_delay_preset / seq_postdelay_preset
# OUT0…OUT7_CONFIG2_DEL0_DEL1                 → seq_out*_config2_del0_del1
# OUT_ANOUT / OUT_PRET / OUT_COMT             → seq_out_anout / pret / comt
# RUN_ON / RUN_OFF                            → seq_run_on / seq_run_off
#
# ===========================================================================


if __name__ == "__main__":
    def _print_seq(name, seq):
        print(f"\n=== {name} ===")
        for reg, data in seq:
            if data is None:
                print(f"  (0x{reg:02X}, None)                       # READ")
            else:
                print(f"  (0x{reg:02X}, {data.hex()})")

    _print_seq("internal 100 MHz", seq_internal_100mhz())
    _print_seq("external CLKIN", seq_external_clkin(100, 30, 1, 1))
    _print_seq("OUT0 config2", seq_out0_config2_del0_del1())
