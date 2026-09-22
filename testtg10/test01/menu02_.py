
"""
menu.py – Interactive UI for EKSMA SY4000 / TG10.

Architecture
------------
    menu.py  →  operations.py  →  calculation.py + registers.py  →  (later) v3.py / CAN

This file only:
  - asks the user questions
  - calls build_* / seq_* from operations
  - keeps application state
  - prints the resulting register sequence (offline verification)

No CAN / serial I/O lives here.
"""

from __future__ import annotations

from operations02 import (
    # Sync / clock
    seq_internal_100mhz,
    seq_external_clkin,
    seq_external_syncin,
    seq_external_dual_in,
    seq_oneshot_software,
    seq_oneshot_smart,
    build_internal_100mhz_from_period,
    build_external_clkin_from_period,
    build_external_dual_in_from_period,
    # RateDiv
    seq_set_ratediv,
    # Delay
    build_delay_channel,
    build_post_delay_channel,
    seq_channels,
    seq_delay_channel,
    seq_post_delay_channel,
    # Config
    seq_config_normal,
    seq_config_gate,
    seq_config_ngate,
    seq_config_burst_syncin,
    seq_config_burst_gate,
    seq_config_burst_ngate,
    seq_config_burst_software,
    seq_config_freq_div,
    # Output
    seq_out0_config2_del0_del1,
    seq_out1_config2_del0_del1,
    seq_out2_config2_del0_del1,
    seq_out3_config2_del0_del1,
    seq_out4_config2_del0_del1,
    seq_out5_config2_del0_del1,
    seq_out6_config2_del0_del1,
    seq_out7_config2_del0_del1,
    seq_out_config_del,
    seq_out_anout_out7,
    seq_out_pret,
    seq_out_comt,
    seq_sr_block,
    # Run
    seq_run_on,
    seq_run_off,
)
from calculations02_ import (
    parse_time,
    parse_freq,
    rate_divider_from_period_100m,
    rate_divider_from_period_ext,
    clock_internal_100mhz,
    clock_external,
)

# ---------------------------------------------------------------------------
# Application state (UI layer only)
# ---------------------------------------------------------------------------
state = {
    "trig_mode": None,       # "internal" | "clkin" | "syncin" | "dual" | "oneshot"
    "f_hz": None,            # current system clock Hz
    "ext_clk_hz": None,      # external clock frequency if used
    "config_mode": "normal",
    "armed": False,
    "delay": {},             # ch → last delay time_s
    "postdelay": {},         # ch → last width_s
    "last_seq": [],          # most recent sequence (for save / re-print)
    "current_config" : {},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ask(prompt: str, default: str = "") -> str:
    if default:
        raw = input(f"{prompt} [{default}]: ").strip()
        return raw if raw else default
    return input(f"{prompt}: ").strip()


def print_sequence(seq, label: str = "sequence"):
    """Pretty-print a register sequence for offline verification."""
    print(f"\n--- {label} ({len(seq)} writes) ---")
    for reg, data in seq:
        if data is None:
            print(f"  (0x{reg:02X}, None)                       # READ")
        else:
            if len(data) <= 4:
                val = int.from_bytes(data, "little")
                print(f"  (0x{reg:02X}, {data.hex():<10s})  # = {val}")
            else:
                print(f"  (0x{reg:02X}, {data.hex()})")
    print("--- end ---")
    state["last_seq"] = list(seq)

def update_current_config(seq):
    """
    Add/update persistent configuration writes.

    If the same register is written again, the newer value replaces
    the previous value in the saved configuration.
    """
    for reg, data in seq:
        if data is not None:
            state["current_config"][reg] = data

def require_sync() -> bool:
    if state["trig_mode"] is None:
        print("!! Configure Sync first (menu 1)")
        return False
    return True


def require_f_hz() -> bool:
    if state["f_hz"] is None:
        print("!! System clock unknown – configure Sync first")
        return False
    return True


# ===========================================================================
# 1. Sync
# ===========================================================================

def menu_sync():
    print("\n--- Sync ---")
    print("1) Normal (internal 100 MHz)")
    print("2) External SINGLE IN — CLK IN")
    print("3) External SINGLE IN — SYNC IN")
    print("4) External DUAL IN — CLK IN + SYNC IN")
    print("5) One-shot FIRE (software)")
    print("6) One-shot FIRE (smart)")
    choice = ask("choose", default="1")

    if choice == "1":
        mode = ask("Enter as (1) Period or (2) Frequency", default="1")
        if mode == "2":
            f = parse_freq(ask("Frequency (e.g. 1kHz)", default="1kHz"))
            period_s = 1.0 / f
        else:
            period_s = parse_time(ask("Period (e.g. 1us)", default="1us"))

        seq = build_internal_100mhz_from_period(period_s, command_on=False)
        state["trig_mode"] = "internal"
        state["f_hz"] = 3_000_000_000
        state["ext_clk_hz"] = None
        state["syncin_hz"] = None
        update_current_config(seq)
        print_sequence(seq, "internal 100 MHz")

    elif choice == "2":
        fext = parse_freq(ask("External clock frequency (e.g. 50MHz)", default="100MHz"))
        mode = ask("Enter as (1) Period or (2) Frequency", default="1")
        if mode == "2":
            f = parse_freq(ask("Desired output frequency (e.g. 1kHz)"))
            period_s = 1.0 / f
        else:
            period_s = parse_time(ask("Desired period (e.g. 1us)", default="1us"))

        seq = build_external_clkin_from_period(
            period_s, fext, command_on=False, include_readback=True
        )
        cfg = clock_external(fext)
        state["trig_mode"] = "clkin"
        state["ext_clk_hz"] = fext
        state["f_hz"] = cfg.f_hz
        state["syncin_hz"] = syncin_hz
        update_current_config(seq)
        print_sequence(seq, "external CLKIN")

    elif choice == "3":
        rd_str = ask("RateDiv now? (Enter = default 2, set later in Freq)", default="")
        ratediv = int(rd_str) if rd_str else 2
        seq = seq_external_syncin(ratediv=ratediv, command_on=False)
        state["trig_mode"] = "syncin"
        state["f_hz"] = 3_000_000_000
        state["ext_clk_hz"] = None
        state["syncin_hz"] = None
        update_current_config(seq)
        print_sequence(seq, "external SYNCIN")
        print("(RateDiv can still be changed later via menu 2 Freq/Period)")

    elif choice == "4":
        fext = parse_freq(ask("External CLKIN frequency (e.g. 100MHz)", default="100MHz"))
        syncin_hz = parse_freq(
        ask("SYNC IN frequency (e.g. 10MHz)")
        )
        mode = ask("Enter as (1) Period or (2) Frequency", default="1")
        if mode == "2":
            f = parse_freq(ask("Desired output frequency"))
            period_s = 1.0 / f
        else:
            period_s = parse_time(ask("Desired period (e.g. 1us)", default="1us"))

        seq = build_external_dual_in_from_period(period_s, fext,syncin_hz, command_on=False)
        cfg = clock_external(fext)
        state["trig_mode"] = "dual"
        state["ext_clk_hz"] = fext
        state["f_hz"] = cfg.f_hz
        state["syncin_hz"] = syncin_hz
        update_current_config(seq)
        print_sequence(seq, "external DUAL IN")

    elif choice == "5":
        seq = seq_oneshot_software()
        update_current_config(seq)
        print_sequence(seq, "one-shot FIRE (software)")

    elif choice == "6":
        seq = seq_oneshot_smart()
        update_current_config(seq)
        print_sequence(seq, "one-shot FIRE (smart)")

    else:
        print("invalid choice")


# ===========================================================================
# 2. Freq / Period
# ===========================================================================

def menu_freq():
    if not require_sync():
        return

    print("\n--- Freq / Period ---")
    print(f"Current mode : {state['trig_mode']}")
    print(f"System clock : {state['f_hz']} Hz" if state["f_hz"] else "")

    mode = ask("Enter as (1) Period or (2) Frequency", default="1")
    if mode == "2":
        f = parse_freq(ask("Frequency (e.g. 10kHz)"))
        period_s = 1.0 / f
    else:
        period_s = parse_time(ask("Period (e.g. 100us)"))

    if state["trig_mode"] == "internal":
        ratediv = rate_divider_from_period_100m(period_s * 1e9)
    elif state["trig_mode"] == "clkin" and state["ext_clk_hz"]:
        ratediv = rate_divider_from_period_ext(
            period_s,
            state["ext_clk_hz"]
        )

    elif state["trig_mode"] == "dual" and state["syncin_hz"]:
        ratediv = rate_divider_from_period_ext(
            period_s,
            state["syncin_hz"]
        )
    else:
        use = ask("Calculate from 100 MHz (1) or enter RateDiv raw (2)?", default="1")
        if use == "2":
            ratediv = int(ask("RateDiv"))
        else:
            ratediv = rate_divider_from_period_100m(period_s * 1e9)

    seq = seq_set_ratediv(ratediv)
    update_current_config(seq)
    print_sequence(seq, f"RateDiv = {ratediv}")


# ===========================================================================
# 3. Config1 / Config2
# ===========================================================================

def menu_config():
    print("\n--- Config ---")
    print("1) Normal")
    print("2) GATE")
    print("3) nGATE")
    print("4) Burst – SYNCIN")
    print("5) Burst – GATE")
    print("6) Burst – nGATE")
    print("7) Burst – software")
    print("8) Frequency divider")
    choice = ask("choose", default="1")

    if choice == "1":
        seq = seq_config_normal()
        update_current_config(seq)
        state["config_mode"] = "normal"
    elif choice == "2":
        seq = seq_config_gate()
        update_current_config(seq)
        state["config_mode"] = "gate"
    elif choice == "3":
        seq = seq_config_ngate()
        update_current_config(seq)
        state["config_mode"] = "ngate"
    elif choice == "4":
        n = int(ask("Burst count", default="1"))
        fd = int(ask("Fdiv", default="1"))
        seq = seq_config_burst_syncin(n, fd)
        update_current_config(seq)
        state["config_mode"] = "burst_syncin"
    elif choice == "5":
        n = int(ask("Burst count", default="100"))
        fd = int(ask("Fdiv", default="1"))
        seq = seq_config_burst_gate(n, fd)
        update_current_config(seq)
        state["config_mode"] = "burst_gate"
    elif choice == "6":
        n = int(ask("Burst count", default="100"))
        fd = int(ask("Fdiv", default="1"))
        seq = seq_config_burst_ngate(n, fd)
        update_current_config(seq)
        state["config_mode"] = "burst_ngate"
    elif choice == "7":
        n = int(ask("Burst count", default="100"))
        fd = int(ask("Fdiv", default="1"))
        seq = seq_config_burst_software(n, fd)
        update_current_config(seq)
        state["config_mode"] = "burst_software"
    elif choice == "8":
        fd = int(ask("Fdiv", default="1"))
        seq = seq_config_freq_div(fd)
        update_current_config(seq)
        state["config_mode"] = "fdiv"
    else:
        print("invalid choice")
        return

    print_sequence(seq, f"config = {state['config_mode']}")


# ===========================================================================
# 4. Delay / Post-delay  (limits from TG10 manual §3.1)
# ===========================================================================

def _fmt_time(s: float) -> str:
    if s < 1e-9:
        return f"{s*1e12:.1f} ps"
    if s < 1e-6:
        return f"{s*1e9:.3f} ns"
    if s < 1e-3:
        return f"{s*1e6:.3f} us"
    if s < 1.0:
        return f"{s*1e3:.3f} ms"
    return f"{s:.3f} s"


def menu_delay():
    """
    Limits from TG10 manual (section 3.1):
      Delay        : 0 … 150 ms   (entry from 25 ps)
      Pulse width  : 4 ns … 150 ms
      High-res res : 25 ps   (DEL0–3, DEL5)
      Low-res res  : ~9.4 ns (DEL6/DEL7 coarse; share fine 25 ps)
      DEL4         : different clock frequency
    """
    if not require_f_hz():
        return

    f_hz = state["f_hz"]
    d_tmin = 25e-12          # 25 ps
    d_tmax = 150e-3          # 150 ms
    p_tmin = 4e-9            # 4 ns
    p_tmax = 150e-3          # 150 ms

    print("\n--- Delay ---")
    print(f"System clock: {f_hz/1e9:.3f} GHz")
    print(f"Delay  limits: {_fmt_time(d_tmin)} .. {_fmt_time(d_tmax)}  (res 25 ps high-res)")
    print(f"Post   limits: {_fmt_time(p_tmin)} .. {_fmt_time(p_tmax)}")
    print("DEL0–3,5: full-res  |  DEL4: alt clock  |  DEL6/7: coarse 9.4 ns + shared fine 25 ps")
    print()
    print("1) Delay channels (del0–del7)")
    print("2) Post-delay channels (postdel0–postdel7)")
    print("3) Load PRESET1")
    choice = ask("choose", default="1")

    if choice == "1":
        print("\nDelay channels del0–del7")
        print(f"Time range: {_fmt_time(d_tmin)} .. {_fmt_time(d_tmax)}")
        print("Units: ps / ns / us / ms / s   (e.g. 25ps, 500ps, 25ns, 1us)")
        print("Leave channel empty to finish.")
        while True:
            ch_str = ask("Channel 0-7 (Enter=done)", default="")
            if ch_str == "":
                break
            ch = int(ch_str)
            if ch not in range(8):
                print("!! channel must be 0-7")
                continue
            if ch == 4:
                print("  note: DEL4 uses alternate clock frequency")
            elif ch in (6, 7):
                print("  note: DEL6/7 coarse ~9.4 ns + shared fine 25 ps")

            t = parse_time(ask(f"del{ch} time (ps/ns/us/ms/s)", default="25ps"))
            if t < d_tmin:
                print(f"!! time {_fmt_time(t)} below {_fmt_time(d_tmin)} – raising")
                t = d_tmin
            if t > d_tmax:
                print(f"!! time {_fmt_time(t)} above {_fmt_time(d_tmax)} – clamping")
                t = d_tmax
            try:
                seq = build_delay_channel(ch, t, f_hz)
                state["delay"][ch] = t
                update_current_config(seq)
                print_sequence(seq, f"del{ch} = {_fmt_time(t)}")
            except ValueError as e:
                print(f"!! {e}")

    elif choice == "2":
        print("\nPost-delay channels postdel0–postdel7")
        print(f"Width range: {_fmt_time(p_tmin)} .. {_fmt_time(p_tmax)}")
        print("Units: ps / ns / us / ms / s   (e.g. 4ns, 10ns, 1us)")
        print("Leave channel empty to finish.")
        while True:
            ch_str = ask("Channel 0-7 (Enter=done)", default="")
            if ch_str == "":
                break
            ch = int(ch_str)
            if ch not in range(8):
                print("!! channel must be 0-7")
                continue
            w = parse_time(ask(f"postdel{ch} width (ps/ns/us/ms/s)", default="4ns"))
            if w < p_tmin:
                print(f"!! width {_fmt_time(w)} below {_fmt_time(p_tmin)} – raising")
                w = p_tmin
            if w > p_tmax:
                print(f"!! width {_fmt_time(w)} above {_fmt_time(p_tmax)} – clamping")
                w = p_tmax
            seq = build_post_delay_channel(ch, w, f_hz)
            state["postdelay"][ch] = w
            update_current_config(seq)
            print_sequence(seq, f"postdel{ch} = {_fmt_time(w)}")


    else:
        print("invalid choice")


# ===========================================================================
# 5. Output
# ===========================================================================

from registers_ import SR_SOURCE_MAP

def _print_sr_sources():
    print("  code  source")
    for name, code in SR_SOURCE_MAP.items():
        print(f"   {code:2d}   {name}")

def _ask_sr_source(prompt: str, default: int) -> int:
    raw = ask(f"{prompt} (code or name)", default=str(default)).strip().lower()
    if raw.isdigit():
        val = int(raw)
        if 0 <= val <= 15:
            return val
        raise ValueError(f"source code must be 0-15, got {val}")
    matches = [(code, name) for code, name in SR_SOURCE_MAP if raw in name.lower()]
    if not matches:
        raise ValueError(f"unknown source {raw!r} – use 0-15 or a name from the list")
    matches.sort(key=lambda x: len(x[1]), reverse=True)
    return matches[0][0]

from registers_ import OUTPUTS
def menu_output():
    print("\n--- Output ---")
    print("0-7) Configure OUTn  (pick rise/fall sources from list)")
    print("a)   Analog out (DAC1/DAC2 → OUT7)")
    print("p)   Pre-trigger source (MuxPreT)")
    print("c)   Common trigger source (MuxTrg1Out)")
    choice = ask("choose", default="0")

    if choice in OUTPUTS:
        ch = int(choice)
        print(f"\nConfiguring OUT{ch}")
        print("Available sources:")
        _print_sr_sources()
        print()
        print("Config1 = normally left at 0 (no change)")
        print("Config2 = active rise / fall edges")
        print()

        s1 = _ask_sr_source("Config1 rise  (set1)", 0)
        r1 = _ask_sr_source("Config1 fall  (res1)", 0)
        s2 = _ask_sr_source("Config2 rise  (set2)", 3)
        r2 = _ask_sr_source("Config2 fall  (res2)", 4)

        logic = None
        if ch in (2, 3, 4, 5):
            logic_str = ask(
                f"Logic mux OUT{ch} (0=pass, 1=and prev, 2=or prev, 3=not prev, Enter=skip)",
                default="",
            )
            if logic_str != "":
                logic = int(logic_str)

        seq = seq_sr_block(ch, set1=s1, set2=s2, res1=r1, res2=r2)

        if logic is not None:
            extra = seq_out_config_del(
                ch, set_src=s2, res_src=r2, logic_mux=logic, command_on=False
            )
            logic_writes = [item for item in extra if item[0] in (0x7A, 0x7B, 0x7C, 0x7D)]
            seq = list(seq) + logic_writes

        name_s2 = next(
            (name for name, code in SR_SOURCE_MAP.items() if code == s2),
            f"code_{s2}"
        )

        name_r2 = next(
            (name for name, code in SR_SOURCE_MAP.items() if code == r2),
            f"code_{r2}"
        )
        update_current_config(seq)
        print_sequence(seq, f"OUT{ch}  rise={name_s2}  fall={name_r2}")

    elif choice.lower() == "a":
        d1 = int(ask("DAC1 code 0-4095", default="3"))
        d2 = int(ask("DAC2 code 0-4095", default="4095"))
        src = int(ask("MuxDAC source (7=OUT7)", default="7"))
        seq = seq_out_anout_out7(dac1=d1, dac2=d2, mux_dac_src=src)
        update_current_config(seq)
        print_sequence(seq, "analog out")

    elif choice.lower() == "p":
        src = int(ask("MuxPreT source (0=OUT0 …)", default="0"))
        seq = seq_out_pret(src)
        update_current_config(seq)
        print_sequence(seq, "MuxPreT")

    elif choice.lower() == "c":
        src = int(ask("MuxTrg1Out source (8=OPTCLK)", default="8"))
        seq = seq_out_comt(src)
        update_current_config(seq)
        print_sequence(seq, "MuxTrg1Out")

    else:
        print("invalid choice")


# ===========================================================================
# 6. Monitor
# ===========================================================================

def menu_monitor():
    print("\n--- Monitor ---")
    print("(Offline mode – no CAN connected)")
    print("Later this will read:")
    print("  Command, CLKvalid, PLL1locked, ErrorCode, …")
    print(f"Current state snapshot:")
    for k, v in state.items():
        if k == "last_seq":
            print(f"  last_seq : {len(v)} items")
        else:
            print(f"  {k:12s}: {v}")


# ===========================================================================
# 7. Save preset  (v3-style with comments)
# ===========================================================================

from registers_ import _REG_NAMES


def _format_payload(data: bytes) -> str:
    n = len(data)
    if n == 1:
        return f"bytes([0x{data[0]:02X}])"
    if n == 2:
        val = int.from_bytes(data, "little")
        return f"({val}).to_bytes(2, \"little\")"
    if n == 4:
        val = int.from_bytes(data, "little")
        return f"({val}).to_bytes(4, \"little\")"
    return f"bytes.fromhex('{data.hex()}')"


def menu_save_preset():
    if not state["current_config"]:
        print("!! No sequence to save – run an operation first")
        return

    name = ask("Preset name (Python identifier)", default="MY_PRESET")
    if not name.isidentifier():
        print("!! Invalid identifier")
        return

    path = "preset.py"
    lines = [f"\n{name} = [\n"]
    for reg, data in state["current_config"].items():
        reg_name = _REG_NAMES.get(reg, f"reg_0x{reg:02X}")
        if data is None:
            lines.append(
                f"    (0x{reg:02X}, None),".ljust(48) + f"  # {reg_name} = <READ>\n"
            )
        else:
            payload = _format_payload(data)
            val = int.from_bytes(data, "little")
            comment = f"{reg_name} = {val}"
            line = f"    (0x{reg:02X}, {payload}),"
            lines.append(line.ljust(48) + f"  # {comment}\n")
    lines.append("]\n")

    with open(path, "a") as f:
        f.writelines(lines)
    print(f"Appended {name} ({len(state['current_config'])} registers) → {path}")

def menu_load_preset():
    path = "preset.py"

    try:
        namespace = {}
        with open(path, "r") as f:
            exec(f.read(), {}, namespace)
    except FileNotFoundError:
        print("!! preset.py not found")
        return
    except Exception as e:
        print(f"!! Error loading preset.py: {e}")
        return

    # Only keep Python-list presets
    presets = {
        name: value
        for name, value in namespace.items()
        if not name.startswith("_") and isinstance(value, list)
    }

    if not presets:
        print("!! No presets found in preset.py")
        return

    print("\n--- Saved Presets ---")

    preset_names = list(presets.keys())

    for i, name in enumerate(preset_names, 1):
        print(f"  {i}) {name}")

    choice = ask("Select preset", default="1")

    try:
        index = int(choice) - 1
        if index < 0 or index >= len(preset_names):
            print("!! Invalid preset number")
            return
    except ValueError:
        print("!! Enter a preset number")
        return

    name = preset_names[index]
    seq = presets[name]

    state["last_seq"] = seq

    print(f"\nLoaded preset: {name}")
    print(f"Sequence contains {len(seq)} entries")

    print_sequence(seq, name)

# ===========================================================================
# 8. Other
# ===========================================================================

def menu_other():
    print("\n--- Other ---")
    print("1) One-shot FIRE (software) – pulse once")
    print("2) One-shot FIRE (smart) – pulse once")
    print("3) Re-print last sequence")
    choice = ask("choose", default="3")

    if choice == "1":
        seq = [
            (0x70, bytes([0x01])),   # OSTrig = START
            (0x70, bytes([0x00])),   # OSTrig = clear
        ]
        print_sequence(seq, "one-shot FIRE (software)")
    elif choice == "2":
        seq = [
            (0x70, bytes([0x01])),
            (0x70, bytes([0x00])),
        ]
        print_sequence(seq, "one-shot FIRE (smart)")
    elif choice == "3":
        if state["last_seq"]:
            print_sequence(state["last_seq"], "last sequence")
        else:
            print("!! nothing stored yet")
    else:
        print("invalid choice")


# ===========================================================================
# 9. Run / Stop
# ===========================================================================

def menu_run():
    print("\n--- Run / Stop ---")
    print("1) Command = ON")
    print("2) Command = OFF")
    choice = ask("choose", default="1")

    if choice == "1":
        seq = seq_run_on()
        state["armed"] = True
        print_sequence(seq, "RUN ON")
    elif choice == "2":
        seq = seq_run_off()
        state["armed"] = False
        print_sequence(seq, "RUN OFF")
    else:
        print("invalid choice")


# ===========================================================================
# Main loop
# ===========================================================================

MENU_TEXT = """
========== SY4000 manual control ==========
  1) Sync
  2) Freq/Period
  3) Config1/2
  4) Delay preset
  5) Output
  6) Monitor
  7) Save preset
  8) Load preset
  9) Other
  r) Run/Stop
  q) Quit
===========================================
"""

MENU_HANDLERS = {
    "1": menu_sync,
    "2": menu_freq,
    "3": menu_config,
    "4": menu_delay,
    "5": menu_output,
    "6": menu_monitor,
    "7": menu_save_preset,
    "8": menu_load_preset,
    "9": menu_other,
    "r": menu_run,
}


def main():
    print("SY4000 / TG10 control (offline sequence builder)")
    print("No CAN traffic is sent – sequences are printed only.\n")

    while True:
        print(MENU_TEXT)
        mode = state["trig_mode"] or "—"
        f = f"{state['f_hz']/1e9:.3f} GHz" if state["f_hz"] else "—"
        armed = "ARMED" if state["armed"] else "idle"
        print(f"  [{mode}]  f={f}  {armed}\n")

        choice = input("select: ").strip().lower()
        if choice == "q":
            print("bye")
            break

        handler = MENU_HANDLERS.get(choice)
        if handler:
            try:
                handler()
            except (ValueError, KeyError) as e:
                print(f"!! error: {e}")
            except KeyboardInterrupt:
                print("\n(cancelled)")
        else:
            print("invalid choice")


if __name__ == "__main__":
    main()
