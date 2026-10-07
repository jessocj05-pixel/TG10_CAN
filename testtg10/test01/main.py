"""
main.py – full hardware control for SY4000 / TG10
Combines:
  - Waveshare USB-CAN-A protocol
  - Automatic sending of every sequence produced by menu.py
"""

import serial
import time
import menu02_ as menu_mod          # the file you pasted (menu.py)

# ────────────────────────────────────────────────
# Serial settings
# ────────────────────────────────────────────────
PORT     = "COM21"               # ← change to your port
BAUDRATE = 2000000
TIMEOUT  = 0.5


# ────────────────────────────────────────────────
# Protocol helpers (exactly as you provided)
# ────────────────────────────────────────────────
def build_frame(can_id: int, data: bytes, extended: bool = True, rtr: bool = False) -> bytes:
    dlc = len(data)
    type_byte = 0xC0
    if extended:
        type_byte |= 0x20
    if rtr:
        type_byte |= 0x10
    type_byte |= dlc
    id_bytes = can_id.to_bytes(4, byteorder="little")
    return bytes([0xAA, type_byte]) + id_bytes + data + bytes([0x55])


def send_frame(ser: serial.Serial, can_id: int, data: bytes):
    pkt = build_frame(can_id, data)
    # print(f"TX  ID=0x{can_id:08X}  DLC={len(data)}  Data={data.hex(' ')}   raw={pkt.hex(' ')}")
    ser.write(pkt)


def send_remote_frame(ser: serial.Serial, can_id: int, dlc: int = 0):
    pkt = build_frame(can_id, data=b"", extended=True, rtr=True)
    if dlc:
        type_byte = 0xC0 | 0x20 | 0x10 | dlc
        id_bytes = can_id.to_bytes(4, byteorder="little")
        pkt = bytes([0xAA, type_byte]) + id_bytes + bytes([0x55])
    # print(f"TX(RTR)  ID=0x{can_id:08X}  DLC={dlc}   raw={pkt.hex(' ')}")
    ser.write(pkt)


def read_response(ser: serial.Serial, timeout=0.3):
    time.sleep(timeout)
    if ser.in_waiting:
        resp = ser.read(ser.in_waiting)
        # print(f"RX  raw={resp.hex(' ')}")
        return resp
    return None


# ────────────────────────────────────────────────
# SY4000 ID helpers
# ────────────────────────────────────────────────
DEST = 0x20
SOURCE = 0x3F
CODE_WR_NV_REQ = 0x38
CODE_WR_REQ    = 0x18
CODE_REQ       = 0x10
CODE_REQ_SUBSCRIBE = 0x50


def make_id_NV(reg_id: int, priority=3, dest=DEST, code=CODE_WR_NV_REQ, source=SOURCE) -> int:
    return (priority << 27) | (dest << 21) | (code << 14) | (source << 8) | reg_id


def make_id(reg_id: int, priority=3, dest=DEST, code=CODE_WR_REQ, source=SOURCE) -> int:
    return (priority << 27) | (dest << 21) | (code << 14) | (source << 8) | reg_id


def read_register(ser: serial.Serial, reg_id: int, subscribe: bool = False, wait=0.3):
    code = CODE_REQ_SUBSCRIBE if subscribe else CODE_REQ
    can_id = make_id(reg_id, code=code)
    send_remote_frame(ser, can_id, dlc=0)
    return read_response(ser, timeout=wait)


def write_register(ser: serial.Serial, reg_id: int, data: bytes, nonvolatile: bool = False):
    can_id = make_id_NV(reg_id) if nonvolatile else make_id(reg_id)
    send_frame(ser, can_id, data)
    return read_response(ser)


# ────────────────────────────────────────────────
# Send a whole sequence produced by the menu
# ────────────────────────────────────────────────
def send_sequence(ser, seq, label="sequence"):
    """Take the list of (reg, data) that menu.py builds and write them to hardware."""
    print(f"\n>>> SENDING TO HARDWARE: {label} ({len(seq)} writes)")
    for reg, data in seq:
        if data is None:
            # Skip READ / RTR requests – only write to the device
            print(f"  (skipped READ  reg=0x{reg:02X})")
            continue
        write_register(ser, reg, data)
    print(">>> SEND COMPLETE\n")


# ────────────────────────────────────────────────
# Hook into menu.py so every sequence is auto-sent
# ────────────────────────────────────────────────
_original_print_sequence = menu_mod.print_sequence

def _print_and_send(seq, label: str = "sequence"):
    """Replacement for menu.print_sequence – prints AND sends to hardware."""
    _original_print_sequence(seq, label)          # keep the nice offline print
    send_sequence(ser, seq, label)                # actually write to the device

# Install the hook
menu_mod.print_sequence = _print_and_send

# ────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────
def main():
    global ser
    ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)
    print(f"Opened {PORT} @ {BAUDRATE}")
    print("Every sequence built by the menu will be sent to the hardware automatically.\n")

    try:
        # Start the original menu
        # menu_mod.main()
                # Give the menu access to the open serial port
        menu_mod.menu_monitor.ser = ser

        # Start the menu
        menu_mod.main()
    finally:
        ser.close()
        print("Port closed.")


if __name__ == "__main__":
    main()