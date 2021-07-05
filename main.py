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
    print("PAGE 0\n\t", hexlify(dw.read_flash(0x00, 128)))
    flash_content = dw.read_flash(128, 128)
    print("PAGE 1\n\t", hexlify(flash_content))
    flash_content = b'\x00\x01\x02\x03\x04' + flash_content[5:]
    print("Attempt to write Page 1 (0x80) as\n\t", hexlify(flash_content))

    dw.write_flash(flash_content, 128, 1)
    print("PAGE 1\n\t", hexlify(dw.read_flash(128, 128)))
    dw.close()