import time

from dwire import STATUS_RUNNING


def gdb_command_reason(answ, packet, state, *args):
    while state["dev"].status() == STATUS_RUNNING:
        print("Device is running, waiting...")
        state["dev"].wait_hit(timeout=5)

