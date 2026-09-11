"""test.py — full test suite. Run: python test.py
Covers: parsing, clock resolve, trigger-mode formula (the OPTCLK bug fix),
delay per-channel quirks (ch4/6/7), thresholds, DAC, burst, watchdog,
addr-collision detection, and the arm_device() lock-gate using mocked
read/send functions (no real hardware needed to verify the logic).
"""

from calculations import (
    parse_time, parse_freq,
    calc_pll2_n, resolve_vco_mode, system_clock_hz,
    calc_trigger_config,
    check_clock_lock, check_pll1_lock,
    calc_delay, validate_delay, min_delay_time_s, max_delay_time_s,
    calc_post_delay_checked, calc_post_delay_clamped, min_post_delay_s, max_post_delay_s,
    calc_rate_divider, calc_burst_count, calc_f_div, calc_f_div_acq,
    calc_burst_mode, calc_watchdog_period,
    calc_dac_value, calc_dac_config,
    check_range, RANGES,
)
from user import check_no_addr_collisions, arm_device, REG_CLKVALID, REG_PLL1LOCKED, REG_COMMAND, REG_ERRORCODE

PASS = 0
FAIL = 0

def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"[OK ] {label}")
    else:
        FAIL += 1
        print(f"[FAIL] {label}")

def expect_raises(label, fn, *a, **kw):
    try:
        fn(*a, **kw)
        check(label, False)
    except (ValueError, RuntimeError):
        check(label, True)


import math

def approx(a, b, rel=1e-9):
    return math.isclose(a, b, rel_tol=rel)

# ========== PARSING ==========
# NOTE: exact float equality (==) is unreliable here — "250ns" parsed via
# float('250')*1e-9 can differ from the literal 250e-9 by 1 ULP due to
# binary float representation. Use isclose for float comparisons throughout.
check("parse_time 250ns", approx(parse_time("250ns"), 250e-9))
check("parse_time 1us", approx(parse_time("1us"), 1e-6))
expect_raises("parse_time bad string raises", parse_time, "abc")
check("parse_freq 20MHz", parse_freq("20MHz") == 20e6)
expect_raises("parse_freq bad string raises", parse_freq, "xyz")


# ========== CLOCK ==========
n, sysclk = calc_pll2_n(100)
check(f"pll2_n(100MHz) n=30", n == 30 and sysclk == 3000)
res = resolve_vco_mode(100)
check(f"resolve_vco_mode(100MHz) -> 3GHz", res["vco2"] == "3GHz")
expect_raises("ext_clock below 20MHz rejected", resolve_vco_mode, 10)
expect_raises("ext_clock above 100MHz rejected", resolve_vco_mode, 150)


# ========== TRIGGER MODE (the OPTCLK-vs-10ns bug fix) ==========
# your exact reported case: 80MHz ext clock, 1us desired period
cfg = calc_trigger_config("internal_extclk", period_s=1e-6, ext_clk_hz=80e6)
check(f"internal_extclk 80MHz/1us -> ratediv={cfg['ratediv']} (expect 80)", cfg["ratediv"] == 80)
check("internal_extclk mux_rateclk=0x01 (OPTCLK)", cfg["mux_rateclk"] == 0x01)

# internal_100mhz mode must use fixed 10ns regardless of any ext clock
cfg2 = calc_trigger_config("internal_100mhz", period_s=1e-6)
check(f"internal_100mhz 1us -> ratediv={cfg2['ratediv']} (expect 100)", cfg2["ratediv"] == 100)
check("internal_100mhz mux_rateclk=0x00 (Internal)", cfg2["mux_rateclk"] == 0x00)

# external_syncin has no rate divider at all
cfg3 = calc_trigger_config("external_syncin")
check("external_syncin ratediv is None", cfg3["ratediv"] is None)
check("external_syncin mux_trigger=0x03", cfg3["mux_trigger"] == 0x03)

expect_raises("internal_extclk missing ext_clk_hz raises", calc_trigger_config, "internal_extclk", period_s=1e-6)
expect_raises("unknown trigger mode raises", calc_trigger_config, "bogus_mode")


# ========== DELAY: per-channel quirks ==========
F = 3_000_000_000

d0 = calc_delay(1e-6, F, 0)
validate_delay(d0, 0)
check(f"ch0 has d_delay+a_delay -> {d0}", "d_delay" in d0 and "a_delay" in d0)

# ch4: direct 10ns units, NOT F/28. 300ns -> counter=30 (this was the bug you hit)
d4 = calc_delay(300e-9, 100e6, 4)
check(f"ch4 300ns -> delay_counter={d4['delay_counter']} (expect 30)", d4["delay_counter"] == 30)
check("ch4 has a_delay, no d_delay", "a_delay" in d4 and "d_delay" not in d4)
validate_delay(d4, 4)

d6 = calc_delay(1e-6, F, 6)
check(f"ch6 shared_ad flag -> {d6}", d6.get("shared_ad") is True and "d_delay" in d6)

d7 = calc_delay(1e-6, F, 7)
check(f"ch7 no d_delay/a_delay (shares ch6) -> {d7}", "d_delay" not in d7 and "a_delay" not in d7)

expect_raises("delay below floor rejected", validate_delay, calc_delay(1e-9, F, 0), 0)
expect_raises("delay above ceiling rejected", validate_delay, calc_delay(1.0, F, 0), 0)


# ========== POST DELAY ==========
pd = calc_post_delay_checked(500e-9, F)
check(f"postdel 500ns -> {pd}", 3 <= pd <= 258)
expect_raises("postdel below floor rejected", calc_post_delay_checked, 1e-12, F)
expect_raises("postdel above ceiling rejected", calc_post_delay_checked, 1e-3, F)
pd_clamped = calc_post_delay_clamped(1e-3, F)
check(f"postdel clamped caps at 258 -> {pd_clamped}", pd_clamped == 258)


# ========== RATE DIVIDER / BURST / FDIV ==========
check("rate_divider basic", calc_rate_divider(1e-6, 10e-9) == 100)
check("burst_count valid", calc_burst_count(100) == 100)
expect_raises("burst_count above max rejected", calc_burst_count, 70000)
check("f_div valid (parked range)", calc_f_div(500) == 500)


# ========== WATCHDOG ==========
wd = calc_watchdog_period(freq_hz=1e6)
check(f"watchdog 1MHz -> {wd} ticks", wd == 100)
expect_raises("watchdog both args rejected", calc_watchdog_period, freq_hz=1e6, period_s=1e-6)


# ========== DAC ==========
check("dac 1V -> 4095", calc_dac_value(1.0) == 4095)
expect_raises("dac above vmax rejected", calc_dac_value, 1.5)
dac_cfg = calc_dac_config(0.3, 1.0)
check(f"dac_config -> {dac_cfg}", dac_cfg["dac2"] == 4095)


# ========== CLOCK-LOCK PRE-FLIGHT GATE ==========
check("check_clock_lock(0x03) passes", check_clock_lock(0x03) is True)
expect_raises("check_clock_lock(0x00) raises", check_clock_lock, 0x00)
expect_raises("check_clock_lock(0x02) raises (clock present, not locked)", check_clock_lock, 0x02)

check("check_pll1_lock(0x01) returns True", check_pll1_lock(0x01) is True)
check("check_pll1_lock(0x00, required=False) returns False, no raise", check_pll1_lock(0x00, required=False) is False)
expect_raises("check_pll1_lock(0x00, required=True) raises", check_pll1_lock, 0x00, True)


# ========== ADDRESS COLLISION DETECTION ==========
good_seq = [(0x10, b'\x00'), (0x11, b'\x14'), (0x12, b'\x7c\x00\x00\x00')]
check("no collisions in clean seq", check_no_addr_collisions(good_seq) is True)

bad_seq = [(0x19, b'\x00'), (0x19, b'\x01')]  # same non-exempt addr, different payload
check("collision detected in bad seq", check_no_addr_collisions(bad_seq) is False)

same_val_seq = [(0x10, b'\x00'), (0x10, b'\x00')]  # same addr, SAME payload - not flagged
check("same addr+same payload not flagged as collision", check_no_addr_collisions(same_val_seq) is True)


# ========== ARM_DEVICE with mocked read/send (no real hardware) ==========

class MockDevice:
    """Simulates device register reads for testing arm_device() logic."""
    def __init__(self, clkvalid=0x03, pll1=0x01, cmd_after_write=0x01, error=0x00):
        self.clkvalid = clkvalid
        self.pll1 = pll1
        self.cmd_after_write = cmd_after_write
        self.error = error
        self.sent = []

    def read_reg(self, addr):
        if addr == REG_CLKVALID:
            return self.clkvalid
        if addr == REG_PLL1LOCKED:
            return self.pll1
        if addr == REG_COMMAND:
            return self.cmd_after_write
        if addr == REG_ERRORCODE:
            return self.error
        raise KeyError(f"mock doesn't know addr 0x{addr:02X}")

    def send(self, seq):
        self.sent.extend(seq)


# scenario 1: clock locked, everything healthy -> should arm successfully
dev_ok = MockDevice(clkvalid=0x03, pll1=0x01, cmd_after_write=0x01, error=0x00)
result = arm_device(dev_ok.read_reg, dev_ok.send)
check("arm_device succeeds when clock locked", result is True)
check("arm_device actually sent Command=ON", len(dev_ok.sent) == 1 and dev_ok.sent[0][0] == REG_COMMAND)

# scenario 2: clock NOT locked -> must refuse, must NOT send Command=ON
dev_nolock = MockDevice(clkvalid=0x00, pll1=0x00, cmd_after_write=0x01, error=0x00)
try:
    arm_device(dev_nolock.read_reg, dev_nolock.send)
    check("arm_device refuses when clock not locked", False)
except RuntimeError as e:
    check(f"arm_device refuses when clock not locked: {e}", True)
check("arm_device did NOT send Command=ON when refused", len(dev_nolock.sent) == 0)

# scenario 3: clock locked but Command write didn't stick -> should raise after send
dev_stuck = MockDevice(clkvalid=0x03, pll1=0x01, cmd_after_write=0x00, error=0x00)  # readback wrong
expect_raises("arm_device raises if Command readback wrong", arm_device, dev_stuck.read_reg, dev_stuck.send)

# scenario 4: clock locked, command stuck, but error code nonzero -> should raise
dev_err = MockDevice(clkvalid=0x03, pll1=0x01, cmd_after_write=0x01, error=0x05)
expect_raises("arm_device raises if error code nonzero after arm", arm_device, dev_err.read_reg, dev_err.send)


# ========== SUMMARY ==========
print(f"\n{'='*40}")
print(f"PASS: {PASS}  FAIL: {FAIL}")
if FAIL:
    raise SystemExit(1)
print("All checks passed.")


# ============================================================================
# STANDALONE SEQ INSPECTOR — paste any hand-written seq (like from v3.py) and
# check it here before sending to real hardware. No pytest/assert needed for
# this part, just call inspect_seq(YOUR_SEQ) and read the printout.
# ============================================================================

import user as _user  # reuse REG_* constants + collision checker


def build_register_name_map():
    """addr -> human-readable name, built from user.py's known register constants."""
    names = {}
    scalar_regs = {
        _user.REG_COMMAND: "Command",
        _user.REG_OSCCLKMUX: "OscClkMux",
        _user.REG_OSCCLOCK: "OscClock",
        _user.REG_VCO: "VCO2freq",
        _user.REG_NDIV: "Ndiv",
        _user.REG_MUX_RATECLK: "MuxRateClk",
        _user.REG_MUX_STARTTRG: "MuxStartTrg",
        _user.REG_RATEDIV: "Ratediv",
        _user.REG_MUX_CONFSW: "MuxConfSw",
        _user.REG_FDIV: "Fdiv",
        _user.REG_BURSTCOUNT: "BurstCount",
        _user.REG_DAC1: "DAC1",
        _user.REG_DAC2: "DAC2",
        _user.REG_CLKVALID: "CLKvalid",
        _user.REG_PLL1LOCKED: "PLL1locked",
        _user.REG_ERRORCODE: "ErrorCode",
    }
    names.update(scalar_regs)
    for ch, regs in _user.DELAY_REGS.items():
        if regs["cnt"] is not None:
            names[regs["cnt"]] = f"DELCNT{ch}"
        if regs["d"] is not None:
            names[regs["d"]] = f"Ddelay{ch}"
        if regs["a"] is not None:
            names[regs["a"]] = f"Adelay{ch}"
    for ch, addr in _user.POSTDEL_REGS.items():
        names[addr] = f"PostCnt{ch}"
    return names


def inspect_seq(seq, label="seq"):
    """
    Print every entry decoded (addr, known name if any, raw hex, decoded int),
    run collision check, flag any addr not in the known register map.
    Works on any (addr:int, payload:bytes) list — hand-written or generated.
    """
    print(f"\n=== inspecting {label}, {len(seq)} entries ===")
    names = build_register_name_map()

    for addr, payload in seq:
        name = names.get(addr, "UNKNOWN")
        val = int.from_bytes(payload, "little") if len(payload) > 1 else payload[0]
        print(f"  0x{addr:02X} ({name:12s}) len={len(payload)}  raw={payload.hex():10s}  decoded={val}")

    ok = _user.check_no_addr_collisions(seq)
    if ok:
        print("  -> no address collisions")

    unknown = sorted(set(addr for addr, _ in seq if addr not in names))
    if unknown:
        print(f"  !! unknown addrs (not in register map, verify these): "
              f"{[f'0x{a:02X}' for a in unknown]}")

    return ok


def run_seq_on_device(seq, dry_run=True):
    """
    dry_run=True (default): inspects/validates only, no hardware contact.
    dry_run=False: imports v3.py and calls v3.run_sequence(v3.ser, seq) for
    real. Adjust the import/attribute names below to match your actual
    v3.py API if they differ (e.g. different serial handle name, different
    send function name).
    """
    ok = inspect_seq(seq, label="seq (pre-send check)")
    if not ok:
        print("!! refusing to send: address collisions detected, fix seq first")
        return False

    if dry_run:
        print("dry_run=True, not sending. Call run_seq_on_device(seq, dry_run=False) to transmit.")
        return True

    confirm = input("About to send to REAL hardware. Type 'YES' to confirm: ").strip()
    if confirm != "YES":
        print("aborted by user")
        return False

    import v3  # your main script — must expose `ser` (or similar) and `run_sequence`
    v3.run_sequence(v3.ser, seq)
    print("sequence sent.")
    return True


# ---------------- EXAMPLE: hand-written seq, computed values plugged in ----------------
# Same shape as your example — ndiv/ratediv computed via calculations.py instead
# of left undefined, so this block actually runs standalone.

_ndiv, _ = calc_pll2_n(100, target_mhz=3000)          # internal 100MHz -> ndiv=30
_ratediv = calc_rate_divider(1e-3, 10e-9)              # 1ms period -> 1kHz, internal 10ns basis

INTERNAL_100MHz_SEQUENCE = [
    (0x10, bytes([0x00])),                          # Command = OFF
    (0x75, bytes([0x00])),                          # OscClkMux = Internal 100MHz
    (0x11, bytes([0x64])),                          # OscClock = 100
    (0x12, _ndiv.to_bytes(4, "little")),             # Ndiv = 30
    (0x6D, bytes([0x01])),                          # VCO2 freq = 3GHz
    (0x55, bytes([0x00])),                          # MuxRateClk = internal
    (0x54, bytes([0x00])),                          # MuxStartTrg = Rate divider
    (0x20, _ratediv.to_bytes(4, "little")),          # Ratediv = 100000
    (0x10, bytes([0x01])),                          # Command = ON
]
EXTERNALSINGLEIN_CLKIN_100MHz_SEQUENCE = [
    (0x10, bytes([0x00])),                          # Command = OFF
    (0x75, bytes([0x01])),                          # OscClkMux = exterenal
    # (0x11, bytes([0x0A])),                          # OscClock = 100--->change clk
    (0x11, bytes([0x64])),                          # OscClock = 100--->change clk
    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30
    (0x6D, bytes([0x01])),                          # VCO2 freq = 3GHz
    (0x55, bytes([0x01])),                          # MuxRateClk = external
    (0x54, bytes([0x01])),                          # MuxStartTrg = Rate divider@optclk
    (0x20, (1).to_bytes(4, "little")),             # Ratediv = 1000 -->set freq
    (0x76, None),
    (0x77, None),
    #(0x10, bytes([0x01])),                          # Command = ON
]

# befor run give the sync of desired value then only it work 
# freq given 5Mhz               freq = 5000000/10 = 5,00,000(500Khz)
# freq given 5Mhz               freq = 10000000/10 = 10,00,000()
# freq given 5Mhz               freq = 20000000/10 = 20,00,000()
EXTERNALSINGLEIN_SYNCIN_SEQUENCE = [
    (0x10, bytes([0x00])),                          # Command = OFF
    (0x75, bytes([0x00])),                          # OscClkMux = Internal 100MHz
    (0x11, bytes([0x64])),                          # OscClock = 100
    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30
    (0x6D, bytes([0x01])),                           # VCO2 freq = 3GHz
    (0x20, (2).to_bytes(4, "little")),             #  output frequency depend on syncin freq freq = syncin / ratedivide
    (0x55, bytes([0x03])),                          # MuxRateClk = SYNCIN
    (0x54, bytes([0x00])),                          # MuxStartTrg = Rate divider
    # (0x20, (100).to_bytes(4, "little")),             # Ratediv = 100
    (0x10, bytes([0x01])),                          # Command = ON

]

EXTERNALDUALIN_CLKIN_100MHZ_SYNCIN_20MHZ_SEQUENCE = [
    (0x10, bytes([0x00])),                          # Command = OFF
    (0x75, bytes([0x01])),                          # OscClkMux = Internal 100MHz
    (0x11, bytes([0x64])),                          # OscClock = 100
    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30
    (0x6D, bytes([0x01])),                          # VCO2 freq = 3GHz
    (0x55, bytes([0x03])),                          # MuxRateClk = SYNCIN
    (0x54, bytes([0x01])),                          # MuxStartTrg = Rate divider
    (0x20, (200).to_bytes(4, "little")),             # Ratediv = 100
    #(0x10, bytes([0x01])),                          # Command = ON
]
ONESHOT_TRIGGER_SOFTWARETRIG = [
    (0x10, bytes([0x00])),                          # Command = OFF
    (0x75, bytes([0x01])),                          # OscClkMux = Internal 100MHz
    (0x11, bytes([0x64])),                          # OscClock = 100
    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30
    (0x6D, bytes([0x01])),                          # VCO2 freq = 3GHz
    (0x55, bytes([0x00])),                          # MuxRateClk = SYNCIN
    (0x54, bytes([0x04])),                          # MuxStartTrg = Rate divider
    (0x20, (10).to_bytes(4, "little")),             # Ratediv = 100
    (0X70, bytes([0X01])),
    (0X70, bytes([0X00])),
    #(0x10, bytes([0x01])),                          # Command = ON
]
ONESHOT_TRIGGER_SMARTTRIG= [

    (0x10, bytes([0x00])),                          # Command = OFF
    (0x80, bytes([0x03])),                          # OscClkMux = Internal 100MHz
    (0x5D, bytes([0x04])),                          # OscClock = 100
    (0x56, bytes([0x00])),
    (0x26, bytes([0x20])),
    (0x2E, bytes([0x03])),
    (0x56, bytes([0x00])),
    (0x26, bytes([0x20])),
    (0x2E, bytes([0x03])),

    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30
    (0x6D, bytes([0x01])),                          # VCO2 freq = 3GHz
    (0x55, bytes([0x00])),                          # MuxRateClk = SYNCIN
    (0x54, bytes([0x05])),                          # MuxStartTrg = Rate divider
    (0x20, (200).to_bytes(4, "little")),             # Ratediv = 100
    #(0x10, bytes([0x01])),                          # Command = ON
]

FREQ_10KHZ = [
    (0x20, (100).to_bytes(4, "little")),
]

PRESET1_CHANNEL_SEQUENCE = [
    (0x80, (3).to_bytes(4, "little")),              # DelayCnt0 = 3
    (0x16, (4).to_bytes(4, "little")),              # DelayCnt1 = 4
    (0x19, (35).to_bytes(4, "little")),             # DelayCnt2 = 35
    (0x1A, (67).to_bytes(4, "little")),             # DelayCnt3 = 67
    (0x1B, (93).to_bytes(4, "little")),             # DelayCnt4 = 93
    (0x1C, (3).to_bytes(4, "little")),              # DelayCnt5 = 3
    (0x1D, (3).to_bytes(4, "little")),              # DelayCnt6 = 3
    (0x1E, (3).to_bytes(4, "little")),              # DelayCnt7 = 3

    (0x26, (32).to_bytes(2, "little")),             # PostCnt0 = 32
    (0x27, (11).to_bytes(2, "little")),             # PostCnt1 = 11
    (0x28, (32).to_bytes(2, "little")),             # PostCnt2 = 32
    (0x29, (32).to_bytes(2, "little")),             # PostCnt3 = 32
    (0x2A, (30).to_bytes(2, "little")),             # PostCnt4 = 30
    (0x2B, (54).to_bytes(2, "little")),             # PostCnt5 = 54
    (0x2C, (64).to_bytes(2, "little")),             # PostCnt6 = 64
    (0x2D, (75).to_bytes(2, "little")),             # PostCnt7 = 75

    (0x2E, bytes([0x03])),                          # MuxSetConf10 = 3
    (0x2F, bytes([0x03])),                          # MuxSetConf20 = 3
    (0x30, bytes([0x02])),                          # MuxResConf10 = 2
    (0x31, bytes([0x02])),                          # MuxResConf20 = 2

    (0x56, bytes([0x00])),                          # Adly0 = 0
    (0x57, bytes([0x0d])),                          # Adly1 = 13
    (0x58, bytes([0x00])),                          # Adly2 = 0
    (0x59, bytes([0x00])),                          # Adly3 = 0
    (0x5A, bytes([0x00])),                          # Adly4 = 0
    (0x5B, bytes([0x01])),                          # Adly5 = 1
    (0x5C, bytes([0x01])),                          # Adly6 = 1

    (0x5D, bytes([0x04])),                          # Ddly0 = 4
    (0x5E, bytes([0x05])),                          # Ddly1 = 5
    (0x5F, bytes([0x08])),                          # Ddly2 = 8
    (0x60, bytes([0x0c])),                          # Ddly3 = 12
    (0x62, bytes([0x04])),                          # Ddly5 = 4
    (0x63, bytes([0x04])),                          # Ddly6 = 4

]

CONFIG_NORMAL_SEQUENCE = [
    (0x52, bytes([0x01])),                          # MuxConfSw = 1
]

CONFIG_GATE_GATE_SEQUENCE = [
    (0x52, bytes([0x05])),                          # MuxConfSw = GATE
]

CONFIG_N_GATE_SEQUENCE = [
    (0x52, bytes([0x06])),                          # MuxConfSw = GATE
    (0x53, bytes([0x06])),
]

CONFIG_BURST_SYNCIN = [
    (0x52, bytes([0x02])),
    (0x53, bytes([0x00])),
    (0x74, (1).to_bytes(4, "little")),
    (0x69, (1).to_bytes(4, "little")),
]
CONFIG_BURST_GATE = [
    (0x52, bytes([0x02])),
    (0x53, bytes([0x01])),
    (0x74, (100).to_bytes(4, "little")),
    (0x69, (1).to_bytes(4, "little")),
]
CONFIG_BURST_NGATE = [
    (0x52, bytes([0x02])),
    (0x53, bytes([0x02])),
    (0x74, (100).to_bytes(4, "little")),  #burst coount
    (0x69, (1).to_bytes(4, "little")),
]
CONFIG_BURST_SOFTWARE = [
    (0x52, bytes([0x02])),
    (0x53, bytes([0x03])), 
    (0x74, (100).to_bytes(4, "little")),
    (0x69, (1).to_bytes(4, "little")),  
]

CONFIG_FREQ_DIV_100_SEQUENCE = [
    (0x52, bytes([0x04])),                          # MuxConfSw = F div
    (0x69, (1).to_bytes(4, "little")),
]
DELAY_PRESET_DEL = [                                #to change delay preset del0
    #DEL0
    (0x80, (5).to_bytes(4, "little")),               #DELCNT0
    (0x5D, bytes([0x04])),                           #Ddelay0
    (0x56, bytes([0x01])),                           #Adelay0
    #DEL1
    (0x16, (22).to_bytes(4, "little")),               #DELCNT1
    (0x5E, bytes([0x04])),                           #Ddelay1
    (0x57, bytes([0x01])),                           #Adelay1
    # DEL2
    (0x19, (33).to_bytes(4, "little")),               #DELCNT2
    (0x5F, bytes([0x04])),                           #Ddelay2
    (0x58, bytes([0x01])),                           #Adelay2
    #DEL3
    (0x1A, (44).to_bytes(4, "little")),               #DELCNT3
    (0x60, bytes([0x04])),                           #Ddelay3
    (0x59, bytes([0x01])),                           #Adelay3
    # #DEL4
    # (0x1B, (3).to_bytes(4, "little")),               #DELCNT4
    # (0x5A, bytes([0x04])),                           #Adelay4
    # #DEL5
    # (0x1C, (3).to_bytes(4, "little")),               #DELCNT5
    # (0x62, bytes([0x04])),                           #Ddelay5
    # (0x5B, bytes([0x01])),                           #Adelay5
    # #DEL6
    # (0x1D, (3).to_bytes(4, "little")),               #DELCNT6
    # (0x63, bytes([0x04])),                           #Ddelay6
    # (0x5C, bytes([0x01])),                           #Adelay6
    # #DEL7
    # (0x1E, (3).to_bytes(4, "little")),               #DELCNT7
]

POSTDELAY_PRESET_POSTDEL = [
    (0x26, (258).to_bytes(2, "little")),            #PostCnt0          
    (0x27, (11).to_bytes(2, "little")),             #PostCnt1
    (0x28, (21).to_bytes(2, "little")),             #PostCnt2
    (0x29, (32).to_bytes(2, "little")),             #PostCnt3
    (0x2A, (40).to_bytes(2, "little")),             #PostCnt4
    (0x2B, (54).to_bytes(2, "little")),             #PostCnt5
    (0x2C, (64).to_bytes(2, "little")),             #PostCnt6
    (0x2D, (75).to_bytes(2, "little")),             #PostCnt7
]

OUT0_CONFIG2_DEL0_DEL1 = [
    (0x10, bytes([0x00])),#COMMAND -OFF
    (0x2E, bytes([0x00])),#MUXSETCONFIG10->CONFIG1 RISEDELAY-->NC
    (0x30, bytes([0x00])),#MUXRESCONFIG10->CONFIG1 FALLDELAY-->NC
    (0x2F, bytes([0x03])),#MUXSETCONFIG20->CONFIG2 RISEDELAY-->del0
    (0x31, bytes([0x04])),#MUXRESCONFIG20->CONFIG2 FALLDELAY-->del1
    (0x10, bytes([0x01])),#COMMAND -OFF
]

OUT1_CONFIG2_DEL0_DEL1 = [
    (0x10, bytes([0x00])),#COMMAND -OFF
    (0x32, bytes([0x00])),#MUXSETCONFIG11->CONFIG1 RISEDELAY-->NC
    (0x34, bytes([0x00])),#MUXRESCONFIG11->CONFIG1 FALLDELAY-->NC
    (0x33, bytes([0x03])),#MUXSETCONFIG21->CONFIG2 RISEDELAY-->del0
    (0x35, bytes([0x04])),#MUXRESCONFIG21->CONFIG2 FALLDELAY-->del1
]
OUT2_CONFIG2_DEL0_DEL1 = [
    (0x10, bytes([0x00])),#COMMAND -OFF
    (0x36, bytes([0x00])),#MUXSETCONFIG13->CONFIG1 RISEDELAY-->NC
    (0x38, bytes([0x00])),#MUXRESCONFIG13->CONFIG1 FALLDELAY-->NC
    (0x37, bytes([0x03])),#MUXSETCONFIG23->CONFIG2 RISEDELAY-->del0
    (0x39, bytes([0x04])),#MUXRESCONFIG23->CONFIG2 FALLDELAY-->del1
    (0x7A, bytes([0x00])),#LOGIC OUT
    (0x10, bytes([0x01])),#COMMAND -OFF
]
OUT3_CONFIG2_DEL0_DEL1 = [
    (0x10, bytes([0x00])),#COMMAND -OFF
    (0x3A, bytes([0x00])),#MUXSETCONFIG10->CONFIG1 RISEDELAY-->NC
    (0x3C, bytes([0x00])),#MUXRESCONFIG10->CONFIG1 FALLDELAY-->NC
    (0x3B, bytes([0x03])),#MUXSETCONFIG20->CONFIG2 RISEDELAY-->del0
    (0x3D, bytes([0x04])),#MUXRESCONFIG20->CONFIG2 FALLDELAY-->del1
    (0x7B, bytes([0x01])),#LOGIC OUT
]
OUT4_CONFIG2_DEL0_DEL1 = [
    (0x10, bytes([0x00])),#COMMAND -OFF
    (0x3E, bytes([0x00])),#MUXSETCONFIG10->CONFIG1 RISEDELAY-->NC
    (0x40, bytes([0x00])),#MUXRESCONFIG10->CONFIG1 FALLDELAY-->NC
    (0x3F, bytes([0x03])),#MUXSETCONFIG20->CONFIG2 RISEDELAY-->del0
    (0x41, bytes([0x04])),#MUXRESCONFIG20->CONFIG2 FALLDELAY-->del1
    (0x7C, bytes([0x02])),#LOGIC OUT
]
OUT5_CONFIG2_DEL0_DEL1 = [
    (0x10, bytes([0x00])),#COMMAND -OFF
    (0x42, bytes([0x00])),#MUXSETCONFIG10->CONFIG1 RISEDELAY-->NC
    (0x44, bytes([0x00])),#MUXRESCONFIG10->CONFIG1 FALLDELAY-->NC
    (0x43, bytes([0x03])),#MUXSETCONFIG20->CONFIG2 RISEDELAY-->del0
    (0x45, bytes([0x04])),#MUXRESCONFIG20->CONFIG2 FALLDELAY-->del1
    (0x7D, bytes([0x03])),#LOGIC OUT
]
OUT6_CONFIG2_DEL0_DEL1 = [
    (0x10, bytes([0x00])),#COMMAND -OFF
    (0x46, bytes([0x00])),#MUXSETCONFIG10->CONFIG1 RISEDELAY-->NC
    (0x48, bytes([0x00])),#MUXRESCONFIG10->CONFIG1 FALLDELAY-->NC
    (0x47, bytes([0x03])),#MUXSETCONFIG20->CONFIG2 RISEDELAY-->del0
    (0x49, bytes([0x04])),#MUXRESCONFIG20->CONFIG2 FALLDELAY-->del1
]
OUT7_CONFIG2_DEL0_DEL1 = [
    (0x10, bytes([0x00])),#COMMAND -OFF
    (0x4A, bytes([0x00])),#MUXSETCONFIG10->CONFIG1 RISEDELAY-->NC
    (0x4C, bytes([0x00])),#MUXRESCONFIG10->CONFIG1 FALLDELAY-->NC
    (0x4B, bytes([0x03])),#MUXSETCONFIG20->CONFIG2 RISEDELAY-->del0
    (0x4D, bytes([0x04])),#MUXRESCONFIG20->CONFIG2 FALLDELAY-->del1
]
OUT_ANOUT_OUT7_CONFIG2_1V = [
    (0x10, bytes([0x00])),#COMMAND -OFF
    (0x6B, (3).to_bytes(2, "little")),#DAC1->CONFIG1
    (0x6C, (4095).to_bytes(2, "little")),#DAC2->CONFIG2
    (0x50, bytes([0x07])),#MUXDAC->TRIGGER_SOURCE->OUT7
]
OUT_PRET_OUT0= [
    (0x10, bytes([0x00])),#COMMAND -OFF
    (0x4F, bytes([0x00])),#muxPreT->TRIGGERSOURCE->OUT0
    
]
OUT_COMT_OPTCLK= [
    (0x10, bytes([0x00])),#COMMAND -OFF
    (0x4E, bytes([0x08])),#muxTrig1OUT->TRIGGERSOURCE->OPTCLK
    
]
if __name__ == "__main__":
    # run_seq_on_device with dry_run=True (default) is always safe to run —
    # it only decodes/validates, never touches hardware unless you pass
    # dry_run=False explicitly and type YES at the confirm prompt.
    run_seq_on_device(INTERNAL_100MHz_SEQUENCE, dry_run=True)
    run_seq_on_device(EXTERNALSINGLEIN_CLKIN_100MHz_SEQUENCE,dry_run=True)
    run_seq_on_device(EXTERNALDUALIN_CLKIN_100MHZ_SYNCIN_20MHZ_SEQUENCE,dry_run=True)
    run_seq_on_device(CONFIG_BURST_GATE,dry_run=True)
    run_seq_on_device(DELAY_PRESET_DEL,dry_run=True)
    run_seq_on_device(POSTDELAY_PRESET_POSTDEL,dry_run=True)
    run_seq_on_device(OUT_ANOUT_OUT7_CONFIG2_1V,dry_run=True)
    run_seq_on_device(OUT0_CONFIG2_DEL0_DEL1,dry_run=True)
    run_seq_on_device(PRESET1_CHANNEL_SEQUENCE,dry_run=True)
    

    print("\nTo test your OWN hand-written seq, paste it above (or import it)")
    print("and call: inspect_seq(YOUR_SEQ)  or  run_seq_on_device(YOUR_SEQ, dry_run=True/False)")