"""
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



def make_id_nv(reg_id: int, priority=3, dest=DEST, code=CODE_WR_NV_REQ, source=SOURCE) -> int:
    return (priority << 27) | (dest << 21) | (code << 14) | (source << 8) | reg_id

def make_id(reg_id: int, priority=3, dest=DEST, code=CODE_WR_REQ, source=SOURCE) -> int:
    return (priority << 27) | (dest << 21) | (code << 14) | (source << 8) | reg_id


# Example: "External Single In -> SYNC IN -> 10MHz" sequence
SYNCIN_10MHZ_SEQUENCE = [
    (0x10, bytes([0x00])),                          # Command = OFF
    (0x75, bytes([0x00])),                          # OscClkMux = Internal 100MHz
    (0x11, bytes([0x64])),                          # OscClock = 100
    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30
    (0x6D, bytes([0x01])),                          # VCO2 freq = 3GHz
    (0x55, bytes([0x03])),                          # MuxRateClk = SYNCIN
    (0x54, bytes([0x00])),                          # MuxStartTrg = Rate divider
    (0x20, (100).to_bytes(4, "little")),             # Ratediv = 100
    (0x10, bytes([0x01])),                          # Command = ON
]
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


def run_sequence(ser: serial.Serial, sequence):
    for reg_id, data in sequence:
        can_id = make_id(reg_id)
        send_frame(ser, can_id, data)
        read_echo(ser)
        time.sleep(0.05)   # small gap between frames, mirrors captured log timing

run_off=[
    (0x10, bytes([0x01]))
]
if __name__ == "__main__":
    with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
        print(f"Opened {PORT} at {BAUDRATE} baud")
       # run_sequence(ser, SYNCIN_10MHZ_SEQUENCE)
        #run_sequence(ser,INTERNAL_100MHz_SEQUENCE)
        #time.sleep(0.10)
        run_sequence(ser,run_off)
