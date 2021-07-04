from dwire.gdb_impl.q.qSupported import qSupported
from dwire.gdb_impl.q.qTStatus import qTStatus


def gdb_command_q(answer, packet: bytes, *args):
    command = packet.split(b':', 1)
    if command[0] == b'Supported':
        qSupported(answer)
    elif command[0] == b'TStatus':
        qTStatus(answer)
    else:
        answer(b'`')