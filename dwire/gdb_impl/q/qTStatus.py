from dwire import STATUS_RUNNING


def qTStatus(answ, packet, state, *args):
    if state["dev"].status() == STATUS_RUNNING():
        return answ(b'T1')
    answ(b'T0;tnotrun:0')