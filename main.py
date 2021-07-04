from binascii import hexlify
from time import sleep

from dwire.SerialDW import SerialDW
from dwire.gdb_impl.H import gdb_command_H
from dwire.gdb_impl.v import gdb_command_v
from dwire.gdb_impl.q import gdb_command_q
from gdb.GDBServer import GDBServer


def irq(sok):
    print("irq called... i don't know what to do!")


if __name__ == '__main__':
    # packets = {
    #     'q': gdb_command_q,
    #     'v': gdb_command_v,
    #     'H': gdb_command_H
    # }
    # GDBServer(1234, "localhost", packets, irq).start()
    dw = SerialDW('/dev/ttyUSB0', 8000000)
    # dw._dw_cmd_break()
    print(dw.read_eeprom(0x00, 16))
    dw.close()