def QStartNoAckMode(answ, state):
    answ(b'OK', True)
    state["ack"] = False