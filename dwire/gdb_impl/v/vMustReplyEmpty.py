from collections import Callable


def vMustReplyEmpty(answer: Callable, *args):
    answer(b'')