import socket
import threading
from functools import reduce, partial

from gdb.GDBUtils import unescape, read_packet, answer


class GDBServer(socket.socket):
    def __init__(self, bind_port, bind_address, command_handlers, irq_handler):
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
        self.bind((bind_address, bind_port))
        self.listen(1)
        self.thread = None
        self.keep_working = True
        self.irq_handler = irq_handler
        self.command_handlers = command_handlers
        self.debugger_state = {}

    def start(self):
        self.thread = threading.Thread(target=GDBServer.gdb_thread, args=(self, *self.accept()))
        self.thread.start()

    def gdb_thread(self, sok: socket.socket, addr_info):
        print(f"connected to {addr_info}")
        while self.keep_working:
            packet = read_packet(sok, self.irq_handler)
            packet = [chr(packet[0]), packet[1:]]
            print(f"Requested command {packet[0]}")
            if packet[0] in self.command_handlers:
                self.command_handlers[packet[0]](partial(answer, sok), packet[1], self.debugger_state)
            else:
                pass

        self.cleanup()

    def cleanup(self):
        print("Stopping execution")
        self.close()
