import signal
from binascii import hexlify

from dwire import CNTXT_GO_TO_HW_BREAKPOINT
from dwire.DWInterface import DWInterface, INST_ADDR
from dwire.SerialDW import SerialDW
from gdb.GDBServer import GDBServer


def irq(sok):
    print("irq called... i don't know what to do!")


def terminate(dw, srv, sig):
    print(f"terminating gdb server signal {sig}")
    srv.terminate()
    if dw is not None:
        dw.close()
    exit(0)


if __name__ == '__main__':
    #dw = DWInterface(SerialDW('/dev/ttyUSB0', 8000000, True, True))
    srv = GDBServer('sock', irq)
    srv.start()
    signal.signal(signal.SIGINT, lambda sig, frame: terminate(None, srv, sig))

    #dw.halt()
    #f = dw.get_fingerprint()

    # dw.write_firmware("./avrtest/main.flash.bin", erease_device=False)
    # dw.restart_execution()
    #dw.close()