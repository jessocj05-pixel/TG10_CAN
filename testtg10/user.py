"""user.py — interactive user-input collector + seq builder + pre-flight arm gate.

Two-phase design:
  1. build_config_seq()  -> everything EXCEPT the final Command=ON write.
  2. arm_device(read_reg_fn, send_fn) -> reads CLKvalid/PLL1locked live from
     device, only sends Command=ON if lock confirmed. Raises otherwise.

This split exists because Command=ON is the one write that can silently
fault the board (Sec5.7.1) — it must not be bundled blindly into a static
seq list, it needs a live read-check right before it fires.

Usage in v3.py:
    from user import build_config_seq, arm_device, check_no_addr_collisions

    seq, ctx = build_config_seq()
    if not check_no_addr_collisions(seq):
        raise RuntimeError("addr collisions in seq, aborting")
    send(seq)                         # your existing CAN send fn, config only
    arm_device(read_register, send)   # your existing read/send fns, does the ON write
"""

from calculations import (
    resolve_vco_mode, system_clock_hz,
    calc_trigger_config,
    check_clock_lock, check_pll1_lock,
    calc_delay, validate_delay, min_delay_time_s, max_delay_time_s,
    calc_post_delay_checked, min_post_delay_s, max_post_delay_s,
    calc_burst_mode, calc_freq_div_mode,
    calc_dac_config, calc_watchdog_period,
    parse_time, parse_freq,
)

# ================= REGISTER ADDR MAPS =================
# Values below marked "verify" came from your CAN dump / earlier messages.
# CONFIRM every one against your actual protocol doc before trusting a live send.

REG_COMMAND        = 0x10   # confirmed from your dump
REG_OSCCLKMUX       = 0x75   # confirmed
REG_OSCCLOCK        = 0x11   # confirmed
REG_VCO             = 0x6D   # confirmed
REG_NDIV            = 0x12   # confirmed
REG_MUX_RATECLK     = 0x55   # confirmed
REG_MUX_STARTTRG    = 0x54   # confirmed
REG_RATEDIV         = 0x20   # confirmed
REG_MUX_CONFSW      = 0x52   # confirmed (F div mode select)
REG_FDIV            = 0x69   # confirmed addr, PARKED range (65535 vs 32767 ambiguity)
REG_BURSTCOUNT      = 0x74   # confirmed
REG_DAC1            = 0x6B   # confirmed
REG_DAC2            = 0x6C   # confirmed

# from your protocol-note message — NOT cross-checked against any manual I have.
# VERIFY these against your actual protocol doc before relying on the arm-gate.
REG_CLKVALID        = 0x1F   # RegID 31 per your note
REG_PLL1LOCKED       = 0x7E   # RegID 126 per your note
REG_ERRORCODE        = 0x02   # RegID 2 per your note

DELAY_REGS = {
    0: {"cnt": 0x80, "d": 0x5D, "a": 0x56},
    1: {"cnt": 0x16, "d": 0x5E, "a": 0x57},
    2: {"cnt": 0x19, "d": 0x5F, "a": 0x58},
    3: {"cnt": 0x1A, "d": 0x60, "a": 0x59},
    4: {"cnt": 0x1B, "d": None, "a": 0x5A},   # own 100MHz clk, no D-delay
    5: {"cnt": 0x1C, "d": 0x5B, "a": 0x5C},
    6: {"cnt": 0x1D, "d": None, "a": None},   # UNVERIFIED - disabled until real addr confirmed
    7: {"cnt": 0x1E, "d": None, "a": None},   # shares ch6's D/A regs once ch6 confirmed
}
POSTDEL_REGS = {i: 0x26 + i for i in range(8)}  # verify past ch1

REG_TRIGGER_TMIN = None   # fill real addr before enabling watchdog
REG_TRIGGER_TMAX = None   # fill real addr before enabling watchdog


# ================= HELPERS =================

def ask(prompt, default=None, required=True):
    while True:
        raw = input(f"{prompt}" + (f" [{default}]" if default else "") + ": ").strip()
        if not raw and default is not None:
            return default
        if not raw and not required:
            return None
        if raw:
            return raw
        print("  required, try again")


def check_no_addr_collisions(seq, exempt_addrs=None):
    """
    Detect same register addr written more than once with different payloads
    WITHIN what should be a single logical config. Registers meant to be
    written multiple times by design (e.g. Command: OFF at start, ON at end)
    must be passed in exempt_addrs or they'll trigger false-positive flags.

    Default exemption: REG_COMMAND, since every valid seq legitimately writes
    it twice (OFF then ON) — that's intentional sequencing, not a collision.
    """
    if exempt_addrs is None:
        exempt_addrs = {REG_COMMAND}

    seen = {}
    collisions = []
    for addr, payload in seq:
        if addr in exempt_addrs:
            continue
        if addr in seen and seen[addr] != payload:
            collisions.append((addr, seen[addr], payload))
        seen[addr] = payload
    if collisions:
        print("\n!! ADDRESS COLLISIONS DETECTED:")
        for addr, old, new in collisions:
            print(f"   0x{addr:02X}: {old.hex()} overwritten by {new.hex()}")
        return False
    return True


# ================= PHASE 1: BUILD CONFIG SEQ (no Command=ON) =================

def build_config_seq():
    """
    Prompt user for every value, validate, build seq list — WITHOUT the final
    Command=ON write. Returns (seq, ctx) where ctx carries values later
    needed by arm_device() diagnostics (e.g. f_hz for context in error msgs).
    """
    print("=== SY4000 config - enter values ===\n")

    # ---------- 1. CLOCK ----------
    ext_clk_str = ask("External clock freq (e.g. 20MHz)", default="20MHz")
    ext_clk_hz = parse_freq(ext_clk_str)
    res = resolve_vco_mode(ext_clk_hz / 1e6)
    f_hz = system_clock_hz("external", n_div=res["ndiv"], ext_clk_hz=ext_clk_hz)
    print(f"  -> Ndiv={res['ndiv']} VCO={res['vco2']} sysclk={f_hz/1e9:.3f}GHz")

    min_t = min_delay_time_s(f_hz)
    max_t = max_delay_time_s(f_hz)
    print(f"  (delay range ch0-3,5,6: ~{min_t*1e9:.1f}ns .. ~{max_t*1e3:.1f}ms)")
    min_t4 = min_delay_time_s(f_hz, channel=4)
    max_t4 = max_delay_time_s(f_hz, channel=4)
    print(f"  (delay range ch4 (own 100MHz clk): ~{min_t4*1e9:.1f}ns .. ~{max_t4*1e3:.1f}ms)")
    min_pd = min_post_delay_s(f_hz)
    max_pd = max_post_delay_s(f_hz)
    print(f"  (post-delay range: ~{min_pd*1e9:.1f}ns .. ~{max_pd*1e9:.1f}ns)\n")

    # ---------- 2. TRIGGER MODE (fixes OPTCLK vs 10ns rate-divider bug) ----------
    print("Trigger mode:")
    print("  1) internal_100mhz  - internal trigger, 10ns-resolution rate divider")
    print("  2) internal_extclk  - internal trigger, rate divider counts external clock periods")
    print("  3) external_syncin  - straight SYNC IN trigger, no rate divider")
    mode_choice = ask("  choose 1/2/3", default="2")
    mode_map = {"1": "internal_100mhz", "2": "internal_extclk", "3": "external_syncin"}
    trig_mode = mode_map.get(mode_choice, "internal_extclk")

    ratediv = None
    if trig_mode != "external_syncin":
        period_str = ask("Trigger period (e.g. 100ns)", default="100ns")
        while True:
            try:
                trig_cfg = calc_trigger_config(
                    trig_mode,
                    period_s=parse_time(period_str),
                    ext_clk_hz=ext_clk_hz if trig_mode == "internal_extclk" else None,
                )
                ratediv = trig_cfg["ratediv"]
                break
            except ValueError as e:
                print(f"  !! {e}")
                period_str = ask("  retry trigger period")
        print(f"  -> mode={trig_mode} ratediv={ratediv}\n")
    else:
        trig_cfg = calc_trigger_config("external_syncin")
        print(f"  -> mode={trig_mode}, no rate divider used\n")

    # ---------- 3. DELAY CHANNELS ----------
    delay_results = {}
    print("Delay channels 0-5 (ch6/7 shared, asked separately). Leave blank to skip.")
    for ch in range(6):
        while True:
            t_str = ask(f"  DEL{ch} time (e.g. 250ns)", required=False)
            if t_str is None:
                break
            f_for_ch = 100e6 if ch == 4 else f_hz
            try:
                r = calc_delay(parse_time(t_str), f_for_ch, ch)
                validate_delay(r, ch)
                delay_results[ch] = r
                print(f"    -> {r}")
                break
            except ValueError as e:
                print(f"    !! {e}")
                lo = min_delay_time_s(f_hz, channel=ch if ch == 4 else None)
                hi = max_delay_time_s(f_hz, channel=ch if ch == 4 else None)
                print(f"    valid range: {lo*1e9:.1f}ns .. {hi*1e3:.1f}ms, try again")

    if DELAY_REGS[6]["d"] is None:
        print("  DEL6/7 skipped - register addr unverified, edit DELAY_REGS[6] in user.py to enable")
    else:
        while True:
            t6_str = ask("  DEL6/7 (shared A/D delay) time (e.g. 1us)", required=False)
            if t6_str is None:
                break
            try:
                r6 = calc_delay(parse_time(t6_str), f_hz, 6)
                validate_delay(r6, 6)
                delay_results[6] = r6
                print(f"    -> ch6/7 shared: {r6}")
                break
            except ValueError as e:
                print(f"    !! {e}")
                print(f"    valid range: {min_t*1e9:.1f}ns .. {max_t*1e3:.1f}ms, try again")

    # ---------- 4. POST DELAY ----------
    postdel_results = {}
    print("\nPost-delay widths 0-7. Leave blank to skip.")
    for ch in range(8):
        while True:
            w_str = ask(f"  PostDel{ch} width (e.g. 500ns)", required=False)
            if w_str is None:
                break
            try:
                pd = calc_post_delay_checked(parse_time(w_str), f_hz)
                postdel_results[ch] = pd
                print(f"    -> {pd}")
                break
            except ValueError as e:
                print(f"    !! {e}")
                print(f"    valid range: {min_pd*1e9:.1f}ns .. {max_pd*1e9:.1f}ns, try again")

    # ---------- 5. DAC ----------
    print()
    dac1_str = ask("DAC1 voltage, Config1 (0-1V, e.g. 0.3)", default="0.3")
    dac2_str = ask("DAC2 voltage, Config2 (0-1V, e.g. 1.0)", default="1.0")
    while True:
        try:
            dac = calc_dac_config(float(dac1_str), float(dac2_str))
            break
        except ValueError as e:
            print(f"  !! {e}")
            dac1_str = ask("  retry DAC1 voltage")
            dac2_str = ask("  retry DAC2 voltage")
    print(f"  -> {dac}\n")

    # ---------- 6. BURST / F DIV (PARKED range, addr confirmed) ----------
    burst_str = ask("Burst count (1-65535, e.g. 100)", default="100")
    fdiv_str = ask("F div (e.g. 1) [range parked, not fully verified]", default="1")
    while True:
        try:
            burst = calc_burst_mode(int(burst_str), fdiv_n=int(fdiv_str))
            break
        except ValueError as e:
            print(f"  !! {e}")
            burst_str = ask("  retry burst count")
            fdiv_str = ask("  retry f_div")
    print(f"  -> {burst}\n")

    # ---------- 7. BUILD SEQ (config only, no Command=ON) ----------
    seq = [
        (REG_COMMAND, bytes([0x00])),                                      # Command OFF first
        (REG_OSCCLKMUX, bytes([0x01])),                                    # OscClkMux = External
        (REG_OSCCLOCK, bytes([int(ext_clk_hz / 1e6)])),                    # OscClock
        (REG_VCO, bytes([0x01 if res["vco2"] == "3GHz" else 0x00])),       # VCO
        (REG_NDIV, res["ndiv"].to_bytes(4, "little")),                     # Ndiv
    ]

    if trig_cfg["mux_rateclk"] is not None:
        seq.append((REG_MUX_RATECLK, bytes([trig_cfg["mux_rateclk"]])))
    seq.append((REG_MUX_STARTTRG, bytes([trig_cfg["mux_trigger"]])))
    if trig_cfg["ratediv"] is not None:
        seq.append((REG_RATEDIV, trig_cfg["ratediv"].to_bytes(4, "little")))

    for ch, r in delay_results.items():
        addr = DELAY_REGS[ch]
        seq.append((addr["cnt"], r["delay_counter"].to_bytes(4, "little")))
        if addr["d"] is not None and "d_delay" in r:
            seq.append((addr["d"], bytes([r["d_delay"]])))
        if addr["a"] is not None and "a_delay" in r:
            seq.append((addr["a"], bytes([r["a_delay"]])))

    for ch, pd in postdel_results.items():
        seq.append((POSTDEL_REGS[ch], pd.to_bytes(2, "little")))

    seq.append((REG_DAC1, dac["dac1"].to_bytes(2, "little")))
    seq.append((REG_DAC2, dac["dac2"].to_bytes(2, "little")))
    seq.append((REG_BURSTCOUNT, burst["burst_count"].to_bytes(4, "little")))
    seq.append((REG_FDIV, burst["f_div"].to_bytes(4, "little")))

    # ---------- 8. VERIFY SHAPE + COLLISIONS ----------
    assert all(isinstance(a, int) for a, _ in seq), "seq addr type check failed"
    assert all(isinstance(p, (bytes, bytearray)) for _, p in seq), "seq payload type check failed"

    ok = check_no_addr_collisions(seq)
    if not ok:
        proceed = ask("Collisions found above - proceed anyway? (y/n)", default="n")
        if proceed.lower() != "y":
            print("aborted due to collisions")
            return None, None

    print(f"\n=== config seq built, {len(seq)} entries (Command=ON NOT included) ===")
    for addr, payload in seq:
        print(f"  0x{addr:02X}: {payload.hex()}")

    ctx = {"f_hz": f_hz, "ext_clk_hz": ext_clk_hz, "trig_mode": trig_mode, "res": res}
    return seq, ctx


# ================= PHASE 2: ARM DEVICE (Command=ON, gated by live lock check) =================

def arm_device(read_reg_fn, send_fn, require_pll1=False):
    """
    Reads CLKvalid (and optionally PLL1locked) live from device via
    read_reg_fn, only sends Command=ON if lock confirmed.

    read_reg_fn(addr) -> int   (single status byte read back from device)
    send_fn(seq)       -> None (your existing CAN send, seq = list of (addr,payload) tuples)

    Raises RuntimeError if lock not ready - does NOT send Command=ON in that case.
    """
    clkvalid = read_reg_fn(REG_CLKVALID)
    check_clock_lock(clkvalid)   # raises if not 0x03

    pll1 = read_reg_fn(REG_PLL1LOCKED)
    check_pll1_lock(pll1, required=require_pll1)   # only raises if require_pll1=True

    send_fn([(REG_COMMAND, bytes([0x01]))])

    # confirm it stuck
    cmd_status = read_reg_fn(REG_COMMAND)
    if cmd_status != 0x01:
        raise RuntimeError(f"Command=ON did not stick, readback=0x{cmd_status:02X}")

    err = read_reg_fn(REG_ERRORCODE)
    if err != 0:
        raise RuntimeError(f"device reports error code 0x{err:02X} after arming")

    print("Device armed: Command=ON confirmed, no error reported.")
    return True


if __name__ == "__main__":
    seq, ctx = build_config_seq()
    if seq:
        print("\nConfig seq ready. To arm the device, call arm_device(read_reg_fn, send_fn)")
        print("with your real CAN read/send functions wired in from v3.py.")