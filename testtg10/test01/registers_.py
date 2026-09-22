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


REGISTERS = {info[0]: reg_id for reg_id, info in REGS.items()}

# Convenience constants (RegID == bus address)
REG_COMMAND       = 16 
REG_OSCCLOCK      = 17
REG_NDIV          = 18
REG_CLKVALID      = 31
REG_RATEDIV       = 32
REG_MUX_CONFSW    = 82
REG_MUX_BURSTTRIG = 83
REG_MUX_STARTTRG  = 84
REG_MUX_RATECLK   = 85
REG_FDIV          = 105
REG_FDIVACQ       = 106
REG_DAC1          = 107
REG_DAC2          = 108
REG_VCO           = 109
REG_ONESHOTTRIG   = 112
REG_ONESHOTBURST = 113
REG_ONESHOTLATCHSET=114
REG_ONESHOTLATCHRESET=115
REG_BURSTCOUNT    = 116
REG_OSCCLKMUX     = 117
REG_PLL1LOCKED    = 126
REG_ERRORCODE     = 2
REG_MUX_COMTRIG   = 78
REG_MUX_PRET      = 79
REG_MUX_DAC       = 80
REG_MUXACQ        = 81

_REG_NAMES = {
    0x10: "Command",
    0x02: "error",
    0x11: "OscClock",
    0x12: "Ndiv",
    0x16: "DelayCnt1", 0x19: "DelayCnt2", 0x1A: "DelayCnt3",
    0x1B: "DelayCnt4", 0x1C: "DelayCnt5", 0x1D: "DelayCnt6", 0x1E: "DelayCnt7",
    0x20: "Ratediv",
    0x26: "PostCnt0", 0x27: "PostCnt1", 0x28: "PostCnt2", 0x29: "PostCnt3",
    0x2A: "PostCnt4", 0x2B: "PostCnt5", 0x2C: "PostCnt6", 0x2D: "PostCnt7",
    0x2E: "MuxSetConf10", 0x2F: "MuxSetConf20", 0x30: "MuxResConf10", 0x31: "MuxResConf20",
    0x32: "MuxSetConf11", 0x33: "MuxSetConf21", 0x34: "MuxResConf11", 0x35: "MuxResConf21",
    0x36: "MuxSetConf12", 0x37: "MuxSetConf22", 0x38: "MuxResConf12", 0x39: "MuxResConf22",
    0x3A: "MuxSetConf13", 0x3B: "MuxSetConf23", 0x3C: "MuxResConf13", 0x3D: "MuxResConf23",
    0x3E: "MuxSetConf14", 0x3F: "MuxSetConf24", 0x40: "MuxResConf14", 0x41: "MuxResConf24",
    0x42: "MuxSetConf15", 0x43: "MuxSetConf25", 0x44: "MuxResConf15", 0x45: "MuxResConf25",
    0x46: "MuxSetConf16", 0x47: "MuxSetConf26", 0x48: "MuxResConf16", 0x49: "MuxResConf26",
    0x4A: "MuxSetConf17", 0x4B: "MuxSetConf27", 0x4C: "MuxResConf17", 0x4D: "MuxResConf27",
    0x4E: "MuxTrg1Out", 0x4F: "MuxPreT", 0x50: "MuxDAC",
    0x52: "MuxConfSw", 0x53: "MuxBurstT", 0x54: "MuxStartTrg", 0x55: "MuxRateClk",
    0x56: "Adly0", 0x57: "Adly1", 0x58: "Adly2", 0x59: "Adly3",
    0x5A: "Adly4", 0x5B: "Adly5", 0x5C: "Adly6",
    0x5D: "Ddly0", 0x5E: "Ddly1", 0x5F: "Ddly2", 0x60: "Ddly3",
    0x62: "Ddly5", 0x63: "Ddly6",
    0x69: "Fdiv", 0x6B: "DAC1", 0x6C: "DAC2", 0x6D: "VCO",
    0x70: "OSTrig", 0x74: "BatchC", 0x75: "OscClkMux",
    0x76: "OscInF", 0x77: "SYNCINF",
    0x7A: "MuxOut2", 0x7B: "MuxOut3", 0x7C: "MuxOut4", 0x7D: "MuxOut5",
    0x80: "DelayCnt0",
}

DELAY_REGS = {
    0: {"cnt": 128, "d": 93, "a": 86},
    1: {"cnt": 22,  "d": 94, "a": 87},
    2: {"cnt": 25,  "d": 95, "a": 88},
    3: {"cnt": 26,  "d": 96, "a": 89},
    4: {"cnt": 27,  "d": None, "a": 90},
    5: {"cnt": 28,  "d": 98, "a": 91},
    6: {"cnt": 29,  "d": 99, "a": 92},
    7: {"cnt": 30,  "d": None, "a": None},
}

POSTDEL_REGS = {i: 38 + i for i in range(8)}

SR_BLOCK_REGS = {
    0: {"set1": 46, "set2": 47, "res1": 48, "res2": 49},
    1: {"set1": 50, "set2": 51, "res1": 52, "res2": 53},
    2: {"set1": 54, "set2": 55, "res1": 56, "res2": 57},
    3: {"set1": 58, "set2": 59, "res1": 60, "res2": 61},
    4: {"set1": 62, "set2": 63, "res1": 64, "res2": 65},
    5: {"set1": 66, "set2": 67, "res1": 68, "res2": 69},
    6: {"set1": 70, "set2": 71, "res1": 72, "res2": 73},
    7: {"set1": 74, "set2": 75, "res1": 76, "res2": 77},
}
LOGIC_MUX_REGS = {
    2: REGISTERS["MuxOut2"],
    3: REGISTERS["MuxOut3"],
    4: REGISTERS["MuxOut4"],
    5: REGISTERS["MuxOut5"],
}
 
# Mux set/res source codes — from SY4000 OEM datasheet Table 15 / Ch7
# register enum (S/R latch input signals). Same table for all 8 blocks.
SR_SOURCE_MAP = {
    "no_change": 0,
    "force": 1,
    "post_count": 2,
    "fine_del0": 3,
    "fine_del1": 4,
    "fine_del2": 5,
    "fine_del3": 6,
    "fine_del4": 7,
    "fine_del5": 8,
    "coarse_del6": 9,
    "coarse_del7": 10,
    "trigger": 11,
    "latch": 12,
    "gate": 13,
    "ngate": 14,
    "delayed": 15,
}

OUTPUTS = {
    "0": "OUT0",
    "1": "OUT1 (internal)",
    "2": "OUT2",
    "3": "OUT3",
    "4": "OUT4",
    "5": "OUT5",
    "6": "OUT6 (internal)",
    "7": "OUT7 (internal)",
}
# print(REGISTERS["Command"])
# print(REGS[0x10])

def enum_lookup(reg_id, user_text):
    """Look up code from REGS[reg_id] enum only (no aliases)."""
    name, typ, size, enum = REGS[reg_id]
    text = str(user_text).strip()

    if enum is None:
        return int(text)

    if text.isdigit():
        val = int(text)
        if val in enum:
            return val
        raise ValueError(f"{val} not in enum for {name}")

    text_l = text.lower()
    for code, label in enum.items():
        if label.lower() == text_l:
            return code

    raise ValueError(f"{user_text!r} not in {name}: {list(enum.values())}")

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

def describe_seq(seq):
    for reg_id, data in seq:
        print(f"  0x{reg_id:02X}  {describe_write(reg_id, data)}")

def validate_register_data(reg_id, data):
    """
    Validate payload before building/sending a CAN frame.
    Raises ValueError if anything is wrong.
    Returns True on success.
    """
    # 1) register exists
    if reg_id not in REGS:
        raise ValueError(f"unknown register 0x{reg_id:02X}")

    name, typ, size, enum = REGS[reg_id]

    # 2) data is bytes
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError(f"{name}: data must be bytes, got {type(data).__name__}")

    # 3) size matches
    if len(data) != size:
        raise ValueError(
            f"{name} (0x{reg_id:02X}): expected {size} byte(s), got {len(data)}"
        )

    # 4) value fits type + enum (if any)
    value = int.from_bytes(data, "little", signed=typ.startswith("s"))

    if typ in ("u8", "u16", "u32"):
        bits = {"u8": 8, "u16": 16, "u32": 32}[typ]
        if not (0 <= value < (1 << bits)):
            raise ValueError(f"{name}: value {value} out of range for {typ}")

    elif typ in ("s8", "s16", "s32"):
        bits = {"s8": 8, "s16": 16, "s32": 32}[typ]
        lo, hi = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
        if not (lo <= value <= hi):
            raise ValueError(f"{name}: value {value} out of range for {typ}")

    # str8 / other: size check above is enough

    # 5) enum membership
    if enum is not None and value not in enum:
        raise ValueError(
            f"{name}: value {value} not in enum {list(enum.keys())}"
        )

    return True
#-------------------------------------------------------------------------------------------------
# testing example:
# print("\n=== sample seq ===")
# if __name__ == "__main__":
#     seq = [
#         (0x10, bytes([0x00])),
#         (0x75, bytes([0x00])),
#         (0x12, (30).to_bytes(4, "little")),
#         (0x55, bytes([0x01])),
#         (0x2E, bytes([enum_lookup(46, "Fine del0")])),
#     ]
#     describe_seq(seq)
# before appending to seq / before send
# validate_register_data(REG_COMMAND, bytes([0x01]))   # OK
# validate_register_data(REG_COMMAND, bytes([0x01, 0x02]))  # raises: expected 1 byte

# seq = []
# payload = (30).to_bytes(4, "little")
# validate_register_data(REG_NDIV, payload)
# seq.append((REG_NDIV, payload))

# eg:
# for addr, payload in seq:
#     validate_register_data(addr, payload)
# OUT sources use enum, not a hand map:Pythoncode = enum_lookup(46, user_text)  # e.g. "Fine del0" → 3
# hw to use in code

#---------------------------------------------------------------------------------------------------