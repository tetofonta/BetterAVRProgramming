import os
from binascii import hexlify
from functools import partial
from math import ceil

from serial import Serial
from tqdm import tqdm

from dwire import *
from dwire.SerialDW import SerialDW #todo abstraction of this class
from dwire.avr import REG_Z, REG_Y, REG_X, BREAK, FLASH_INSTRUCTION


def FLASH_PAGE(pages):
    return pages * 128


def INST_ADDR(memory_address):
    return int(memory_address/2)


def _preserve_ctrl_register(reg, function):
    def _preserve_register(self, *args, **kwargs):
        v = self.device._dw_read_ctrl_reg_word(reg)
        ret = function(self, *args, **kwargs)
        self.device._dw_wrt_ctrl_reg_word(reg, v)
        return ret
    return _preserve_register


def preserve_register(reg, length=1):
    def _preserve_register(function):
        def __preserve_register(self, *args, **kwargs):
            v = self.device.read_registers(reg, reg + length)
            ret = function(self, *args, **kwargs)
            self.device.write_registers(v, reg)
            return ret
        return __preserve_register
    return _preserve_register


def preserve_pc(function):
    return _preserve_ctrl_register(CTRL_REG_PC, function)


def preserve_hwbp(function):
    return _preserve_ctrl_register(CTRL_REG_HWBP, function)


def preserve_ir(function):
    return _preserve_ctrl_register(CTRL_REG_IR, function)


def halted(function):
    def _halted(self, *args, **kwargs):
        if self.device.is_running:
            raise SystemError("Target has to be halted")
        return function(self, *args, **kwargs)
    return _halted


def running(function):
    def _running(self, *args, **kwargs):
        if not self.device.is_running:
            raise SystemError("Target has to be running")
        return function(self, *args, **kwargs)
    return _running


class DWInterface:
    def __init__(self, device: SerialDW):
        self.device = device
        self.cur_pc = b'\x00\x00' #the effective value of the program counter
        self.sw_breakpoints = {} #dict address -> instruction

    def halt(self):
        """
        halt the cpu by sending a break. saves the current program counter value (effective).
        :return:
        """
        self.device._dw_cmd_break()
        self.breaked = True
        self.cur_pc = self.device._dw_read_ctrl_reg_word(CTRL_REG_PC)
        print(f"MCU Break. PC={hexlify(self.cur_pc).decode()}")

    @halted
    def resume_execution(self, cntxt=CNTXT_GO_INDEFINITLY, pc=None, rel=False):
        """
        Resumes code execution. the context tells how to deal with breakpoints
        (mainly CNTXT_GO_INDEFINITLY and CNTXT_GO_TO_HW_BREAKPOINT), and the pc is the address
        where to resume code execution.
        :param cntxt:
        :param pc: is the absolute address (if bytes or positive int with rel=False) or the relative address
        :rel: if pc is int, it will be treated as a relative increment added to the current pc stored
        :return:
        """
        pc_value = pc if pc is not None else self.cur_pc

        if type(pc_value) is int and (pc_value < 0 or rel):
            pc_value = int.from_bytes(self.cur_pc, 'big') + pc

        if type(pc_value) is int:
            pc_value = int.to_bytes(pc_value, 2, 'big')

        print(f"Resuming execution. PC={hexlify(pc_value).decode()}")
        if self.halt_reason() == 'swbreak':
            self.device.load_instruction(FLASH_INSTRUCTION(self.sw_breakpoints[(int.from_bytes(self.cur_pc, 'big')*2)-2]))
            self.device.resume_execution(pc_value, cntxt, False, cmd=CONTINUE_WITH_LOADED_INST)
        else:
            self.device.resume_execution(pc_value, cntxt, False, cmd=CONTINUE)
        self.cur_pc = pc_value

    def restart_execution(self, resume=True, context=CNTXT_GO_INDEFINITLY):
        """
        restarts the execution after a full reset.
        if the device is running, it will break the execution and then reset.
        :param resume: if true code execution will restart
        :context: the context to resume after restart. ???
        :return:
        """
        if self.device.is_running:
            print("Halting the MCU")
            self.device._dw_cmd_break()

        self.device._dw_cmd_reset()
        self.cur_pc = self.device._dw_read_ctrl_reg_word(CTRL_REG_PC)
        print(f"PC Reset Value={hexlify(self.cur_pc).decode()}")
        if resume:
            print(f"Resuming execution.")
            self.device.resume_execution(None, context, False)

    def step_out(self, timeout=None, wait=True):
        """
        ?
        :param timeout:
        :param wait:
        :return:
        """
        self.resume_execution(CNTXT_STEP_OUT)
        if wait:
            self.wait_hit(timeout)

    @halted
    def set_hw_breakpoint(self, address: int):
        """
        sets the hw breakpoint.
        used for step over execution.
        NB after a breakpoint hit, PC increments onece more and should be decremented before resuming.
        :param address:
        :return:
        """
        if type(address) is int:
            address = int.to_bytes(address, 2, 'big')
        self.device._dw_wrt_ctrl_reg_word(CTRL_REG_HWBP, address)
        print(f"Set hw-breakpoint to {hexlify(address).decode()}")

    @halted
    def set_sw_breakpoint(self, address: int):
        """
        :param address: memory address (not instruction address)
        :return:
        """
        page_idx = int(address / self.device.dev.FLASH_PAGEEND)
        offset = address % self.device.dev.FLASH_PAGEEND
        page = self.read_flash(self.device.dev.FLASH_PAGEEND * page_idx, self.device.dev.FLASH_PAGEEND)
        instruction = page[offset:offset + 2]
        page = page[0: offset] + FLASH_INSTRUCTION(BREAK()) + page[offset + 2:]
        self.write_flash_page(self.device.dev.FLASH_PAGEEND * page_idx, page)
        self.sw_breakpoints[address] = instruction
        print(f"Breakpoint set substituting instruction {instruction}@{hex(address)}")

    @halted
    def remove_sw_breakpoint(self, address: int):
        """
        :param address: memory address (not instruction address)
        :return:
        """
        page_idx = int(address/self.device.dev.FLASH_PAGEEND)
        offset = address % self.device.dev.FLASH_PAGEEND
        page = self.read_flash(self.device.dev.FLASH_PAGEEND*page_idx, self.device.dev.FLASH_PAGEEND)
        assert page[offset:offset+2] == b'\x98\x95'
        instruction = self.sw_breakpoints[address]
        page = page[0: offset] + instruction + page[offset+2:]
        self.write_flash_page(self.device.dev.FLASH_PAGEEND*page_idx, page)
        self.sw_breakpoints.pop(address)
        print(f"Breakpoint set substituting instruction {instruction}@{hex(address)}")

    @running
    def wait_hit(self, timeout=None):
        """
        waits for a break coming from the device
        :param timeout:
        :return:
        """
        t = self.device.timeout
        self.device.timeout = timeout
        assert self.device.read(2) == b'\x00\x55'
        self.device.timeout = t
        self.device.is_running = False
        self.cur_pc = self.device._dw_read_ctrl_reg_word(CTRL_REG_PC)

    @halted
    def set_com_divisor(self, divisor: int):
        self.device._dw_cmd_set_baud_rate(2**divisor)
        print(f"Set transmission throughput to {int(self.device.target_freq/self.device.divisor)} baud")

    @halted
    def get_fingerprint(self):
        return self.device._dw_cmd_fingerprint()
    
    @halted
    def step(self):
        # TODO slow loaded instruction?
        return self.device._dw_cmd_single_step()

    @halted
    @preserve_pc
    @preserve_hwbp
    def read_registers(self, register: int, length=1):
        return self.device.read_registers(register, register+length)

    @halted
    @preserve_pc
    @preserve_hwbp
    def write_register(self, register: int, data:bytes, length=None):
        return self.device.write_registers(data, register, length)

    @halted
    @preserve_pc
    @preserve_hwbp
    @preserve_register(REG_Z, 2)
    def read_sram(self, address: int, len: int):
        return self.device.read_sram(address, len)

    @halted
    @preserve_pc
    @preserve_hwbp
    @preserve_register(REG_Z, 2)
    def write_sram(self, address: int, data: bytes, length=None):
        self.device.write_sram(data, address, length)

    @halted
    @preserve_pc
    @preserve_hwbp
    @preserve_register(REG_Y, 4)
    @preserve_register(0)
    def read_eeprom(self, address: int, len: int):
        return self.device.read_eeprom(address, len)

    @halted
    @preserve_pc
    @preserve_hwbp
    @preserve_register(REG_X, 6)
    @preserve_register(0)
    def write_eeprom(self, address: int, data: bytes, length=None):
        return self.device.write_eeprom(data, address, length)

    @halted
    @preserve_pc
    @preserve_hwbp
    @preserve_register(REG_Z, 2)
    def read_flash(self, address: int, len = None):
        if len is None:
            len = self.device.dev.FLASH_PAGEEND
        return self.device.read_flash(address, len)

    @halted
    @preserve_pc
    @preserve_hwbp
    @preserve_register(24, 8)
    @preserve_register(0, 2)
    def write_flash_page(self, address, data, progress=True):
        assert len(data) == self.device.dev.FLASH_PAGEEND
        self.device.write_flash_page(data, address, progress=progress)

    @halted
    @preserve_pc
    @preserve_hwbp
    @preserve_register(24, 8)
    @preserve_register(0, 2)
    def clear_flash_page(self, address):
        self.device.clear_flash_page(address)

    def close(self):
        for k in list(self.sw_breakpoints.keys()):
            self.remove_sw_breakpoint(k)
        self.device.close()

    def status(self):
        return self.device.is_running

    @halted
    def get_pc(self):
        return int.from_bytes(self.device._dw_read_ctrl_reg_word(CTRL_REG_PC), 'big')

    @halted
    def halt_reason(self):
        if (int.from_bytes(self.cur_pc, 'big')*2)-2 in self.sw_breakpoints:
            return "swbreak"
        if int.from_bytes(self.device._dw_read_ctrl_reg_word(CTRL_REG_HWBP), 'big') == int.from_bytes(self.cur_pc, 'big') - 1:
            #pc increments one more
            return "hwbreak"
        return "unknown"

    @halted
    @preserve_pc
    @preserve_hwbp
    @preserve_register(24, 8)
    @preserve_register(0, 2)
    def write_firmware(self, file, verify=True, erease_device=False, debug=False):
        firmware_pages = []
        with open(file, 'rb') as fw:
            while True:
                page = fw.read(self.device.dev.FLASH_PAGEEND)
                if not page:
                    break
                page = page + bytes([0xff] * (self.device.dev.FLASH_PAGEEND - len(page)))
                firmware_pages.append(page)

        if erease_device:
            print("Clearing device")
            for i in tqdm(range(0, int(self.device.dev.FLASH_SIZE), self.device.dev.FLASH_PAGEEND)):
                self.device.clear_flash_page(i)

        addr = 0x00
        for i in firmware_pages:
            if debug:
                print(f"Writing addr={addr}\t\tdata={i}")
            print(f"page {int(addr/64)+1}/{len(firmware_pages)}", end='')
            self.device.write_flash_page(i, addr, progress=True)
            addr += self.device.dev.FLASH_PAGEEND

        if verify:
            addr = 0
            print("Verifying...")
            for i in tqdm(firmware_pages):
                page = self.read_flash(addr)
                addr += self.device.dev.FLASH_PAGEEND
                assert i == page

