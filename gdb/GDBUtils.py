from socket import socket

def escape(data: bytes):
    ret = b''
    checksum = 0
    for c in data:
        if bytes([c]) in [b'#', b'$', b'}']:
            ret += b'}' + bytes([c ^ 0x20])
            checksum += 125 + c ^ 0x20
        else:
            ret += bytes([c])
            checksum += c
    return ret, checksum % 256


def unescape(data: bytes):
    ret = b''
    escape = False
    checksum = 0
    data_checksum = 0
    for c in data:
        checksum += c
        if bytes([c]) == b'}':
            escape = True
            continue
        if escape:
            c = c ^ 0x20
            escape = False
        ret += bytes([c])
        data_checksum += c
    return ret, checksum % 256, data_checksum % 256


def read_packet(sok: socket, interrupt):
    r = sok.recv(1)
    while r != b'$':
        if r == b'\x03' and interrupt is not None:
            interrupt(sok)
            return None
        r = sok.recv(1)
    data = sok.recv(1)
    while not data.endswith(b'#'):
        data += sok.recv(1)
    checksum = int(sok.recv(2), 16)
    data, packet_checksum, data_checksum = unescape(data[:-1])
    if checksum != packet_checksum:
        print(f"Wrong packet checksum {data} {checksum} {packet_checksum}")
        answer(sok, None, False)
        return None
    print(f"<- {data}")
    return data


def answer(sok: socket, state, data=b"", success=True):
    packet = b''
    if success is not None:
        sok.send(b'+' if success else b'-')
    if not state["ack"]:
        success = None

    if data is not None:
        send_data, checksum = escape(data)
        packet = b'$' + send_data + b'#' + ('0' + hex(checksum)[2:])[-2:].encode()
        sok.send(packet)
    print(f"-> {'+' if success else '-' if success is not None else ''} {packet}")