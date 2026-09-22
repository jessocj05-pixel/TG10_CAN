
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

save002 = [
    (0x3A, bytes([0x00])),                        # MuxSetConf13 = 0
    (0x3B, bytes([0x06])),                        # MuxSetConf23 = 6
    (0x3C, bytes([0x00])),                        # MuxResConf13 = 0
    (0x3D, bytes([0x04])),                        # MuxResConf23 = 4
]

preset_check = [
    (0x10, bytes([0x00])),                        # Command = 0
    (0x75, bytes([0x00])),                        # OscClkMux = 0
    (0x11, bytes([0x64])),                        # OscClock = 100
    (0x12, (30).to_bytes(4, "little")),           # Ndiv = 30
    (0x6D, bytes([0x01])),                        # VCO = 1
    (0x55, bytes([0x00])),                        # MuxRateClk = 0
    (0x54, bytes([0x00])),                        # MuxStartTrg = 0
    (0x20, (10).to_bytes(4, "little")),           # Ratediv = 10
    (0x52, bytes([0x01])),                        # MuxConfSw = 1
    (0x80, (3).to_bytes(4, "little")),            # DelayCnt0 = 3
    (0x5D, bytes([0x04])),                        # Ddly0 = 4
    (0x56, bytes([0x00])),                        # Adly0 = 0
    (0x16, (3).to_bytes(4, "little")),            # DelayCnt1 = 3
    (0x5E, bytes([0x08])),                        # Ddly1 = 8
    (0x57, bytes([0x00])),                        # Adly1 = 0
    (0x19, (3).to_bytes(4, "little")),            # DelayCnt2 = 3
    (0x5F, bytes([0x0A])),                        # Ddly2 = 10
    (0x58, bytes([0x00])),                        # Adly2 = 0
    (0x1B, (4).to_bytes(4, "little")),            # DelayCnt4 = 4
    (0x1C, (10).to_bytes(4, "little")),           # DelayCnt5 = 10
    (0x62, bytes([0x18])),                        # Ddly5 = 24
    (0x5B, bytes([0x00])),                        # Adly5 = 0
    (0x26, (21).to_bytes(2, "little")),           # PostCnt0 = 21
    (0x28, (11).to_bytes(2, "little")),           # PostCnt2 = 11
    (0x29, (258).to_bytes(2, "little")),          # PostCnt3 = 258
    (0x2E, bytes([0x00])),                        # MuxSetConf10 = 0
    (0x2F, bytes([0x03])),                        # MuxSetConf20 = 3
    (0x30, bytes([0x00])),                        # MuxResConf10 = 0
    (0x31, bytes([0x02])),                        # MuxResConf20 = 2
]
