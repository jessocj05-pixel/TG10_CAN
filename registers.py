# ---------- register table: RegID -> (name, type, size, enum-dict or None) ----------

REGS = {
    8: ("EmergencyStop","u32",4,None),
    9: ("Version", "u32", 4, None),
    16: ("Command", "u8", 1, {0: "OFF", 1: "ON", 2: "FAULT"}),
    17: ("OscClock", "u8", 1, None),
    18: ("Ndiv", "u32", 4, None),
    20: ("PhdBias", "u16", 2, None),
    21: ("OptClk", "u32", 4, None),
    22: ("DelayCnt1", "u32", 4, None),
    23: ("Tmin", "u32", 4, None),
    24: ("Tmax", "u32", 4, None),
    25: ("DelayCnt2", "u32", 4, None),
    26: ("DelayCnt3", "u32", 4, None),
    27: ("DelayCnt4", "u32", 4, None),
    28: ("DelayCnt5", "u32", 4, None),
    29: ("DelayCnt6", "u32", 4, None),
    30: ("DelayCnt7", "u32", 4, None),
    31: ("CLKvalid", "u8", 1, {0: "NOCLOCK-NOLOCK", 1: "NOCLOCK-LOCKOK", 2: "CLOCKOK-NOLOCK", 3: "CLOCKOK-LOCKOK"}),
    32: ("Ratediv", "u32", 4, None),
    33: ("Calibrate", "u8", 1, None),
    34: ("SyncRPhase", "u8", 1, None),
    35: ("CPLDVer0", "str8", 8, None),
    36: ("CPLDVer1", "u32", 4, None),
    37: ("CPLDate", "u32", 4, None),
    38: ("PostCnt0", "u16", 2, None),
    39: ("PostCnt1", "u16", 2, None),
    40: ("PostCnt2", "u16", 2, None),
    41: ("PostCnt3", "u16", 2, None),
    42: ("PostCnt4", "u16", 2, None),
    43: ("PostCnt5", "u16", 2, None),
    44: ("PostCnt6", "u16", 2, None),
    45: ("PostCnt7", "u16", 2, None),
    46: ("MuxSetConf10", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    47: ("MuxSetConf20", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    48: ("MuxResConf10", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    49: ("MuxResConf20", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    50: ("MuxSetConf11", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    51: ("MuxSetConf21", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    52: ("MuxResConf11", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    53: ("MuxResConf21", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    54: ("MuxSetConf12", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    55: ("MuxSetConf22", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    56: ("MuxResConf12", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    57: ("MuxResConf22", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    58: ("MuxSetConf13", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    59: ("MuxSetConf23", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    60: ("MuxResConf13", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    61: ("MuxResConf23", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    62: ("MuxSetConf14", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    63: ("MuxSetConf24", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    64: ("MuxResConf14", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    65: ("MuxResConf24", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    66: ("MuxSetConf15", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    67: ("MuxSetConf25", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    68: ("MuxResConf15", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    69: ("MuxResConf25", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    70: ("MuxSetConf16", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    71: ("MuxSetConf26", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    72: ("MuxResConf16", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    73: ("MuxResConf26", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    74: ("MuxSetConf17", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    75: ("MuxSetConf27", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch SET", 13: "GATE", 14: "nGATE", 15: "Delayed res"}),
    76: ("MuxResConf17", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    77: ("MuxResConf27", "u8", 1, {0: "0", 1: "1", 2: "Post-count", 3: "Fine del0", 4: "Fine del1", 5: "Fine del2", 6: "Fine del3", 7: "Fine del4", 8: "Fine del5", 9: "Coarse del6", 10: "Coarse del7", 11: "Trigger", 12: "Latch RES", 13: "GATE", 14: "nGATE", 15: "Delayed set"}),
    78: ("MuxTrg1Out", "u8", 1, {0: "nbOUT0", 1: "nbOUT1", 2: "nbOUT2", 3: "nbOUT3", 4: "nbOUT4", 5: "nbOUT5", 6: "nbOUT6", 7: "nbOUT7", 8: "OPTCLK", 9: "OPCLK div 2", 10: "t1", 11: "t2", 12: "t3", 13: "t4", 14: "t5", 15: "t6"}),
    79: ("MuxPreT", "u8", 1, {0: "nbOUT0", 1: "nbOUT1", 2: "nbOUT2", 3: "nbOUT3", 4: "nbOUT4", 5: "nbOUT5", 6: "nbOUT6", 7: "nbOUT7", 8: "OPTCLK", 9: "OPCLK div 2", 10: "OPTCLK multipler"}),
    80: ("MuxDAC", "u8", 1, {0: "GATE", 1: "nGATE", 2: "GATE and SYNCIN1", 3: "Conf switch", 4: "nbOUT4", 5: "nbOUT5", 6: "nbOUT6", 7: "nbOUT7", 8: "AWG", 9: "AWG@OPTCLK"}),
    81: ("MuxACQ", "u8", 1, {0: "nbOUT0", 1: "nbOUT1", 2: "nbOUT2", 3: "nbOUT3", 4: "nbOUT4", 5: "nbOUT5", 6: "nbOUT6", 7: "nbOUT7"}),
    82: ("MuxConfSw", "u8", 1, {0: "0", 1: "1", 2: "Burst", 3: "nBurst", 4: "F div", 5: "GATE", 6: "nGATE", 7: "GATE and SYNCIN1"}),
    83: ("MuxBurstT", "u8", 1, {0: "SYNCIN", 1: "GATE", 2: "nGATE", 3: "One shot burst"}),
    84: ("MuxStartTrg", "u8", 1, {0: "Rate divider", 1: "Rate div@OPTCLK", 2: "SYNCIN", 3: "SYNCIN@OPTCLK", 4: "One shot trig", 5: "One shot smart"}),
    85: ("MuxRateClk", "u8", 1, {0: "Internal", 1: "OPTCLK", 2: "OPTCLKdiv2", 3: "SYNCIN"}),
    86: ("Adly0", "u8", 1, None),
    87: ("Adly1", "u8", 1, None),
    88: ("Adly2", "u8", 1, None),
    89: ("Adly3", "u8", 1, None),
    90: ("Adly4", "u8", 1, None),
    91: ("Adly5", "u8", 1, None),
    92: ("Adly6", "u8", 1, None),
    93: ("Ddly0", "u8", 1, None),
    94: ("Ddly1", "u8", 1, None),
    95: ("Ddly2", "u8", 1, None),
    96: ("Ddly3", "u8", 1, None),
    98: ("Ddly5", "u8", 1, None),
    99: ("Ddly6", "u8", 1, None),
    100: ("LMKid", "u32", 4, None),
    101: ("FltTmin", "u8", 1, {0: "OFF", 1: "ON"}),
    102: ("FltTmax", "u8", 1, {0: "OFF", 1: "ON"}),
    103: ("LimTmin", "u8", 1, {0: "OFF", 1: "ON"}),
    104: ("LimTmax", "u8", 1, {0: "OFF", 1: "ON"}),
    105: ("Fdiv", "u16", 2, None),
    106: ("FdivAcq", "u16", 2, None),
    107: ("DAC1", "u16", 2, None),
    108: ("DAC2", "u16", 2, None),
    109: ("VCO", "u8", 1, {0: "2.5GHz", 1: "3GHz"}),
    110: ("LagPLL", "s8", 1, None),
    111: ("LD2mux", "s8", 1, {0: "Logic Low", 1: "PLL1 DLD", 2: "PLL2 DLD", 3: "PLL1 & PLL2 DLD", 4: "Holdover Status", 5: "DAC Locked", 6: "Reserved", 7: "SPI Readback", 8: "DAC Rail", 9: "DAC Low", 10: "DAC High", 11: "PLL1_N", 12: "PLL1_Ndiv2", 13: "PLL2_N", 14: "PLL2_N/2", 15: "PLL1_R", 16: "PLL1_Rdiv2", 17: "PLL2_R", 18: "PLL2_Rdiv2"}),
    112: ("OSTrig", "s8", 1, {0: "-", 1: "START"}),
    113: ("OSBurst", "s8", 1, {0: "-", 1: "START"}),
    114: ("OSLSET", "s8", 1, {0: "-", 1: "START"}),
    115: ("OSLCLR", "s8", 1, {0: "-", 1: "START"}),
    116: ("BatchC", "u32", 4, None),
    117: ("OscClkMux", "u8", 1, {0: "Internal 100Mhz", 1: "External"}),
    118: ("OscInF", "u32", 4, None),
    119: ("SYNCINF", "u32", 4, None),
    120: ("SYNCINP", "u32", 4, None),
    121: ("SYNCIN1DL", "u32", 4, None),
    122: ("MuxOut2", "u8", 1, {0: "lOUT2", 1: "lOUT2 and OUT1", 2: "lOUT2 or OUT1", 3: "not OUT1"}),
    123: ("MuxOut3", "u8", 1, {0: "lOUT3", 1: "lOUT3 and OUT2", 2: "lOUT3 or OUT2", 3: "not OUT2"}),
    124: ("MuxOut4", "u8", 1, {0: "lOUT4", 1: "lOUT4 and OUT3", 2: "lOUT4 or OUT3", 3: "not OUT3"}),
    125: ("MuxOut5", "u8", 1, {0: "lOUT5", 1: "lOUT5 and OUT4", 2: "lOUT5 or OUT4", 3: "not OUT4"}),
    126: ("PLL1locked", "u8", 1, {0: "NOLOCK", 1: "LOCKOK"}),
    127: ("NoBurstSync", "u8", 1, {0: "OFF", 1: "ON"}),
    128: ("DelayCnt0", "u32", 4, None),
    129: ("x200mux", "u8", 1, {0: "x4", 1: "x5"}),
    132: ("WADR", "u16", 2, None),
    133: ("WD", "u16", 2, None),
    134: ("AWGdivmux", "u8", 1, {0: "/1", 1: "/2", 2: "/4", 3: "/8"}),
}

# REGISTERS = {info[0]: reg_id for reg_id, info in REGS.items()}

# print(REGISTERS["Command"])
# print(REGS[0x10])
def describe_write(reg_id: int,data:bytes)->str:
    """
    convert(reg_id,data) to readdable strings
    eg  suppose:
        describe_write(0x10, bytes([0x00]))    -> "command = off"
        print(describe_write(0x20, (1000).to_bytes(4, "little")))    ->ratediv=1000
    
    to call in seq you can use this
    for reg_id,data in seq:
        print(describe_write(reg,id,data))
    """
    if reg_id not in REGS:
        return f"UnknownRegister(0x{reg_id:02X})={data.hex()}"
    name, typ, size, enum = REGS[reg_id]

    if data is None:
        return f"{name} = <READ>"
    #convert data bytes back to integer
    value = int.from_bytes(data,byteorder="little")

    if enum is not None:
        meaning = enum.get(value, f"Unknown({value})")
        return f"{name} = {meaning}"
    else:
        return f"{name} = {value}"