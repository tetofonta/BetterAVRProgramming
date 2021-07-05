class AbstractDevice:
    FINGERPRINT = None
    EECR = None
    EEDR = None
    EEARL = None
    EEARH = None
    DWRD = None
    SPMCSR = 0x37

    def __init__(self):
        assert False