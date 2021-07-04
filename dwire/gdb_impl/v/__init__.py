from dwire.gdb_impl.v.vMustReplyEmpty import vMustReplyEmpty


def gdb_command_v(answer, packet: bytes, *args):
    if packet == b"MustReplyEmpty":
        vMustReplyEmpty(answer)