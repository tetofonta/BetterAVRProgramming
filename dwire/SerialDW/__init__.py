import math
from binascii import hexlify

from serial import Serial

from dwire.SerialDW.devices import devices
from dwire.avr import OUT, IN, MOVW, SPM, ADIW, LDI

_dw_baud_divisor_bytes = [b'\xA3', b'\xA2', b'\xA1', b'\xA0', b'\x80', b'\x81', b'\x82', b'\x83']

class SerialDW(Serial):
    def __init__(self, port, target_frequency, break_execution=True, reset_execution=False):
        self.target_freq = target_frequency
        self.divisor = 128
        baudrate = int(self.target_freq/self.divisor)
        Serial.__init__(self, port, baudrate=baudrate)

        if not self.isOpen():
            self.open()
        assert self.isOpen()
        assert baudrate * 0.95 <= self.baudrate <= baudrate * 1.05 # baud stability within 5%
        self.timeout = 4 #(s?)

        print("Connecting to the device...")
        assert self._dw_cmd_break()
        self._dw_cmd_set_baud_rate(self.divisor)
        self.device_fingerprint = self._dw_cmd_fingerprint()
        print(f"Connected to the device. DW ID is {hexlify(self.device_fingerprint)}")

        if self.device_fingerprint in devices:
            self.dev = devices[self.device_fingerprint]
            print(f"Device found:\n\t name: {self.dev.NAME}")

        if reset_execution:
            print("Resetting program execution")
            self._dw_cmd_reset()
        print(f"PC is now @ {self._dw_cmd_get_pc()}")
        if not break_execution:
            self._dw_cmd_continue()

    def open(self):
        print(f"Opening serial port @ {self.baudrate} baud")
        Serial.open(self)

    def dw_cmd(self, cmd: bytes, response_length: int):
        self.reset_input_buffer()
        self.write(cmd)
        assert self.read(len(cmd)) == cmd
        return self.read(response_length) if response_length > 0 else None

    def _dw_cmd_break(self):
        """
        Sends a break command to the target. expects a 0x55 as an answer.
        this makes the target reset the baudrate.
        :return:
        """
        baudrate = int(self.target_freq / self.divisor)
        self.baudrate = baudrate
        assert baudrate * 0.95 <= self.baudrate <= baudrate * 1.05  # baud stability within 5%
        self.send_break(0)
        return self.read(2) == b'\x00\x55'

    def _dw_cmd_set_baud_rate(self, divisor):
        """
        sets the transmission baud rate and sends a break instruction afterwards.
        :param divisor: the frequency divisor for the baudrate
        :return:
        """
        assert (divisor & (divisor - 1)) == 0 and divisor > 0 #has to be power of two
        self.divisor = divisor
        self.dw_cmd(_dw_baud_divisor_bytes[int(math.log2(divisor))], 0)
        self.reset_input_buffer()

        baudrate = int(self.target_freq/self.divisor)
        self.baudrate = baudrate
        assert baudrate * 0.95 <= self.baudrate <= baudrate * 1.05 # baud stability within 5%

    def _dw_cmd_fingerprint(self):
        """
        returns target fingerprint
        :return:
        """
        return self.dw_cmd(b'\xf3', 2)

    def _dw_cmd_continue(self):
        """
        tells the target to continue the program execution from where the pc is set
        :return:
        """
        return self.dw_cmd(b'\x30', 0)

    def _dw_cmd_disable(self):
        """
        disables debugWire [until next reset?]
        :return:
        """
        return self.dw_cmd(b'\x06', 0)

    def _dw_cmd_reset(self):
        """
        resets the target
        :return:
        """
        return self.dw_cmd(b'\x07', 2) == b'\x00\x55'

    def _dw_cmd_get_pc(self):
        """
        return the value of the program counter
        :return:
        """
        return self.dw_cmd(b'\xF0', 2)

    def _dw_cmd_start_mem_cycle(self):
        """
        this is a command used to issue a memory (sram/flash) read/write cycle
        :return:
        """
        return self.dw_cmd(b'\x20', 0)

    def _dw_cmd_start_reg_cycle(self):
        """
        this is a command used to issue a register read/write cycle
        :return:
        """
        return self.dw_cmd(b'\x21', 0)

    def _dw_cmd_exec(self):
        """
        this command executes the instruction which has been stored inside the IR (\xD2)
        :return:
        """
        return self.dw_cmd(b'\x23', 0)

    def _dw_cmd_single_step(self):
        """
        single steps to the next instruction (PC increment twice?)
        :return:
        """
        return self.dw_cmd(b'\x31', 0)

    def _dw_cmd_continue_inst_override(self):
        """
        makes the target continues the execution but keeps the IR status as loaded (does not fetch the current instruction)
        Used to software breakpoint, then we load the instruction into the ir and resume execution but we keep the break in memory (baaaad)
        :return:
        """
        return self.dw_cmd(b'\x32', 0)

    def _dw_cmd_single_step_slow(self):
        """
        single step for slow loaded instruction (spm). wait for \x00\x55
        :return:
        """
        return self.dw_cmd(b'\x33', 2) == b'\x00\x55'

    CNTXT_GO_INDEFINITLY = 0x40
    CNTXT_GO_TO_HW_BREAKPOINT = 0x41
    CNTXT_STEP_OUT= 0x43 # step out
    CNTXT_WRT_FLASH = 0x44
    CNTXT_RW = 0x46
    CNTXT_STEP_IN = 0x59
    CNTXT_SINGLE_STEP = 0x5A

    def _dw_set_cntxt(self, context, disable_timers=False):
        self.dw_cmd(bytes([context | ((1 << 5) if disable_timers else 0)]), 0)

    TRGT_SRAM_R = b'\x00'
    TRGT_SRAM_W = b'\x04'
    TRGT_REGS_R = b'\x01'
    TRGT_REGS_W = b'\x05'
    TRGT_FLASH = b'\x02'

    def _dw_set_rw_destination(self, target):
        self.dw_cmd(b'\xC2' + target, 0)

    CTRL_REG_PC = 0x00
    CTRL_REG_HWBP = 0x01
    CTRL_REG_IR = 0x02

    def _dw_wrt_ctrl_reg_word(self, ctrl_reg, value: bytes):
        self.dw_cmd(bytes([0xD0 | ctrl_reg]) + value, 0)

    def _dw_wrt_ctrl_reg_low(self, ctrl_reg, value: bytes):
        self.dw_cmd(bytes([0xC0 | ctrl_reg]) + bytes([value[0]]), 0)

    def _dw_read_ctrl_reg_word(self, ctrl_reg):
        return self.dw_cmd(bytes([0xF0 | ctrl_reg]), 2)

    def _dw_read_ctrl_reg_low(self, ctrl_reg):
        return self.dw_cmd(bytes([0xE0 | ctrl_reg]), 1)

    def resume_execution(self, pc_address=None, context=CNTXT_GO_TO_HW_BREAKPOINT, disable_timers=False):
        if pc_address is not None:
            self._dw_wrt_ctrl_reg_word(SerialDW.CTRL_REG_PC, pc_address)
        self._dw_set_cntxt(context, disable_timers)
        self._dw_cmd_continue()

    def _setup_register_rw(self, start_register, end_register, target):
        self._dw_set_cntxt(self.CNTXT_RW, disable_timers=True)  # 66
        self._dw_wrt_ctrl_reg_word(SerialDW.CTRL_REG_PC, b'\x00' + bytes([start_register]))
        self._dw_wrt_ctrl_reg_word(SerialDW.CTRL_REG_HWBP, b'\x00' + bytes([end_register]))
        self._dw_set_rw_destination(target)  # C2 01
        self._dw_cmd_start_mem_cycle()  # registers are contiguous mem

    def read_registers(self, start_register, end_register=None):
        end_register = end_register if end_register is not None else start_register + 1
        self._setup_register_rw(start_register, end_register, self.TRGT_REGS_R)
        return self.read(end_register - start_register)

    def write_registers(self, data, start_register, length=None):
        end_register = start_register + len(data)
        if length is not None:
            data = data[:length]
        self._setup_register_rw(start_register, end_register, self.TRGT_REGS_W)
        self.dw_cmd(data, 0)

    def read_mem(self, addr, len, target):
        """
        Do not read addresses 30, 31 or DWDR of sram as these interfere with the read process. should not exceed 128bytes at a time
        :param addr:
        :param len:
        :return:
        """
        assert 1 <= len
        self.write_registers(int.to_bytes(addr, 2, 'little'), 0x1E, 2)  # set address in Z reg - sends 66 too
        self._dw_wrt_ctrl_reg_word(SerialDW.CTRL_REG_PC, b'\x00\x00')
        self._dw_wrt_ctrl_reg_word(SerialDW.CTRL_REG_HWBP, int.to_bytes(len * 2, 2, 'big'))
        self._dw_set_rw_destination(target)
        self._dw_cmd_start_mem_cycle()
        return self.read(len)

    def read_sram(self, addr, len):
        return self.read_mem(addr, len, SerialDW.TRGT_SRAM_R)

    def write_sram(self, data, addr, length=None):
        """
        write sram. should not write to registers from 28 to 31
        :param data:
        :param addr:
        :param length:
        :return:
        """
        if length is not None:
            data = data[:length]

        self.write_registers(int.to_bytes(addr, 2, 'little'), 0x1E, 2) # set address in Z reg - sends 66 too
        self._dw_wrt_ctrl_reg_word(SerialDW.CTRL_REG_PC, b'\x00\x01')
        self._dw_wrt_ctrl_reg_word(SerialDW.CTRL_REG_HWBP, int.to_bytes(len(data)*2+1, 2, 'big'))
        self._dw_set_rw_destination(SerialDW.TRGT_SRAM_W)
        self._dw_cmd_start_mem_cycle()
        self.dw_cmd(data, 0)

    def read_flash(self, addr, len):
        return self.read_mem(addr, len, SerialDW.TRGT_FLASH)

    def write_flash(self, data, addr, pages=None):
        if pages is not None:
            data = data[:pages*128]

        # write XYZ registers
        self.write_registers(b'\x03\x01\x05\x40' + int.to_bytes(addr, 2, 'little'), 0x1A)

        # set pc inside boot region (allows spm)
        self._dw_wrt_ctrl_reg_word(SerialDW.CTRL_REG_PC, b'\x1F\x00')

        self._dw_set_cntxt(self.CNTXT_WRT_FLASH, True)  # change context 64 - code execution
        self.exec(MOVW(24, 30)) # saves a copy of the start address to r24:r25
        self.exec(OUT(self.dev.SPMCSR, 26)) # SPMCSR = 0x03 -> flash page erase
        self.exec(SPM(), True)

        assert self.dw_cmd(b'\x83', 1) == b'\x55' # -> set baudrate after reset TODO
        # Erased page @ address

        self._dw_set_cntxt(self.CNTXT_WRT_FLASH)  # change context 44
        # And then repeat the following until the page is full.
        data = [data[i:i+2] for i in range(0, len(data), 2)]
        for i in data:
            self._dw_wrt_ctrl_reg_word(SerialDW.CTRL_REG_PC, b'\x1F\x00') # make spm possible
            self.exec(IN(0, self.dev.DWRD), aux=bytes([i[0]])) # load r0 with low byte
            self.exec(IN(1, self.dev.DWRD), aux=bytes([i[1]])) # load r1 with high byte
            #written value in r0:r1
            #address has been already set in Z before
            self.exec(OUT(self.dev.SPMCSR, 27)) #write SPMCS = 1 --> prepare for buffer fill at [Z]
            self.exec(SPM())
            self.exec(ADIW(3, 2)) #increment Z + 2 (next word)

        self._dw_wrt_ctrl_reg_word(SerialDW.CTRL_REG_PC, b'\x1F\x00')
        self.exec(MOVW(30, 24)) # restore original address after buffer fill
        self.exec(OUT(self.dev.SPMCSR, 28)) # SPMCSR = 5 -> write to page
        self.exec(SPM(), True) #execute page write
        #why not baud reset?

        self._dw_wrt_ctrl_reg_word(SerialDW.CTRL_REG_PC, b'\x1F\x00')
        self.exec(LDI(28, 0x11))
        self.exec(OUT(self.dev.SPMCSR, 28))
        self.exec(SPM(), True)
        assert self.dw_cmd(b'\x83', 1) == b'\x55' #??
        #performs RWWSRE (clears the buffer) IS THIS NOT NECESSARY?

    def exec(self, instruction, long_instruction=False, ret_len=0, aux=b''):
        if type(instruction) is list:
            for i in instruction:
                assert type(i) is bytes
                return self.exec(instruction, long_instruction)
        assert len(instruction) == 2
        return self.dw_cmd(b'\xD2' + instruction + (b'\x23' if not long_instruction else b'\x33') + aux, ret_len if not long_instruction else 2+ret_len)

    def read_eeprom(self, addr, len):
        assert len >= 1
        #can be far more optimized =(
        # read EECR.EEPE to check no write is in progress

        buf = b''
        for i in range(len):
            #set Z (r30 r31) as starting address
            self.write_registers(b'\x01\x01' + int.to_bytes(addr + i, 2, 'little'), 0x1C)
            self._dw_set_cntxt(self.CNTXT_WRT_FLASH, True) #change context
            self.exec(OUT(self.dev.EEARH, 31))
            self.exec(OUT(self.dev.EEARL, 30))
                # ;EEAR EEPROM ADDR REGISTER = Z
            self.exec(OUT(self.dev.EECR, 28))
                # ; EEprom Ctrl Register = 01 YL ==> EERE (EEprom Read enable)
            self.exec(IN(0, self.dev.EEDR))
            self.exec(OUT(self.dev.DWRD, 0))
                # ; send data over dw
            buf += self.read(1)
        return buf

    def write_eeprom(self, data, addr, length=None):
        if length is not None:
            data = data[:length]
        # can be far more optimized =(
        for i in range(len(data)):
            self.write_registers(b'\x04\x02\x01\x01' + int.to_bytes(addr + i, 2, 'little'), 0x1A)
            self._dw_set_cntxt(self.CNTXT_WRT_FLASH, True)  # change context
            self.exec(OUT(self.dev.EEARH, 31))
            self.exec(OUT(self.dev.EEARL, 30))
            self.exec(IN(0, self.dev.DWRD), aux=bytes([data[i]]))
            self.exec(OUT(self.dev.EEDR, 0))
            self.exec(OUT(self.dev.EECR, 26))
            self.exec(OUT(self.dev.EECR, 27))



