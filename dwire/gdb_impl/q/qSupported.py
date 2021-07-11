from collections import Callable


def qSupported(answer: Callable, data, state, *args):
    state["supported"] = data[10:].split(b";")
    answer(b'PacketSize=47ff;'
           b'QStartNoAckMode+;'
           b'no-resumed+'
           b'Qbtrace:off-;'
           b'QStartNoAckMode+'
           b'Qbtrace:bts-;'
           b'Qbtrace:pt-;'
           b'Qbtrace-conf:bts:size-;'
           b'Qbtrace-conf:pt:size-')