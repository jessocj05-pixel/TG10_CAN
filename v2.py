"""
witth remote frame

SY4000 CAN control via Waveshare USB-CAN-A (variable-length serial protocol).

Wire protocol (serial -> CAN), extended frames:
    AA [TYPE] [ID0 ID1 ID2 ID3] [DATA...] 55
    TYPE = 0xC0 | 0x20(extended) | 0x10(RTR, if remote frame) | DLC
    ID bytes are little-endian (LSB first) of the 29-bit extended ID
"""

import serial
import time

PORT = "COM22"          # change to your adapter's port, e.g. "/dev/ttyUSB0" on Linux
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
    print(f"TX(RTR)  ID=0x{can_id:08X}  DLC={dlc}   raw={pkt.hex(' ')}")
    ser.write(pkt)


def read_echo(ser: serial.Serial, timeout=0.3):
    """Read back whatever the device sends (module's confirmation echo)."""
    time.sleep(timeout)
    if ser.in_waiting:
        resp = ser.read(ser.in_waiting)
        print(f"RX  raw={resp.hex(' ')}")
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


# Example: "External Single In -> SYNC IN -> 10MHz" sequence
INTERNAL_100MHz_SEQUENCE = [
    (0x10, bytes([0x00])),                          # Command = OFF
    (0x75, bytes([0x00])),                          # OscClkMux = Internal 100MHz
    (0x11, bytes([0x64])),                          # OscClock = 100
    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30
    (0x6D, bytes([0x01])),                          # VCO2 freq = 3GHz
    (0x55, bytes([0x00])),                          # MuxRateClk = internal
    (0x54, bytes([0x00])),                          # MuxStartTrg = Rate divider
    (0x20, (5).to_bytes(4, "little")),             # Ratediv = 1000
    (0x10, bytes([0x01])),                          # Command = ON
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
EXTERNALSINGLEIN_SYNCIN_10MHZ_SEQUENCE = [
    (0x10, bytes([0x00])),                          # Command = OFF
    (0x75, bytes([0x00])),                          # OscClkMux = Internal 100MHz
    (0x11, bytes([0x64])),                          # OscClock = 100
    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30
    (0x6D, bytes([0x01])),                          # VCO2 freq = 3GHz
    (0x55, bytes([0x01])),                          # MuxRateClk = SYNCIN
    (0x54, bytes([0x01])),                          # MuxStartTrg = Rate divider
    (0x20, (100).to_bytes(4, "little")),             # Ratediv = 100
    #(0x10, bytes([0x01])),                          # Command = ON
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
    (0x75, bytes([0x00])),                          # OscClkMux = Internal 100MHz
    (0x11, bytes([0x64])),                          # OscClock = 100
    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30
    (0x6D, bytes([0x01])),                          # VCO2 freq = 3GHz
    (0x55, bytes([0x00])),                          # MuxRateClk = SYNCIN
    (0x54, bytes([0x05])),                          # MuxStartTrg = Rate divider
    (0x20, (200).to_bytes(4, "little")),             # Ratediv = 100
    #(0x10, bytes([0x01])),                          # Command = ON
]

FREQ_10KHZ = {
    (0x20, (10000).to_bytes(4, "little")),
}

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


if __name__ == "__main__":
    with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
        print(f"Opened {PORT} at {BAUDRATE} baud")
        #run_sequence(ser, INTERNAL_100MHz_SEQUENCE)
        #run_sequence(ser,EXTERNALSINGLEIN_CLKIN_100MHz_SEQUENCE)
        #run_sequence(ser,EXTERNALSINGLEIN_SYNCIN_10MHZ_SEQUENCE)
        time.sleep(1.00)
        #run_sequence(ser,FREQ_10KHZ)
        #run_sequence(ser,EXTERNALDUALIN_CLKIN_100MHZ_SYNCIN_20MHZ_SEQUENCE)
        run_sequence(ser,ONESHOT_TRIGGER_SOFTWARETRIG)
        #run_sequence(ser,ONESHOT_TRIGGER_SMARTTRIG)