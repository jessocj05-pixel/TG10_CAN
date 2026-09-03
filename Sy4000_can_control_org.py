"""
SY4000 CAN control via Waveshare USB-CAN-A (variable-length serial protocol).

Wire protocol (serial -> CAN), extended frames:
    AA [TYPE] [ID0 ID1 ID2 ID3] [DATA...] 55
    TYPE = 0xC0 | 0x20(extended) | 0x10(RTR, if remote frame) | DLC
    ID bytes are little-endian (LSB first) of the 29-bit extended ID
"""

import serial
import time
import sys

PORT = "COM22"          # change to your adapter's port, e.g. "/dev/ttyUSB0" on Linux
BAUDRATE = 2000000      # adapter's serial baud (check your adapter config, common default)
TIMEOUT = 0.5

#waveshare packet builder
# C8 = STANDARD + DATA + DLC 8
# C2 = STANDARD + DATA + DLC 2
# E8 = EXTENDD +  DATA + DLC 8
# E2 = EXTENDED + DATA + DLC 2
def build_frame(can_id: int, data: bytes, extended: bool = True, rtr: bool = False) -> bytes:           #it takes CAN id,CAN data ,Extendend/standard,data/remote frames and produces waveshare serial packet
    """Build a Waveshare USB-CAN-A variable-length serial packet for one CAN frame."""
    dlc = len(data)     #if data = 11 22 len(data) will give 2 ie. bytes
    type_byte = 0xC0          
    if extended:
        type_byte |= 0x20    # 0xC0 | 0x20 = E0 then DLC 8 E0|08 = E8 else C0 |08 = C8
    if rtr:
        type_byte |= 0x10
    type_byte |= dlc        #OR ING WITH DLC(THE ELSE PART)

    id_bytes = can_id.to_bytes(4, byteorder="little")      #SUPPOSE CAN ID :1C143F01 TO BYTES : 1C 14 3F 01 BYTEORDER (LITTLE) : 01 3F 14 1C bcoz waveshare extended frame uses little indian order

    packet = bytes([0xAA, type_byte]) + id_bytes + data + bytes([0x55])   #waveshare packet: AA + TYPE + CAN ID + DATA + 55
    return packet                                                           #PACKET WILL BE: AA E1 01 3F 14 1C 01 55     bcoz. E0 + DLC 1 = E1 


def send_frame(ser: serial.Serial, can_id: int, data: bytes):              #SER : serialy sending ,CANID,DATA
    pkt = build_frame(can_id, data)                                         #it builds
    print(f"TX  ID=0x{can_id:08X}  DLC={len(data)}  Data={data.hex(' ')}   raw={pkt.hex(' ')}")
    ser.write(pkt)                                                         # helps to see tx data (pkt->python memory->pyserial->com22->usb->usb can a)


def read_response(ser: serial.Serial, timeout=0.3):                                             
    """Read back whatever the device sends (module's confirmation echo)."""
    time.sleep(timeout)
    if ser.in_waiting:                                                     #ask hw many bytes are currently waitng in serial receive buffer if there are bytes reads the and print them
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

def make_id(reg_id: int, priority=3, dest=DEST, code=CODE_WR_REQ, source=SOURCE) -> int:                # builidng sy4000 can id
    return (priority << 27) | (dest << 21) | (code << 14) | (source << 8) | reg_id                      # bit field packing operation


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
    (0x12, (30).to_bytes(4, "little")),              # Ndiv = 30                                        #id:0x12 data :1e 00 00 00
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
        read_response(ser)
        time.sleep(0.05)   # small gap between frames, mirrors captured log timing

run_off=[
    (0x10, bytes([0x00]))
]
if __name__ == "__main__":
    with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
        print(f"Opened {PORT} at {BAUDRATE} baud")
       # run_sequence(ser, SYNCIN_10MHZ_SEQUENCE)
        run_sequence(ser,INTERNAL_100MHz_SEQUENCE)
        time.sleep(0.10)
        run_sequence(ser,run_off)
