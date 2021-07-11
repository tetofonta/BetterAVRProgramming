class AbstractDevice:
    FINGERPRINT = None
    EECR = None
    EEDR = None
    EEARL = None
    EEARH = None
    DWRD = None
    SPMCSR = 0x37
    FLASH_SIZE = 0
    EEPROM_SIZE = 0
    SRAM_SIZE = 0
    SRAM_BASE = 0x100
    FLASH_PAGEEND = 128

    def __init__(self):
        assert False