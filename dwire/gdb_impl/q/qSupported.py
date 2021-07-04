from collections import Callable


def qSupported(answer: Callable, *args):
    answer(b'PacketSize=4096')