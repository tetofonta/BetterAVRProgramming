class AbstractDevice:
    FINGERPRINT = None
    EECR = None
    EEDR = None
    EEARL = None
    EEARH = None
    DWRD = None

    def __init__(self):
        assert False