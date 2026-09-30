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

from calculations import (
    resolve_vco_mode, system_clock_hz,
    calc_delay, validate_delay, min_delay_time_s, max_delay_time_s,
    calc_post_delay_checked, min_post_delay_s, max_post_delay_s,
    calc_rate_divider, calc_burst_mode, calc_freq_div_mode,
    calc_dac_config, calc_watchdog_period,
    parse_time, parse_freq,
)

PORT = "COM21"          # change to your adapter's port, e.g. "/dev/ttyUSB0" on Linux
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
    (0x20, (1000).to_bytes(4, "little")),             # Ratediv = 1000
    (0x10, bytes([0x01])),                          # Command = ON
]
"""
0x11 fsystem = n * oscclk
                30 * 100->3GHz
    
    Oscillator clock    (0x64)-->>>>0x11


    0x0A -> 10Mhz 
"""
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
RUN_ON = [
    (0x10, bytes([0x01])),
]
RUN_OFF = [
    (0x10, bytes([0x00])),
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
        #run_sequence(ser, INTERNAL_100MHz_SEQUENCE)
        #run_sequence(ser,EXTERNALSINGLEIN_CLKIN_100MHz_SEQUENCE)
        #run_sequence(ser,EXTERNALSINGLEIN_SYNCIN_SEQUENCE)
        time.sleep(1.00)
        run_sequence(ser,FREQ_10KHZ)
        #run_sequence(ser,EXTERNALDUALIN_CLKIN_100MHZ_SYNCIN_20MHZ_SEQUENCE)
        #run_sequence(ser,ONESHOT_TRIGGER_SOFTWARETRIG)
        #run_sequence(ser,ONESHOT_TRIGGER_SMARTTRIG)
        #run_sequence(ser,PRESET1_CHANNEL_SEQUENCE)
        # describewrite(EXTERNALSINGLEIN_CLKIN_100MHz_SEQUENCE)
        
        # run_sequence(ser, CONFIG_NORMAL_SEQUENCE)
        # run_sequence(ser, CONFIG_GATE_GATE_SEQUENCE)
        # run_sequence(ser,CONFIG_N_GATE_SEQUENCE)
        # run_sequence(ser, CONFIG_FREQ_DIV_100_SEQUENCE)
        #run_sequence(ser, DELAY_PRESET_DEL)
        # run_sequence(ser, POSTDELAY_PRESET_POSTDEL)
        #run_sequence(ser, OUT0_CONFIG2_DEL0_DEL1)
        #run_sequence(ser, OUT2_CONFIG2_DEL0_DEL1)
        #run_sequence(ser,RUN_ON)
        #run_check_out()
        #run_sequence(ser,RUN_OFF)
        # run_sequence(ser, CONFIG_BURST_GATE)
        # run_sequence(ser, CONFIG_BURST_NGATE)
        # run_sequence(ser, CONFIG_BURST_SOFTWARE)
        # run_sequence(ser, CONFIG_BURST_SYNCIN)


