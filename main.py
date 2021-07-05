from binascii import hexlify
from time import sleep

from dwire import CTRL_REG_IR, CTRL_REG_PC, CNTXT_GO_TO_HW_BREAKPOINT
from dwire.DWInterface import DWInterface, FLASH_PAGE, INST_ADDR
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
    dev = SerialDW('/dev/ttyUSB0', 8000000)
    dw = DWInterface(dev)
    dw.halt()
    dw.restart_execution(False)

    while True:
        print(f"PC={hex(dw.get_pc())}")
        dw.set_hw_breakpoint(INST_ADDR(int(input("nex_addr (hex)> "), 16)))
        dw.resume_execution(CNTXT_GO_TO_HW_BREAKPOINT, pc=-1)
        dw.wait_hit()
        print("hit")

    dw.close()