import signal
from binascii import hexlify

from dwire import CNTXT_GO_TO_HW_BREAKPOINT
from dwire.DWInterface import DWInterface, INST_ADDR
from dwire.SerialDW import SerialDW
from dwire.gdb_impl import packets
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
    dw = DWInterface(SerialDW('/dev/ttyUSB0', 8000000, True, True))
    # srv = GDBServer(1234, "localhost", packets, irq, {"dev": dw})
    # srv.start()
    # signal.signal(signal.SIGINT, lambda sig, frame: terminate(dw, srv, sig))

    dw.write_firmware("/home/stefano/avrtest/blink2.bin", erease_device=True)
    dw.restart_execution(False)
    dw.set_sw_breakpoint(0x36)
    dw.close()