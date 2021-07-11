from dwire.gdb_impl.H import gdb_command_H
from dwire.gdb_impl.Q import gdb_command_Q
from dwire.gdb_impl.cmd_exclamation import gdb_command_exclamation
from dwire.gdb_impl.cmd_stop_reason import gdb_command_reason
from dwire.gdb_impl.q import gdb_command_q
from dwire.gdb_impl.v import gdb_command_v

packets = {
        'q': gdb_command_q,
        'Q': gdb_command_Q,
        'v': gdb_command_v,
        'H': gdb_command_H,
        '!': gdb_command_exclamation,
        '?': gdb_command_reason
}

