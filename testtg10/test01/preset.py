
save01 = [
    (0x32, bytes([0x00])),                        # MuxSetConf11 = 0
    (0x33, bytes([0x03])),                        # MuxSetConf21 = 3
    (0x34, bytes([0x00])),                        # MuxResConf11 = 0
    (0x35, bytes([0x02])),                        # MuxResConf21 = 2
]

save002 = [
    (0x3A, bytes([0x00])),                        # MuxSetConf13 = 0
    (0x3B, bytes([0x06])),                        # MuxSetConf23 = 6
    (0x3C, bytes([0x00])),                        # MuxResConf13 = 0
    (0x3D, bytes([0x04])),                        # MuxResConf23 = 4
]
