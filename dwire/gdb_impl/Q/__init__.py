from dwire.gdb_impl.Q.QStartNoAckMode import QStartNoAckMode


def gdb_command_Q(answ, packet, state, *args):
    if packet == b'StartNoAckMode':
        QStartNoAckMode(answ, state)