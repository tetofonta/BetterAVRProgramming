from dwire.SerialDW.devices.AbstractDevice import AbstractDevice


class DevATTINY85(AbstractDevice):
    NAME = "ATTiny85"
    FINGERPRINT = b'\x93\x0b'
    EECR = 0x1C
    EEDR = 0x1D
    EEARL = 0x1E
    EEARH = 0x1F
    DWRD = 0x22
    SPMCSR = 0x37
    FLASH_PAGEEND = 64

