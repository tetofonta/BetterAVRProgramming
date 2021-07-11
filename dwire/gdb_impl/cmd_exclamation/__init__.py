def gdb_command_exclamation(answ, data, state, *args):
    #enable extended mode
    state["extended_mode"] = True
    answ(b'OK')