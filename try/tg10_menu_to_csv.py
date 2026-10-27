#!/usr/bin/env python3
"""
tg10_menu_to_csv.py
--------------------
Pull the register "menu file" out of an EKSMA Optics TG10 timing generator
over CAN bus (via a Waveshare USB-CAN-A adapter) and write it to a CSV.

Protocol reference: EKSMA "DocCanNet" protocol (used by TG10 / SY4000 and
other EKSMA CAN modules) + Waveshare USB-CAN-A serial<->CAN framing.

Wiring: connect Waveshare USB-CAN-A CAN-H/CAN-L to the TG10 CAN bus
(back panel CAN connector). Bus speed is fixed at 1 Mbit/s.

Usage:
    python3 tg10_menu_to_csv.py --port /dev/ttyUSB0 --device-id 1 --out menu.csv
    python3 tg10_menu_to_csv.py --port COM5 --device-id 1 --register 4 --out errors.csv

Requires: pyserial   (pip install pyserial)
"""

import argparse
import sys
import time
from enum import IntEnum


# ---------------------------------------------------------------------------
# Waveshare USB-CAN-A: serial <-> CAN framing (variable-length protocol)
# ---------------------------------------------------------------------------

class CANUSB_SPEED(IntEnum):
    SPEED_1000000 = 0x01
    SPEED_800000 = 0x02
    SPEED_500000 = 0x03
    SPEED_400000 = 0x04
    SPEED_250000 = 0x05
    SPEED_200000 = 0x06
    SPEED_125000 = 0x07
    SPEED_100000 = 0x08
    SPEED_50000 = 0x09
    SPEED_20000 = 0x0A
    SPEED_10000 = 0x0B
    SPEED_5000 = 0x0C


class WaveshareUsbCanA:
    """Minimal driver for the Waveshare USB-CAN-A adapter.

    Uses the fixed 20-byte frame to configure the adapter (CAN speed /
    mode / frame type), then the variable-length frame format for actual
    traffic (AA <type> <id...> <data...> 55).
    """

    def __init__(self, port, serial_baud=2_000_000):
        import serial  # local import so the rest of the file can be
                        # inspected without pyserial installed
        # NOTE: plain defaults (8N1) confirmed working against real hardware.
        # An earlier version forced 2 stop bits, which broke UART framing
        # entirely (adapter received garbage, every request timed out).
        self._serial = serial.Serial(
            port,
            baudrate=serial_baud,
            timeout=0.1,
        )
        self._rxbuf = bytearray()

    def close(self):
        self._serial.close()

    @staticmethod
    def _checksum(data):
        return sum(data) & 0xFF

    def configure(self, can_speed=CANUSB_SPEED.SPEED_1000000, extended=True, mode=0x00):
        """Send the fixed 20-byte configuration frame to the adapter.

        TG10 / DocCanNet bus speed is fixed at 1 Mbit/s and uses CAN 2.0B
        (29-bit / extended) identifiers.
        """
        frame_type = 0x02 if extended else 0x01
        cmd = bytearray()
        cmd.append(0xAA)
        cmd.append(0x55)
        cmd.append(0x12)                 # TYPE = settings frame
        cmd.append(int(can_speed))       # CAN bus speed
        cmd.append(frame_type)           # 0x01 standard / 0x02 extended
        cmd.extend([0] * 8)              # filter ID + mask ID (unused)
        cmd.append(mode)                 # 0x00 = normal
        cmd.extend([0x01, 0, 0, 0, 0])   # reserved
        cmd.append(self._checksum(cmd[2:19]))
        self._serial.write(bytes(cmd))
        time.sleep(0.05)
        self._serial.reset_input_buffer()
        self._rxbuf.clear()

    def send(self, can_id, data=b"", rtr=False, extended=True):
        """Send one CAN frame (extended 29-bit ID by default)."""
        dlc = 0 if rtr else len(data)
        type_byte = 0xC0
        if extended:
            type_byte |= 0x20
        if rtr:
            type_byte |= 0x10
        type_byte |= (dlc & 0x0F)

        id_len = 4 if extended else 2
        id_bytes = can_id.to_bytes(id_len, "little")

        frame = bytearray([0xAA, type_byte]) + id_bytes
        if not rtr:
            frame += bytes(data)
        frame.append(0x55)
        self._serial.write(bytes(frame))

    def receive(self, timeout=1.0):
        """Read one CAN frame from the adapter. Returns dict or None on timeout.

        Reads in bulk (not byte-by-byte) into an internal buffer and parses
        frames out of it. Byte-by-byte reads were too slow under heavy bus
        traffic (many frames/sec) -- each pyserial .read() call has real
        per-call overhead on Windows, and reading one byte at a time couldn't
        keep up, causing lost frame sync even though the data was on the wire.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            frame = self._try_parse_buffer()
            if frame is not None:
                return frame
            n = self._serial.in_waiting
            chunk = self._serial.read(n if n > 0 else 64)
            if chunk:
                self._rxbuf.extend(chunk)
            else:
                time.sleep(0.001)
        return None

    def _try_parse_buffer(self):
        buf = self._rxbuf
        while True:
            idx = buf.find(b"\xAA")
            if idx == -1:
                buf.clear()
                return None
            if idx > 0:
                del buf[:idx]  # drop any garbage before the header byte

            if len(buf) < 2:
                return None  # need the type byte too, wait for more data

            type_byte = buf[1]
            extended = bool(type_byte & 0x20)
            rtr = bool(type_byte & 0x10)
            dlc = type_byte & 0x0F
            id_len = 4 if extended else 2
            data_len = 0 if rtr else dlc
            total_len = 2 + id_len + data_len + 1  # AA + type + id + data + 55

            if len(buf) < total_len:
                return None  # incomplete frame, wait for more bytes

            if buf[total_len - 1] != 0x55:
                # misaligned -- this 0xAA wasn't really a frame start.
                # Drop it and keep searching from the next byte.
                del buf[0:1]
                continue

            id_bytes = bytes(buf[2:2 + id_len])
            data_bytes = bytes(buf[2 + id_len:2 + id_len + data_len])
            can_id = int.from_bytes(id_bytes, "little")
            del buf[:total_len]
            return {"id": can_id, "extended": extended, "rtr": rtr, "data": data_bytes}


# ---------------------------------------------------------------------------
# EKSMA DocCanNet protocol (register / message addressing, per TG10 & SY4000
# CAN protocol description)
# ---------------------------------------------------------------------------

PC_ADDRESS = 0x3F          # PC / host default source ID
PRIORITY_DEFAULT = 0x3     # standard priority

# Code field bits (7-bit value, later shifted into the 29-bit CAN ID)
cNS = 0x40      # subscribe to register updates  (shared bit with cRESET)
cRESET = 0x40   # reset file transfer pointer    (shared bit with cNS)
cNV = 0x20      # make register value nonvolatile
cREQ = 0x10     # request (read/refresh) register value
cWR = 0x08      # write register value
cnF = 0x04      # do-not-forward (bridge only)

REG_MENU_FILE = 1
REG_ERROR_FILE = 4


def build_can_id(destination, code, source=PC_ADDRESS, reg_id=0, priority=PRIORITY_DEFAULT):
    """Pack DocCanNet address fields into a 29-bit CAN identifier."""
    return (
        ((priority & 0x3) << 27)
        | ((destination & 0x3F) << 21)
        | ((code & 0x7F) << 14)
        | ((source & 0x3F) << 8)
        | (reg_id & 0xFF)
    )


def parse_can_id(can_id):
    """Unpack a 29-bit DocCanNet CAN identifier into its address fields."""
    return {
        "priority": (can_id >> 27) & 0x3,
        "destination": (can_id >> 21) & 0x3F,
        "code": (can_id >> 14) & 0x7F,
        "source": (can_id >> 8) & 0x3F,
        "reg_id": can_id & 0xFF,
    }


def read_binary_register(can, device_id, reg_id, chunk_timeout=2.0, max_chunks=100_000):
    """Perform the DocCanNet binary file transfer handshake for a given
    register (menu file = reg 1, error file = reg 4) and return raw bytes.

    The bus is shared (up to 62 nodes per the protocol spec), so every
    reply is filtered on source/destination/reg_id before being accepted
    as part of our file transfer -- unrelated bus traffic is ignored
    rather than mistaken for file data.
    """
    data = bytearray()

    first = True
    chunks = 0
    while True:
        # cRESET+cREQ on the very first request (resets device's file
        # pointer), cREQ only on subsequent handshake/continue frames --
        # per protocol doc's 2019 update, cREQ is kept set on every
        # request for CAN-FD forward compatibility.
        code = cREQ | (cRESET if first else 0)
        can_id = build_can_id(destination=device_id, code=code, reg_id=reg_id)
        can.send(can_id, data=b"", rtr=True)
        first = False

        deadline = time.time() + chunk_timeout
        reply = None
        while time.time() < deadline:
            remaining = deadline - time.time()
            candidate = can.receive(timeout=remaining)
            if candidate is None:
                break
            if candidate["rtr"]:
                continue  # ignore remote frames (e.g. other hosts polling)
            fields = parse_can_id(candidate["id"])
            if (fields["source"] == device_id
                    and fields["destination"] == PC_ADDRESS
                    and fields["reg_id"] == reg_id):
                reply = candidate
                break
            # frame from unrelated bus traffic -- keep waiting

        if reply is None:
            raise TimeoutError(
                f"No response from device ID {device_id} while reading register {reg_id}. "
                "Check wiring, device address, and that the bus is terminated (120 ohm)."
            )

        chunk = reply["data"]
        data.extend(chunk)
        chunks += 1

        if len(chunk) < 8:
            break  # last chunk of the file
        if chunks > max_chunks:
            raise RuntimeError("Too many chunks received, aborting (possible protocol mismatch).")

    return bytes(data)


# ---------------------------------------------------------------------------
# Menu file binary parsing
# ---------------------------------------------------------------------------

REG_TYPE_NAMES = {
    0: "u8", 1: "s8", 2: "u16", 3: "s16", 4: "u32", 5: "s32",
    6: "float", 7: "string8", 8: "u64", 9: "s64", 10: "double",
}

# Field size (bytes) used for Low/High limit fields, per the protocol doc:
# "1 octet for 8-bit registers, 2 octets for 16-bit, 4 octets for 32-bit".
# Types beyond 32-bit (string8/u64/s64/double) aren't covered explicitly by
# the spec for limits; we fall back to 4 bytes as the most reasonable
# assumption (these types rarely carry meaningful Low/High limits).
LIMIT_SIZE = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4}


def crc16_ccitt(data, init=0xFFFF, poly=0x1021):
    crc = init
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def read_cstring(buf, offset):
    end = buf.index(0, offset)
    return buf[offset:end].decode("ascii", errors="replace"), end + 1


def parse_menu_file(raw):
    """Parse DocCanNet menu-file binary format into a list of dict records."""
    if len(raw) < 2:
        raise ValueError("File too short to contain header")

    checksum_lo, checksum_hi = raw[0], raw[1]
    stored_crc = checksum_lo | (checksum_hi << 8)
    body = raw[2:]
    computed_crc = crc16_ccitt(body)
    crc_ok = stored_crc == computed_crc

    records = []
    off = 0
    n = len(body)
    while off < n:
        reg_id = body[off]; off += 1
        tree_id = body[off]; off += 1
        reg_type = body[off]; off += 1
        permissions = body[off]; off += 1

        limit_size = LIMIT_SIZE.get(reg_type, 4)
        low_limit = int.from_bytes(body[off:off + limit_size], "little", signed=(reg_type % 2 == 1))
        off += limit_size
        high_limit = int.from_bytes(body[off:off + limit_size], "little", signed=(reg_type % 2 == 1))
        off += limit_size

        short_name, off = read_cstring(body, off)
        fmt, off = read_cstring(body, off)
        long_name, off = read_cstring(body, off)

        tree_node = (tree_id >> 4) & 0x0F
        tree_node_idx = tree_id & 0x0F

        nv = bool(permissions & 0x40)
        adv_mode = (permissions >> 4) & 0x03
        user_mode = (permissions >> 2) & 0x03
        svc_mode = permissions & 0x03

        records.append({
            "RegID": reg_id,
            "TreeID": tree_id,
            "TreeNode": tree_node,
            "TreeNodeIdx": tree_node_idx,
            "RegType": REG_TYPE_NAMES.get(reg_type, f"unknown({reg_type})"),
            "Permissions_raw": f"0x{permissions:02X}",
            "NV": nv,
            "AdvancedMode": adv_mode,
            "UserMode": user_mode,
            "ServiceMode": svc_mode,
            "LowLimit": low_limit,
            "HighLimit": high_limit,
            "ShortName": short_name,
            "Format": fmt,
            "LongName": long_name,
        })

    return records, crc_ok, stored_crc, computed_crc


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def write_csv(records, path):
    import csv
    fieldnames = [
        "RegID", "TreeID", "TreeNode", "TreeNodeIdx", "RegType",
        "Permissions_raw", "NV", "AdvancedMode", "UserMode", "ServiceMode",
        "LowLimit", "HighLimit", "ShortName", "Format", "LongName",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)


def write_xlsx(records, path):
    """Write the parsed menu-file records to a formatted .xlsx workbook."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    fieldnames = [
        "RegID", "TreeID", "TreeNode", "TreeNodeIdx", "RegType",
        "Permissions_raw", "NV", "AdvancedMode", "UserMode", "ServiceMode",
        "LowLimit", "HighLimit", "ShortName", "Format", "LongName",
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "TG10 Menu"

    header_font = Font(name="Arial", bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    body_font = Font(name="Arial")

    for col, name in enumerate(fieldnames, start=1):
        cell = ws.cell(row=1, column=col, value=name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for row_idx, rec in enumerate(records, start=2):
        for col_idx, name in enumerate(fieldnames, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=rec.get(name))
            cell.font = body_font

    # Auto-size columns based on content length (openpyxl has no native autofit)
    for col_idx, name in enumerate(fieldnames, start=1):
        max_len = len(str(name))
        for rec in records:
            val = rec.get(name)
            if val is not None:
                max_len = max(max_len, len(str(val)))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 60)

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    wb.save(path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Extract TG10 menu file to CSV over CAN (Waveshare USB-CAN-A)")
    ap.add_argument("--port", required=True, help="Serial port of the Waveshare USB-CAN-A, e.g. /dev/ttyUSB0 or COM5")
    ap.add_argument("--serial-baud", type=int, default=2_000_000, help="Adapter's USB serial baud rate (default 2000000)")
    ap.add_argument("--device-id", type=int, required=True, help="TG10 CAN device ID / address (1..62)")
    ap.add_argument("--register", type=int, default=REG_MENU_FILE, choices=[REG_MENU_FILE, REG_ERROR_FILE],
                     help="1 = menu file (default), 4 = error file")
    ap.add_argument("--out", required=True, help="Output CSV path")
    ap.add_argument("--xlsx-out", default=None, help="Optional: also save an Excel (.xlsx) version")
    ap.add_argument("--raw-out", default=None, help="Optional: also save the raw binary file to this path")
    ap.add_argument("--timeout", type=float, default=2.0, help="Per-chunk response timeout in seconds")
    ap.add_argument("--skip-configure", action="store_true",
                     help="Skip the adapter's 20-byte settings frame (use if adapter is already "
                          "configured, e.g. via the vendor's GUI tool, or if configure() causes issues)")
    args = ap.parse_args()

    print(f"Opening {args.port} @ {args.serial_baud} baud ...")
    can = WaveshareUsbCanA(args.port, serial_baud=args.serial_baud)
    try:
        if not args.skip_configure:
            print("Configuring adapter for 1 Mbit/s, extended (29-bit) CAN frames ...")
            can.configure(can_speed=CANUSB_SPEED.SPEED_1000000, extended=True, mode=0x00)
        else:
            print("Skipping adapter configure step (--skip-configure).")

        print(f"Requesting register {args.register} from device ID {args.device_id} ...")
        raw = read_binary_register(can, args.device_id, args.register, chunk_timeout=args.timeout)
        print(f"Received {len(raw)} bytes.")

        if args.raw_out:
            with open(args.raw_out, "wb") as f:
                f.write(raw)
            print(f"Raw binary saved to {args.raw_out}")

        records, crc_ok, stored_crc, computed_crc = parse_menu_file(raw)
        print(f"Parsed {len(records)} register records.")
        if not crc_ok:
            print(f"WARNING: CRC mismatch (stored=0x{stored_crc:04X}, computed=0x{computed_crc:04X}). "
                  "File may be corrupted or parsing offsets may have drifted.", file=sys.stderr)

        write_csv(records, args.out)
        print(f"CSV written to {args.out}")

        if args.xlsx_out:
            write_xlsx(records, args.xlsx_out)
            print(f"Excel file written to {args.xlsx_out}")

    finally:
        can.close()


if __name__ == "__main__":
    main()#!/usr/bin/env python3
"""
tg10_menu_to_csv.py
--------------------
Pull the register "menu file" out of an EKSMA Optics TG10 timing generator
over CAN bus (via a Waveshare USB-CAN-A adapter) and write it to a CSV.

Protocol reference: EKSMA "DocCanNet" protocol (used by TG10 / SY4000 and
other EKSMA CAN modules) + Waveshare USB-CAN-A serial<->CAN framing.

Wiring: connect Waveshare USB-CAN-A CAN-H/CAN-L to the TG10 CAN bus
(back panel CAN connector). Bus speed is fixed at 1 Mbit/s.

Usage:
    python3 tg10_menu_to_csv.py --port /dev/ttyUSB0 --device-id 1 --out menu.csv
    python3 tg10_menu_to_csv.py --port COM5 --device-id 1 --register 4 --out errors.csv

Requires: pyserial   (pip install pyserial)
"""

import argparse
import sys
import time
from enum import IntEnum


# ---------------------------------------------------------------------------
# Waveshare USB-CAN-A: serial <-> CAN framing (variable-length protocol)
# ---------------------------------------------------------------------------

class CANUSB_SPEED(IntEnum):
    SPEED_1000000 = 0x01
    SPEED_800000 = 0x02
    SPEED_500000 = 0x03
    SPEED_400000 = 0x04
    SPEED_250000 = 0x05
    SPEED_200000 = 0x06
    SPEED_125000 = 0x07
    SPEED_100000 = 0x08
    SPEED_50000 = 0x09
    SPEED_20000 = 0x0A
    SPEED_10000 = 0x0B
    SPEED_5000 = 0x0C


class WaveshareUsbCanA:
    """Minimal driver for the Waveshare USB-CAN-A adapter.

    Uses the fixed 20-byte frame to configure the adapter (CAN speed /
    mode / frame type), then the variable-length frame format for actual
    traffic (AA <type> <id...> <data...> 55).
    """

    def __init__(self, port, serial_baud=2_000_000):
        import serial  # local import so the rest of the file can be
                        # inspected without pyserial installed
        # NOTE: plain defaults (8N1) confirmed working against real hardware.
        # An earlier version forced 2 stop bits, which broke UART framing
        # entirely (adapter received garbage, every request timed out).
        self._serial = serial.Serial(
            port,
            baudrate=serial_baud,
            timeout=0.1,
        )
        self._rxbuf = bytearray()

    def close(self):
        self._serial.close()

    @staticmethod
    def _checksum(data):
        return sum(data) & 0xFF

    def configure(self, can_speed=CANUSB_SPEED.SPEED_1000000, extended=True, mode=0x00):
        """Send the fixed 20-byte configuration frame to the adapter.

        TG10 / DocCanNet bus speed is fixed at 1 Mbit/s and uses CAN 2.0B
        (29-bit / extended) identifiers.
        """
        frame_type = 0x02 if extended else 0x01
        cmd = bytearray()
        cmd.append(0xAA)
        cmd.append(0x55)
        cmd.append(0x12)                 # TYPE = settings frame
        cmd.append(int(can_speed))       # CAN bus speed
        cmd.append(frame_type)           # 0x01 standard / 0x02 extended
        cmd.extend([0] * 8)              # filter ID + mask ID (unused)
        cmd.append(mode)                 # 0x00 = normal
        cmd.extend([0x01, 0, 0, 0, 0])   # reserved
        cmd.append(self._checksum(cmd[2:19]))
        self._serial.write(bytes(cmd))
        time.sleep(0.05)
        self._serial.reset_input_buffer()
        self._rxbuf.clear()

    def send(self, can_id, data=b"", rtr=False, extended=True):
        """Send one CAN frame (extended 29-bit ID by default)."""
        dlc = 0 if rtr else len(data)
        type_byte = 0xC0
        if extended:
            type_byte |= 0x20
        if rtr:
            type_byte |= 0x10
        type_byte |= (dlc & 0x0F)

        id_len = 4 if extended else 2
        id_bytes = can_id.to_bytes(id_len, "little")

        frame = bytearray([0xAA, type_byte]) + id_bytes
        if not rtr:
            frame += bytes(data)
        frame.append(0x55)
        self._serial.write(bytes(frame))

    def receive(self, timeout=1.0):
        """Read one CAN frame from the adapter. Returns dict or None on timeout.

        Reads in bulk (not byte-by-byte) into an internal buffer and parses
        frames out of it. Byte-by-byte reads were too slow under heavy bus
        traffic (many frames/sec) -- each pyserial .read() call has real
        per-call overhead on Windows, and reading one byte at a time couldn't
        keep up, causing lost frame sync even though the data was on the wire.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            frame = self._try_parse_buffer()
            if frame is not None:
                return frame
            n = self._serial.in_waiting
            chunk = self._serial.read(n if n > 0 else 64)
            if chunk:
                self._rxbuf.extend(chunk)
            else:
                time.sleep(0.001)
        return None

    def _try_parse_buffer(self):
        buf = self._rxbuf
        while True:
            idx = buf.find(b"\xAA")
            if idx == -1:
                buf.clear()
                return None
            if idx > 0:
                del buf[:idx]  # drop any garbage before the header byte

            if len(buf) < 2:
                return None  # need the type byte too, wait for more data

            type_byte = buf[1]
            extended = bool(type_byte & 0x20)
            rtr = bool(type_byte & 0x10)
            dlc = type_byte & 0x0F
            id_len = 4 if extended else 2
            data_len = 0 if rtr else dlc
            total_len = 2 + id_len + data_len + 1  # AA + type + id + data + 55

            if len(buf) < total_len:
                return None  # incomplete frame, wait for more bytes

            if buf[total_len - 1] != 0x55:
                # misaligned -- this 0xAA wasn't really a frame start.
                # Drop it and keep searching from the next byte.
                del buf[0:1]
                continue

            id_bytes = bytes(buf[2:2 + id_len])
            data_bytes = bytes(buf[2 + id_len:2 + id_len + data_len])
            can_id = int.from_bytes(id_bytes, "little")
            del buf[:total_len]
            return {"id": can_id, "extended": extended, "rtr": rtr, "data": data_bytes}


# ---------------------------------------------------------------------------
# EKSMA DocCanNet protocol (register / message addressing, per TG10 & SY4000
# CAN protocol description)
# ---------------------------------------------------------------------------

PC_ADDRESS = 0x3F          # PC / host default source ID
PRIORITY_DEFAULT = 0x3     # standard priority

# Code field bits (7-bit value, later shifted into the 29-bit CAN ID)
cNS = 0x40      # subscribe to register updates  (shared bit with cRESET)
cRESET = 0x40   # reset file transfer pointer    (shared bit with cNS)
cNV = 0x20      # make register value nonvolatile
cREQ = 0x10     # request (read/refresh) register value
cWR = 0x08      # write register value
cnF = 0x04      # do-not-forward (bridge only)

REG_MENU_FILE = 1
REG_ERROR_FILE = 4


def build_can_id(destination, code, source=PC_ADDRESS, reg_id=0, priority=PRIORITY_DEFAULT):
    """Pack DocCanNet address fields into a 29-bit CAN identifier."""
    return (
        ((priority & 0x3) << 27)
        | ((destination & 0x3F) << 21)
        | ((code & 0x7F) << 14)
        | ((source & 0x3F) << 8)
        | (reg_id & 0xFF)
    )


def parse_can_id(can_id):
    """Unpack a 29-bit DocCanNet CAN identifier into its address fields."""
    return {
        "priority": (can_id >> 27) & 0x3,
        "destination": (can_id >> 21) & 0x3F,
        "code": (can_id >> 14) & 0x7F,
        "source": (can_id >> 8) & 0x3F,
        "reg_id": can_id & 0xFF,
    }


def read_binary_register(can, device_id, reg_id, chunk_timeout=2.0, max_chunks=100_000):
    """Perform the DocCanNet binary file transfer handshake for a given
    register (menu file = reg 1, error file = reg 4) and return raw bytes.

    The bus is shared (up to 62 nodes per the protocol spec), so every
    reply is filtered on source/destination/reg_id before being accepted
    as part of our file transfer -- unrelated bus traffic is ignored
    rather than mistaken for file data.
    """
    data = bytearray()

    first = True
    chunks = 0
    while True:
        # cRESET+cREQ on the very first request (resets device's file
        # pointer), cREQ only on subsequent handshake/continue frames --
        # per protocol doc's 2019 update, cREQ is kept set on every
        # request for CAN-FD forward compatibility.
        code = cREQ | (cRESET if first else 0)
        can_id = build_can_id(destination=device_id, code=code, reg_id=reg_id)
        can.send(can_id, data=b"", rtr=True)
        first = False

        deadline = time.time() + chunk_timeout
        reply = None
        while time.time() < deadline:
            remaining = deadline - time.time()
            candidate = can.receive(timeout=remaining)
            if candidate is None:
                break
            if candidate["rtr"]:
                continue  # ignore remote frames (e.g. other hosts polling)
            fields = parse_can_id(candidate["id"])
            if (fields["source"] == device_id
                    and fields["destination"] == PC_ADDRESS
                    and fields["reg_id"] == reg_id):
                reply = candidate
                break
            # frame from unrelated bus traffic -- keep waiting

        if reply is None:
            raise TimeoutError(
                f"No response from device ID {device_id} while reading register {reg_id}. "
                "Check wiring, device address, and that the bus is terminated (120 ohm)."
            )

        chunk = reply["data"]
        data.extend(chunk)
        chunks += 1

        if len(chunk) < 8:
            break  # last chunk of the file
        if chunks > max_chunks:
            raise RuntimeError("Too many chunks received, aborting (possible protocol mismatch).")

    return bytes(data)


# ---------------------------------------------------------------------------
# Menu file binary parsing
# ---------------------------------------------------------------------------

REG_TYPE_NAMES = {
    0: "u8", 1: "s8", 2: "u16", 3: "s16", 4: "u32", 5: "s32",
    6: "float", 7: "string8", 8: "u64", 9: "s64", 10: "double",
}

# Field size (bytes) used for Low/High limit fields, per the protocol doc:
# "1 octet for 8-bit registers, 2 octets for 16-bit, 4 octets for 32-bit".
# Types beyond 32-bit (string8/u64/s64/double) aren't covered explicitly by
# the spec for limits; we fall back to 4 bytes as the most reasonable
# assumption (these types rarely carry meaningful Low/High limits).
LIMIT_SIZE = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4}


def crc16_ccitt(data, init=0xFFFF, poly=0x1021):
    crc = init
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def read_cstring(buf, offset):
    end = buf.index(0, offset)
    return buf[offset:end].decode("ascii", errors="replace"), end + 1


def parse_menu_file(raw):
    """Parse DocCanNet menu-file binary format into a list of dict records."""
    if len(raw) < 2:
        raise ValueError("File too short to contain header")

    checksum_lo, checksum_hi = raw[0], raw[1]
    stored_crc = checksum_lo | (checksum_hi << 8)
    body = raw[2:]
    computed_crc = crc16_ccitt(body)
    crc_ok = stored_crc == computed_crc

    records = []
    off = 0
    n = len(body)
    while off < n:
        reg_id = body[off]; off += 1
        tree_id = body[off]; off += 1
        reg_type = body[off]; off += 1
        permissions = body[off]; off += 1

        limit_size = LIMIT_SIZE.get(reg_type, 4)
        low_limit = int.from_bytes(body[off:off + limit_size], "little", signed=(reg_type % 2 == 1))
        off += limit_size
        high_limit = int.from_bytes(body[off:off + limit_size], "little", signed=(reg_type % 2 == 1))
        off += limit_size

        short_name, off = read_cstring(body, off)
        fmt, off = read_cstring(body, off)
        long_name, off = read_cstring(body, off)

        tree_node = (tree_id >> 4) & 0x0F
        tree_node_idx = tree_id & 0x0F

        nv = bool(permissions & 0x40)
        adv_mode = (permissions >> 4) & 0x03
        user_mode = (permissions >> 2) & 0x03
        svc_mode = permissions & 0x03

        records.append({
            "RegID": reg_id,
            "TreeID": tree_id,
            "TreeNode": tree_node,
            "TreeNodeIdx": tree_node_idx,
            "RegType": REG_TYPE_NAMES.get(reg_type, f"unknown({reg_type})"),
            "Permissions_raw": f"0x{permissions:02X}",
            "NV": nv,
            "AdvancedMode": adv_mode,
            "UserMode": user_mode,
            "ServiceMode": svc_mode,
            "LowLimit": low_limit,
            "HighLimit": high_limit,
            "ShortName": short_name,
            "Format": fmt,
            "LongName": long_name,
        })

    return records, crc_ok, stored_crc, computed_crc


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def write_csv(records, path):
    import csv
    fieldnames = [
        "RegID", "TreeID", "TreeNode", "TreeNodeIdx", "RegType",
        "Permissions_raw", "NV", "AdvancedMode", "UserMode", "ServiceMode",
        "LowLimit", "HighLimit", "ShortName", "Format", "LongName",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)


def write_xlsx(records, path):
    """Write the parsed menu-file records to a formatted .xlsx workbook."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    fieldnames = [
        "RegID", "TreeID", "TreeNode", "TreeNodeIdx", "RegType",
        "Permissions_raw", "NV", "AdvancedMode", "UserMode", "ServiceMode",
        "LowLimit", "HighLimit", "ShortName", "Format", "LongName",
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "TG10 Menu"

    header_font = Font(name="Arial", bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    body_font = Font(name="Arial")

    for col, name in enumerate(fieldnames, start=1):
        cell = ws.cell(row=1, column=col, value=name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for row_idx, rec in enumerate(records, start=2):
        for col_idx, name in enumerate(fieldnames, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=rec.get(name))
            cell.font = body_font

    # Auto-size columns based on content length (openpyxl has no native autofit)
    for col_idx, name in enumerate(fieldnames, start=1):
        max_len = len(str(name))
        for rec in records:
            val = rec.get(name)
            if val is not None:
                max_len = max(max_len, len(str(val)))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 60)

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    wb.save(path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Extract TG10 menu file to CSV over CAN (Waveshare USB-CAN-A)")
    ap.add_argument("--port", required=True, help="Serial port of the Waveshare USB-CAN-A, e.g. /dev/ttyUSB0 or COM5")
    ap.add_argument("--serial-baud", type=int, default=2_000_000, help="Adapter's USB serial baud rate (default 2000000)")
    ap.add_argument("--device-id", type=int, required=True, help="TG10 CAN device ID / address (1..62)")
    ap.add_argument("--register", type=int, default=REG_MENU_FILE, choices=[REG_MENU_FILE, REG_ERROR_FILE],
                     help="1 = menu file (default), 4 = error file")
    ap.add_argument("--out", required=True, help="Output CSV path")
    ap.add_argument("--xlsx-out", default=None, help="Optional: also save an Excel (.xlsx) version")
    ap.add_argument("--raw-out", default=None, help="Optional: also save the raw binary file to this path")
    ap.add_argument("--timeout", type=float, default=2.0, help="Per-chunk response timeout in seconds")
    ap.add_argument("--skip-configure", action="store_true",
                     help="Skip the adapter's 20-byte settings frame (use if adapter is already "
                          "configured, e.g. via the vendor's GUI tool, or if configure() causes issues)")
    args = ap.parse_args()

    print(f"Opening {args.port} @ {args.serial_baud} baud ...")
    can = WaveshareUsbCanA(args.port, serial_baud=args.serial_baud)
    try:
        if not args.skip_configure:
            print("Configuring adapter for 1 Mbit/s, extended (29-bit) CAN frames ...")
            can.configure(can_speed=CANUSB_SPEED.SPEED_1000000, extended=True, mode=0x00)
        else:
            print("Skipping adapter configure step (--skip-configure).")

        print(f"Requesting register {args.register} from device ID {args.device_id} ...")
        raw = read_binary_register(can, args.device_id, args.register, chunk_timeout=args.timeout)
        print(f"Received {len(raw)} bytes.")

        if args.raw_out:
            with open(args.raw_out, "wb") as f:
                f.write(raw)
            print(f"Raw binary saved to {args.raw_out}")

        records, crc_ok, stored_crc, computed_crc = parse_menu_file(raw)
        print(f"Parsed {len(records)} register records.")
        if not crc_ok:
            print(f"WARNING: CRC mismatch (stored=0x{stored_crc:04X}, computed=0x{computed_crc:04X}). "
                  "File may be corrupted or parsing offsets may have drifted.", file=sys.stderr)

        write_csv(records, args.out)
        print(f"CSV written to {args.out}")

        if args.xlsx_out:
            write_xlsx(records, args.xlsx_out)
            print(f"Excel file written to {args.xlsx_out}")

    finally:
        can.close()


if __name__ == "__main__":
    main() 