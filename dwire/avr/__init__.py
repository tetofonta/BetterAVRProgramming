def OUT(A, r):
    return int.to_bytes(0b1011100000000000 | ((r & 0x1F) << 4) | (A & 0x0F) | ((A & 0x30) << 5), 2, 'big')


def IN(r, A):
    return int.to_bytes(0b1011000000000000 | ((r & 0x1F) << 4) | (A & 0x0F) | ((A & 0x30) << 5), 2, 'big')


def MOVW(wd, wr):
    wd = int(wd/2)
    wr = int(wr/2)
    return int.to_bytes(0b0000000100000000 | ((wd & 0x0F) << 4) | (wr & 0x0F), 2, 'big')


def SPM():
    return int.to_bytes(0b1001010111101000, 2, 'big')


def ADIW(w, K):
    return int.to_bytes(0b1001011000000000 | ((K & 0x30) << 2) | (K & 0x0F) | ((w & 0x03) << 4), 2, 'big')


def LDI(rd, K):
    return int.to_bytes(0b1110000000000000 | ((K & 0xF0) << 8) | (K & 0x0F) | ((rd & 0x0F) << 4), 2, 'big')