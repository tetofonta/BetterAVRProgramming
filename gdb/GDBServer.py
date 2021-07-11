import signal
import socket
import sys
import threading
from functools import reduce, partial

from gdb.GDBUtils import unescape, read_packet, answer


class GDBServer(socket.socket):
    def __init__(self, bind_port, bind_address, command_handlers, irq_handler, state=None):
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
        if state is None:
            state = {}
        self.bind_port = bind_port
        self.bind_addr = bind_address
        self.thread = None
        self.keep_working = True
        self.irq_handler = irq_handler
        self.command_handlers = command_handlers
        state["ack"] = True
        self.debugger_state = state

    def terminate(self, timeout=1):
        self.keep_working = False
        self.thread.join(timeout)
        print("Closed")

    def start(self):
        self.bind((self.bind_addr, self.bind_port))
        self.listen(1)
        self.thread = threading.Thread(target=GDBServer.gdb_thread, args=(self, *self.accept()))
        self.thread.start()
        return self.thread

    def gdb_thread(self, sok: socket.socket, addr_info):
        try:
            print(f"connected to {addr_info}")
            while self.keep_working:
                packet = read_packet(sok, self.irq_handler)
                packet = [chr(packet[0]), packet[1:]]
                print(f"Requested command {packet[0]}")
                if packet[0] in self.command_handlers:
                    self.command_handlers[packet[0]](partial(answer, sok, self.debugger_state), packet[1], self.debugger_state)
                else:
                    print(f"Unknown command {packet[0]}")
                    pass

            self.cleanup(sok)
        except Exception as e:
            print("Exception threw:", e)
            self.cleanup(sok)

    def cleanup(self, sok):
        print("Stopping execution")
        sok.close()
        self.close()
