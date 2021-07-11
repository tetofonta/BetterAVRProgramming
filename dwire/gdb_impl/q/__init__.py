from dwire.gdb_impl.q.qSupported import qSupported
from dwire.gdb_impl.q.qTStatus import qTStatus
from dwire.gdb_impl.q.qTfV import qTfV


def gdb_command_q(answer, packet: bytes, state, *args):
    command = packet.split(b':', 1)
    if command[0] == b'Supported':
        qSupported(answer, packet, state, *args)
    elif command[0] == b'TStatus':
        qTStatus(answer, packet, state)
    elif command[0] == b'TfV':
        qTfV(answer, packet, state)
    else:
        pass