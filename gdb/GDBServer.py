import os
import signal
import socket
import sys
import threading
from binascii import hexlify
from functools import reduce, partial

from dwire.DWInterface import DWInterface
from gdb.GDBUtils import unescape, read_packet, answer

commands = {}
def command(character):
    def _func(func):
        commands[character] = func
        print(f'registered packet handler for {character}')
    return _func


class GDBServer(socket.socket):

    def __init__(self, bind_file, irq_handler, dw: DWInterface):
        socket.socket.__init__(self, socket.AF_UNIX, socket.SOCK_STREAM)
        self.bind_file = bind_file
        self.thread = None
        self.keep_working = True
        self.irq_handler = irq_handler
        self.dw = dw

        self.ack = True
        self.extended = False

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
            #list supported features
            print("GDB SERVER SUPPORTED FUNCTIONS", data)
            answ(b"PacketSize=48ff;qXfer:features:read+;hwbreak+;swbreak+")
        elif b'Xfer:' in data:
            #transfer somenthing from target
            data = data[5:]
            if b'features:read' in data:
                #transfer features
                data = data[14:]
                annex, offset, length = data.replace(b',', b':').split(b':')
                with open(annex, "rb") as file:
                    file.seek(int(offset))
                    read = file.read(int(length))
                    if len(read) < int(length):
                        answ(b'l' + read)
                    else:
                        answ(b'm' + read)
        elif b"TStatus" in data:
            #Trace experiment status (no trace suopported)
            answ()
        elif b'fThreadInfo' in data:
            # first thread info request for thread ids
            answ(b'm1')
        elif b'sThreadInfo' in data:
            answ(b'l')
        elif b'Attached' in data:
            answ(b'1')
        elif b'Offset' in data:
            answ()  # no relocation
        elif b'C' in data:
            answ(b'QC01')
        else:
            answ()

    @command('v')
    def empty(self, answ, data):
        if data == b"MustReplyEmpty":
            answ()

    @command('!')
    def begin_extended_remote(self, answ, data):
        self.extended = True
        answ()

    @command('H')
    def set_thread(self, answ, data):
        answ(b'OK') #we are singlethreaded...

    @command('?')
    def query_halt_reason(self, answ, data):
        answ(self.dw.halt_reason().encode())

    @command('g')
    def get_registers(self, answ, data):
        #reg 0-31 SREG SP(16bit) PC2(16bit) PC(16bit)
        gpreg = hexlify(self.dw.read_registers(0, 32))
        sreg = hexlify(self.dw.read_io_space(0x3F, 1))
        sp = hexlify(self.dw.read_io_space(0x3D, 2))
        pc2 = b'0000'
        pc = hexlify(int.to_bytes(self.dw.get_pc()-1, 2, 'little'))
        answ(gpreg + sreg + sp + pc + pc2)

    #@command('v')
    #def
