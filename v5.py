"""
witth autorun output

SY4000 CAN control via Waveshare USB-CAN-A (variable-length serial protocol).

Wire protocol (serial -> CAN), extended frames:
    AA [TYPE] [ID0 ID1 ID2 ID3] [DATA...] 55
    TYPE = 0xC0 | 0x20(extended) | 0x10(RTR, if remote frame) | DLC
    ID bytes are little-endian (LSB first) of the 29-bit extended ID
"""

import serial
import time
from registers import describe_write
# from readtest import *


from user import get_int, get_float, ratediv, ndiv, freq, tperiod
# from user_calculation import read_osc_clk

from readv1 import read_status, read_config, read_live, read_mux_delay, read_run_status, fmt_freq, dump_delay_regs, read_logic_out

PORT = "COM11"          # change to your adapter's port, e.g. "/dev/ttyUSB0" on Linux
BAUDRATE = 2000000      # adapter's serial baud (check your adapter config, common default)
TIMEOUT = 0.5


def build_frame(can_id: int, data: bytes, extended: bool = True, rtr: bool = False) -> bytes:
    """Build a Waveshare USB-CAN-A variable-length serial packet for one CAN frame."""
    dlc = len(data)
    type_byte = 0xC0
    if extended:
        type_byte |= 0x20
    if rtr:
        type_byte |= 0x10
    type_byte |= dlc

    id_bytes = can_id.to_bytes(4, byteorder="little")

    packet = bytes([0xAA, type_byte]) + id_bytes + data + bytes([0x55])
    return packet


def send_frame(ser: serial.Serial, can_id: int, data: bytes):
    pkt = build_frame(can_id, data)
    print(f"TX  ID=0x{can_id:08X}  DLC={len(data)}  Data={data.hex(' ')}   raw={pkt.hex(' ')}")
    ser.write(pkt)


def send_remote_frame(ser: serial.Serial, can_id: int, dlc: int = 0):
    """
    Send a CAN remote frame (RTR=1) -- used to request a register's current
    value. Remote frames carry no data payload, only DLC (usually 0).
    Per DocCanNet 'Trigger read register value request' (protocol doc p.6):
        Code = cREQ (0x10)             -> plain read
        Code = cNS + cREQ (0x50)       -> read AND subscribe to updates
        DLC = 0, Data = none
    """
    pkt = build_frame(can_id, data=b"", extended=True, rtr=True)
    # pad dlc bytes manually since build_frame derives DLC from len(data)==0;
    # remote frames with DLC>0 (rare, usually 0) need the type byte's DLC bits set
    if dlc:
        type_byte = 0xC0 | 0x20 | 0x10 | dlc
        id_bytes = can_id.to_bytes(4, byteorder="little")
        pkt = bytes([0xAA, type_byte]) + id_bytes + bytes([0x55])
    # print(f"TX(RTR)  ID=0x{can_id:08X}  DLC={dlc}   raw={pkt.hex(' ')}")
    ser.write(pkt)


def read_echo(ser: serial.Serial, timeout=0.3):
    """Read back whatever the device sends (module's confirmation echo)."""
    time.sleep(timeout)
    if ser.in_waiting:
        resp = ser.read(ser.in_waiting)
        # print(f"RX  raw={resp.hex(' ')}")
        return resp
    return None


# ---------------------------------------------------------------------------
# SY4000 register writes: DocCanNet frame = Priority<<27 | Dest<<21 | Code<<14
#                                          | Source<<8 | RegID
# Code = 0x38 = cWR + cNV + cREQ  (write, nonvolatile, request confirm)
# Dest = 0x20 (device ID)  Source = 0x3F (PC)
# ---------------------------------------------------------------------------

DEST = 0x20
SOURCE = 0x3F
CODE_WR_NV_REQ = 0x38
CODE_WR_REQ= 0x18

CODE_REQ = 0x10          # cREQ only -- plain read request
CODE_REQ_SUBSCRIBE = 0x50  # cNS + cREQ -- read once, then module auto-reports updates


def make_id_NV(reg_id: int, priority=3, dest=DEST, code=CODE_WR_NV_REQ, source=SOURCE) -> int:
    return (priority << 27) | (dest << 21) | (code << 14) | (source << 8) | reg_id

def make_id(reg_id: int, priority=3, dest=DEST, code=CODE_WR_REQ, source=SOURCE) -> int:
    return (priority << 27) | (dest << 21) | (code << 14) | (source << 8) | reg_id

def read_register(ser: serial.Serial, reg_id: int, subscribe: bool = False, wait=0.3):
    """
    Send a remote (RTR) frame to request a register's current value.
    subscribe=True also turns on periodic auto-report for that register
    (per protocol: only read-only/report-capable registers support this).
    """
    code = CODE_REQ_SUBSCRIBE if subscribe else CODE_REQ
    can_id = make_id(reg_id, code=code)
    send_remote_frame(ser, can_id, dlc=0)
    return read_echo(ser, timeout=wait)


# def read_osc_clk(ser: serial.Serial) -> float:
#     """
#     Read the Oscillator clock frequency currently used by the device.
#     Register 0x11 (u8) returns the value already in MHz.
#     """
#     data = read_register(ser, reg_id=0x11, subscribe=False, wait=0.3)

#     if data is None or len(data) < 1:
#         raise RuntimeError("Failed to read OscClock (Reg 0x11)")

#     osc_mhz = data[0]          # already in MHz
#     print(f"Device OscClock = {osc_mhz} MHz")
#     return float(osc_mhz)


# def read_osc_clk(ser: serial.Serial) -> float:
#     """
#     Read OscClock (Reg 0x11) from the SY4000.
#     Works with Waveshare USB-CAN-A variable-length protocol.
#     Returns frequency in MHz.
#     """
#     raw = read_register(ser, reg_id=0x11, subscribe=False, wait=0.5)

#     if not raw:
#         raise RuntimeError("No data received from device")

#     # Search for the frame that answers register 0x11
#     # Pattern: AA E1 11 .... 64 55   (or any DLC=1 frame for reg 0x11)
#     i = 0
#     while i < len(raw) - 6:
#         if (raw[i] == 0xAA and
#             raw[i+1] == 0xE1 and          # extended + data + DLC=1
#             raw[i+2] == 0x11):            # RegID = 0x11

#             # Find the end marker 0x55
#             end = raw.find(b'\x55', i + 3)
#             if end != -1:
#                 data_byte = raw[end - 1]  # byte just before 0x55
#                 osc_mhz = data_byte
#                 print(f"Device OscClock = {osc_mhz} MHz")
#                 return float(osc_mhz)
#         i += 1

#     raise RuntimeError("OscClock (Reg 0x11) frame not found in the reply")


# def get_current_rate_clock_freq(ser: serial.Serial) -> dict:
#     """
#     Detects the current clock configuration and returns the relevant frequencies.

#     Special case – External dual-in:
#         Reg 0x75 == 0x01  (Optical clock mux = External)
#         Reg 0x55 == 0x03  (MuxRateClk      = SYNCIN)
#         → read BOTH 0x76 (OscInF) and 0x77 (SYNCINF)

#     Returns a dictionary with all useful information.
#     """
#     # ----------------------------------------------------------
#     # Helper to read a single-byte register
#     # ----------------------------------------------------------
#     def read_u8(reg_id: int) -> int:
#         raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
#         i = 0
#         while i < len(raw) - 5:
#             if (raw[i] == 0xAA and
#                 raw[i+1] in (0xE1, 0xC1) and   # DLC = 1
#                 raw[i+2] == reg_id):
#                 end = raw.find(b'\x55', i + 3)
#                 if end != -1:
#                     return raw[end - 1]
#             i += 1
#         raise RuntimeError(f"Could not read register 0x{reg_id:02X}")

#     # ----------------------------------------------------------
#     # 1. Read the two control registers
#     # ----------------------------------------------------------
#     osc_clk_mux = read_u8(0x75)   # Optical clock mux
#     rate_clk    = read_u8(0x55)   # MuxRateClk

#     print(f"Optical clock mux (0x75) = 0x{osc_clk_mux:02X}")
#     print(f"MuxRateClk        (0x55) = 0x{rate_clk:02X}")

#     result = {
#         "osc_clk_mux": osc_clk_mux,
#         "rate_clk": rate_clk,
#         "mode": None,
#         "freq_hz": None,          # main frequency for Ratediv calculation
#         "osc_inf_hz": None,       # 0x76
#         "sync_inf_hz": None,      # 0x77
#     }

#     # ----------------------------------------------------------
#     # 2. Decide the mode
#     # ----------------------------------------------------------
#     if osc_clk_mux == 0x01 and rate_clk == 0x03:
#         # ===== External dual-in =====
#         result["mode"] = "External dual-in"
#         print("→ Mode: External dual-in  (reading both 0x76 and 0x77)")

#         osc_inf  = _read_u32_freq(ser, 0x76)   # CLK IN frequency
#         sync_inf = _read_u32_freq(ser, 0x77)   # SYNC IN frequency

#         result["osc_inf_hz"]  = osc_inf
#         result["sync_inf_hz"] = sync_inf
#         result["freq_hz"]     = sync_inf       # SYNCIN is the rate source

#     elif rate_clk == 0x00:
#         result["mode"] = "Internal"
#         osc_mhz = read_osc_clk(ser)
#         result["freq_hz"] = osc_mhz * 1e6

#     elif rate_clk == 0x01:
#         result["mode"] = "OPTCLK"
#         result["osc_inf_hz"] = _read_u32_freq(ser, 0x76)
#         result["freq_hz"] = result["osc_inf_hz"]

#     elif rate_clk == 0x02:
#         result["mode"] = "OPTCLK/2"
#         result["osc_inf_hz"] = _read_u32_freq(ser, 0x76)
#         result["freq_hz"] = result["osc_inf_hz"] / 2.0

#     elif rate_clk == 0x03:
#         result["mode"] = "SYNCIN"
#         result["sync_inf_hz"] = _read_u32_freq(ser, 0x77)
#         result["freq_hz"] = result["sync_inf_hz"]

#     else:
#         raise RuntimeError(f"Unknown combination: 0x75={osc_clk_mux}, 0x55={rate_clk}")

#     return result


# def _read_u32_freq(ser: serial.Serial, reg_id: int) -> float:
#     """Read u32 frequency register and return Hz (device stores value ×100 as kHz)."""
#     raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
#     i = 0
#     while i < len(raw) - 8:
#         if (raw[i] == 0xAA and
#             raw[i+1] in (0xE4, 0xC4) and   # DLC = 4
#             raw[i+2] == reg_id):
#             end = raw.find(b'\x55', i + 3)
#             if end != -1 and end >= i + 7:
#                 data = raw[end-4:end]
#                 value = int.from_bytes(data, 'little')
#                 freq_khz = value / 100.0
#                 print(f"  Reg 0x{reg_id:02X} = {freq_khz:.2f} kHz")
#                 return freq_khz * 1000.0
#         i += 1
#     raise RuntimeError(f"Could not read frequency register 0x{reg_id:02X}")



# def get_current_rate_clock_freq(ser: serial.Serial) -> dict:
#     """
#     Detects the current Sync / Trigger mode of the SY4000
#     and returns the frequencies needed for Ratediv calculation.
#     """
#     def read_u8(reg_id: int) -> int:
#         raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
#         i = 0
#         while i < len(raw) - 5:
#             if (raw[i] == 0xAA and raw[i+1] in (0xE1, 0xC1) and raw[i+2] == reg_id):
#                 end = raw.find(b'\x55', i + 3)
#                 if end != -1:
#                     return raw[end - 1]
#             i += 1
#         raise RuntimeError(f"Could not read register 0x{reg_id:02X}")

#     # ---- read the three key registers ----
#     osc_clk_mux = read_u8(0x75)   # Optical clock mux
#     rate_clk    = read_u8(0x55)   # MuxRateClk
#     start_trg   = read_u8(0x54)   # MuxStartTrg

#     print(f"0x75 Optical clock mux = {osc_clk_mux}")
#     print(f"0x55 MuxRateClk        = {rate_clk}")
#     print(f"0x54 MuxStartTrg       = {start_trg}")

#     result = {
#         "osc_clk_mux": osc_clk_mux,
#         "rate_clk": rate_clk,
#         "start_trg": start_trg,
#         "mode": None,
#         "freq_hz": None,
#         "osc_inf_hz": None,
#         "sync_inf_hz": None,
#     }

#     # ------------------------------------------------------------------
#     # Mode detection according to official description + register map
#     # ------------------------------------------------------------------
#     if start_trg in (4, 5):
#         result["mode"] = "One shot trigger" if start_trg == 4 else "One shot smart"
#         # still give a usable clock
#         result["freq_hz"] = read_osc_clk(ser) * 1e6

#     elif osc_clk_mux == 0 and rate_clk == 0:
#         result["mode"] = "Internal"
#         result["freq_hz"] = read_osc_clk(ser) * 1e6

#     elif osc_clk_mux == 1 and rate_clk == 1:
#         result["mode"] = "External SINGLE IN – CLK IN"
#         result["osc_inf_hz"] = _read_u32_freq(ser, 0x76)
#         result["freq_hz"] = result["osc_inf_hz"]

#     elif rate_clk == 3 and osc_clk_mux != 1:
#         result["mode"] = "External SINGLE IN – SYNC IN"
#         result["sync_inf_hz"] = _read_u32_freq(ser, 0x77)
#         result["freq_hz"] = result["sync_inf_hz"]

#     elif osc_clk_mux == 1 and rate_clk == 3:
#         # ===== External DUAL IN =====
#         result["mode"] = "External DUAL IN"
#         print("→ External DUAL IN – reading both CLK IN (0x76) and SYNC IN (0x77)")
#         result["osc_inf_hz"]  = _read_u32_freq(ser, 0x76)
#         result["sync_inf_hz"] = _read_u32_freq(ser, 0x77)
#         result["freq_hz"]     = result["sync_inf_hz"]   # rate divider is driven by SYNC IN

#     else:
#         result["mode"] = f"Unknown combination (0x75={osc_clk_mux}, 0x55={rate_clk}, 0x54={start_trg})"
#         # fallback
#         if rate_clk == 0:
#             result["freq_hz"] = read_osc_clk(ser) * 1e6
#         elif rate_clk in (1, 2):
#             result["osc_inf_hz"] = _read_u32_freq(ser, 0x76)
#             result["freq_hz"] = result["osc_inf_hz"] / (2 if rate_clk == 2 else 1)
#         elif rate_clk == 3:
#             result["sync_inf_hz"] = _read_u32_freq(ser, 0x77)
#             result["freq_hz"] = result["sync_inf_hz"]

#     return result


# def _read_u32_freq(ser: serial.Serial, reg_id: int) -> float:
#     """Read u32 frequency register → Hz (device stores value × 100 as kHz)."""
#     raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
#     i = 0
#     while i < len(raw) - 8:
#         if (raw[i] == 0xAA and raw[i+1] in (0xE4, 0xC4) and raw[i+2] == reg_id):
#             end = raw.find(b'\x55', i + 3)
#             if end != -1 and end >= i + 7:
#                 value = int.from_bytes(raw[end-4:end], 'little')
#                 freq_khz = value / 100.0
#                 print(f"  Reg 0x{reg_id:02X} = {freq_khz:.2f} kHz")
#                 return freq_khz * 1000.0
#         i += 1
#     raise RuntimeError(f"Could not read frequency register 0x{reg_id:02X}")


# def read_output_frequency(ser: serial.Serial) -> dict:
#     """
#     Reads the current output frequency / period of the rate generator
#     (the value shown when the user presses the Freq button).

#     Returns
#     -------
#     dict
#         {
#             "mode"          : str,
#             "rate_clock_hz" : float,   # frequency that clocks the rate divider
#             "ratediv"       : int,     # register 0x20
#             "freq_hz"       : float,   # actual output frequency
#             "period_s"      : float,   # actual output period in seconds
#         }
#     """
#     # 1. Get the current rate-clock frequency and mode
#     info = get_current_rate_clock_freq(ser)
#     rate_clock_hz = info["freq_hz"]

#     if rate_clock_hz is None or rate_clock_hz <= 0:
#         raise RuntimeError("Could not determine rate-clock frequency")

#     # 2. Read Ratediv (register 0x20) – u32
#     ratediv = _read_u32(ser, 0x20)

#     if ratediv < 1:
#         ratediv = 1          # safety

#     # 3. Calculate output frequency and period
#     out_freq_hz = rate_clock_hz / ratediv
#     out_period_s = 1.0 / out_freq_hz

#     result = {
#         "mode":          info["mode"],
#         "rate_clock_hz": rate_clock_hz,
#         "ratediv":       ratediv,
#         "freq_hz":       out_freq_hz,
#         "period_s":      out_period_s,
#     }

#     # Nice print-out
#     print("\n=== Output Frequency (Freq button) ===")
#     print(f"Mode            : {result['mode']}")
#     print(f"Rate-clock      : {result['rate_clock_hz']:,.3f} Hz")
#     print(f"Ratediv (0x20)  : {result['ratediv']}")
#     print(f"Output Frequency: {result['freq_hz']:,.6f} Hz")
#     print(f"Output Period   : {result['period_s']*1e9:,.3f} ns "
#           f"({result['period_s']*1e6:,.3f} µs)")
#     print("=" * 40)

#     return result


# def _read_u32(ser: serial.Serial, reg_id: int) -> int:
#     """Read a plain u32 register (little-endian)."""
#     raw = read_register(ser, reg_id=reg_id, subscribe=False, wait=0.4)
#     i = 0
#     while i < len(raw) - 8:
#         if (raw[i] == 0xAA and
#             raw[i+1] in (0xE4, 0xC4) and          # DLC = 4
#             raw[i+2] == reg_id):
#             end = raw.find(b'\x55', i + 3)
#             if end != -1 and end >= i + 7:
#                 data = raw[end-4:end]
#                 return int.from_bytes(data, 'little')
#         i += 1
#     raise RuntimeError(f"Could not read u32 register 0x{reg_id:02X}")

"""
user input
"""

# ratediv = get_int(f"Enter ratediv")
# ndiv = get_int(f"Enter ndiv")
# freq = get_int(f"Enter output freq")
# tperiod = get_float(f"Enter tperiod")


# Example: "External Single In -> SYNC IN -> 10MHz" sequence
INTERNAL_100MHz_SEQUENCE = [
    (0x10, bytes([0x00])),                          # Command = OFF
    (0x75, bytes([0x00])),                          # OscClkMux = Internal 100MHz
    (0x11, bytes([0x64])),                          # OscClock = 100
    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30
    (0x6D, bytes([0x01])),                          # VCO2 freq = 3GHz
    (0x55, bytes([0x00])),                          # MuxRateClk = internal
    (0x54, bytes([0x00])),                          # MuxStartTrg = Rate divider
    (0x20, (1000).to_bytes(4, "little")),             # Ratediv = 1000
    # (0x10, bytes([0x01])),                          # Command = ON
]
EXTERNALSINGLEIN_CLKIN_100MHz_SEQUENCE = [
    (0x10, bytes([0x00])),                          # Command = OFF
    (0x75, bytes([0x01])),                          # OscClkMux = exterenal
    (0x11, bytes([0x64])),                          # OscClock = 100--->change clk
    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30
    (0x6D, bytes([0x01])),                          # VCO2 freq = 3GHz
    (0x55, bytes([0x01])),                          # MuxRateClk = external
    (0x54, bytes([0x01])),                          # MuxStartTrg = Rate divider@optclk
    (0x20, (100).to_bytes(4, "little")),             # Ratediv = 1000 -->set freq
    (0x76, None),
    (0x77, None),
    #(0x10, bytes([0x01])),                          # Command = ON
]
# befor run give the sync of desired value then only it work 
# freq given 5Mhz               freq = 5000000/10 = 5,00,000(500Khz)
# freq given 5Mhz               freq = 10000000/10 = 10,00,000()
# freq given 5Mhz               freq = 20000000/10 = 20,00,000()
EXTERNALSINGLEIN_SYNCIN_10MHZ_SEQUENCE = [
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
    (0x20, (100).to_bytes(4, "little")),             # Ratediv = 100
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
    (0x20, (1000).to_bytes(4, "little")),
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
]
CONFIG_FREQ_DIV_100_SEQUENCE = [
    (0x52, bytes([0x04])),                          # MuxConfSw = F div
    (0x69, (100).to_bytes(4, "little")),
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
DELAY_PRESET_DEL = [                                #to change delay preset del0
    #DEL0
    (0x80, (5).to_bytes(4, "little")),               #DELCNT0
    (0x5D, bytes([0x04])),                           #Ddelay0
    (0x56, bytes([0x01])),                           #Adelay0
    #DEL1
    (0x16, (22).to_bytes(4, "little")),               #DELCNT1
    (0x5E, bytes([0x04])),                           #Ddelay1
    (0x57, bytes([0x01])),                           #Adelay1
    #DEL2
    # (0x19, (22).to_bytes(4, "little")),               #DELCNT2
    # (0x5F, bytes([0x04])),                           #Ddelay2
    # (0x58, bytes([0x01])),                           #Adelay2
    # #DEL3
    # (0x1A, (3).to_bytes(4, "little")),               #DELCNT3
    # (0x60, bytes([0x04])),                           #Ddelay3
    # (0x59, bytes([0x01])),                           #Adelay3
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
RUN_ON = [
    (0x10, bytes([0x01])),
]
def run_check_out():
    run_sequence(ser , OUT0_CONFIG2_DEL0_DEL1)
    time.sleep(1.00)
    run_sequence(ser , OUT1_CONFIG2_DEL0_DEL1)
    time.sleep(1.00)
    run_sequence(ser , OUT2_CONFIG2_DEL0_DEL1)
    time.sleep(1.00)
    run_sequence(ser , OUT3_CONFIG2_DEL0_DEL1)
    time.sleep(1.00)
    run_sequence(ser , OUT4_CONFIG2_DEL0_DEL1)
    time.sleep(1.00)
    run_sequence(ser , OUT5_CONFIG2_DEL0_DEL1)
    time.sleep(1.00)
    run_sequence(ser , OUT6_CONFIG2_DEL0_DEL1)
    time.sleep(1.00)
    run_sequence(ser , OUT7_CONFIG2_DEL0_DEL1)
    time.sleep(1.00)
    run_sequence(ser , OUT_ANOUT_OUT7_CONFIG2_1V)
    time.sleep(1.00) 
    run_sequence(ser , OUT_COMT_OPTCLK)
    time.sleep(1.00)
    run_sequence(ser , OUT_PRET_OUT0)
    time.sleep(1.00)
       

def on_monitor_button_click():
    status = read_status(ser, show=False)
    config = read_config(ser, show=False)
    live   = read_live(ser, show=False)
    mux    = read_mux_delay(ser, show=False)
    run    = read_run_status(ser)
    return status, config, live, mux, run

def run_sequence(ser, sequence):
    for reg_id, data in sequence:
        if data is None:
            can_id = make_id(reg_id, code=CODE_REQ)
            send_remote_frame(ser, can_id, dlc=0)
        else:
            can_id = make_id(reg_id)
            send_frame(ser, can_id, data)
        read_echo(ser)
        time.sleep(0.05)
    print("\n")
    describewrite(sequence)
    print("\n")

def describewrite(sequence):
    for reg_id, data in sequence:
        print(describe_write(reg_id, data))

if __name__ == "__main__":
    with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
        print(f"Opened {PORT} at {BAUDRATE} baud")

        #  # quick test: only read, no writes
        # try:
        #     read_status(ser)
        # except Exception as e:
        #     print("Error:", e)
        

        try:
            status, config, live, mux, run = on_monitor_button_click()

            print("STATUS:", status)
            print("CONFIG:", config)
            print("LIVE  :", live)
            print("RUN   :", run)

            for b in sorted(mux):
                entry = mux[b]
                print(f"--- block {b} ---")
                print("  conf1:", entry["conf1"])
                print("  conf2:", entry["conf2"])
                if "logic_out" in entry:
                    print("  logic_out:", entry["logic_out"]["text"])
        finally:
            ser.close()

        # read_config(ser)
        # read_live(ser)

        # a = snap(ser)
        # for _ in range(5):
        #     read_live(ser)
        # b = snap(ser)
        # print("Config changed:", a != b)
        # print(a); print(b)


        # read_mux_delay(ser)
        # read_mux_delay(ser, blocks=range(8), show=True, fast=False)

        # # --- live monitor demo ---
        # mon = LiveMonitor(ser)
        # mon.start()

        # try:
        #     for _ in range(50):              # ~5 seconds, change as needed
        #         clk, sync = mon.get()
        #         print(f"\rCLK={fmt_freq(clk):<18} SYNC={fmt_freq(sync):<18}", end="")
        #         time.sleep(0.1)
        # except KeyboardInterrupt:
        #     pass
        # finally:
        #     mon.stop()

        # print()   # newline after \r loop


        # for ch in range(8):
        #     dump_delay_regs(ser, ch)
        #run_sequence(ser, INTERNAL_100MHz_SEQUENCE)
        #run_sequence(ser,EXTERNALSINGLEIN_CLKIN_100MHz_SEQUENCE)
        #run_sequence(ser,EXTERNALSINGLEIN_SYNCIN_10MHZ_SEQUENCE)


        # try:
        #     while True:
        #         read_live(ser)
        #         time.sleep(0.1)
        # except KeyboardInterrupt:
        #     pass

        time.sleep(1.00)
        #run_sequence(ser,FREQ_10KHZ)
        #run_sequence(ser,EXTERNALDUALIN_CLKIN_100MHZ_SYNCIN_20MHZ_SEQUENCE)
        #run_sequence(ser,ONESHOT_TRIGGER_SOFTWARETRIG)
       
        

        #run_sequence(ser, CONFIG_FREQ_DIV_100_SEQUENCE)

       

    
        
        #run_sequence(ser,ONESHOT_TRIGGER_SMARTTRIG)
        #run_sequence(ser,PRESET1_CHANNEL_SEQUENCE)
        # describewrite(EXTERNALSINGLEIN_CLKIN_100MHz_SEQUENCE)
        
        # run_sequence(ser, CONFIG_NORMAL_SEQUENCE)
        # run_sequence(ser, CONFIG_GATE_GATE_SEQUENCE)
        # run_sequence(ser,CONFIG_N_GATE_SEQUENCE)
        #run_sequence(ser, CONFIG_FREQ_DIV_100_SEQUENCE)
        #run_sequence(ser, DELAY_PRESET_DEL)
        # run_sequence(ser, POSTDELAY_PRESET_POSTDEL)
        #run_sequence(ser, OUT0_CONFIG2_DEL0_DEL1)
        #run_sequence(ser, OUT2_CONFIG2_DEL0_DEL1)
        #run_sequence(ser,RUN_ON)
        #run_check_out()
     
