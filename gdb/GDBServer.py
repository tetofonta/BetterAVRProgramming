import os
import signal
import socket
import sys
import threading
from functools import reduce, partial

from gdb.GDBUtils import unescape, read_packet, answer

commands = {}
def command(character):
    def _func(func):
        commands[character] = func
        print(f'registered packet handler for {character}')
    return _func


class GDBServer(socket.socket):

    def __init__(self, bind_file, irq_handler, **kwargs):
        socket.socket.__init__(self, socket.AF_UNIX, socket.SOCK_STREAM)
        self.bind_file = bind_file
        self.thread = None
        self.keep_working = True
        self.irq_handler = irq_handler
        self.oth = kwargs
        self.ack = True

    def terminate(self, timeout=1):
        self.keep_working = False
        self.thread.join(timeout)
        print("Closed")

    def start(self):
        if os.path.exists("sock"):
            os.remove("sock")
        self.bind(self.bind_file)
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
                if packet[0] in commands:
                    commands[packet[0]](self, partial(answer, sok, self.ack), packet[1])
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

    @command('q')
    def cmd_query(self, answ, data):
        if b"Supported:" in data:
            print("GDB SERVER SUPPORTED FUNCTIONS", data)
            answ(b"$PacketSize=48ff;qXfer:features:read+#a3")

    @command('v')
    def empty(self, answ, data):
        if data == b"MustReplyEmpty":
            answ()

    @command('!')
    def begin_extended_remote(self, answ, data):
        answ()
