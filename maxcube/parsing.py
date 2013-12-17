import socket
import base64
import binascii
from pprint import pprint
from io import BytesIO
from collections import defaultdict


def handle_output_H(line):
    serial, rf_address, firmware_version, *_ = line.decode().strip().split(',')
    return {
        'serial': serial,
        'rf_address': rf_address,
        'firmware_version': firmware_version,
    }


def handle_output_M(line):
    position = 0
    data = {}
    _1, _2, encoded = line.strip().split(b',', 2)
    decoded = BytesIO(base64.decodebytes(encoded))

    # Unknown bytes
    data['?0'] = ord(decoded.read(1))
    data['?1'] = ord(decoded.read(1))

    # Rooms
    data['room_count'] = ord(decoded.read(1))
    data['rooms'] = {}
    for i in range(data['room_count']):
        room = {}
        room['id'] = ord(decoded.read(1))
        room['name_len'] = ord(decoded.read(1))
        room['name'] = decoded.read(room['name_len'])
        room['rf_address'] = binascii.b2a_hex(decoded.read(3))
        data['rooms'][room['id']] = room

    # Devices
    data['devices_count'] = ord(decoded.read(1))
    data['devices'] = []
    for i in range(data['devices_count']):
        device = {}
        device['type'] = ord(decoded.read(1))
        device['rf_address'] = binascii.b2a_hex(decoded.read(3))
        device['serial'] = decoded.read(10)
        device['name_len'] = ord(decoded.read(1))
        device['name'] = decoded.read(device['name_len'])
        device['room_id'] = ord(decoded.read(1))

        data['devices'].append(device)

    # Unknown byte
    data['?2'] = decoded.read(1)

    return data

def handle_output_C(line):
    data = {}
    prefix, encoded = line.strip().split(b',', 1)
    decoded = BytesIO(base64.decodebytes(encoded))
    data['data_len'] = ord(decoded.read(1))
    data['rf_address'] = binascii.b2a_hex(decoded.read(3))
    data['type'] = ord(decoded.read(1))
    data['?1'] = binascii.b2a_hex(decoded.read(3))
    data['serial'] = decoded.read(10)
    if data['type'] == 2:
        # VALVES
        data['temperature_comfort'] = ord(decoded.read(1)) / 2
        data['temperature_eco'] = ord(decoded.read(1)) / 2
        data['temperature_setpoint_max'] = ord(decoded.read(1)) / 2
        data['temperature_setpoint_min'] = ord(decoded.read(1)) / 2
        data['temperature_offset'] = (ord(decoded.read(1)) / 2) - 3.5
        data['temperature_window_open'] = ord(decoded.read(1)) / 2
        data['duration_window_open'] = ord(decoded.read(1))
        data['duration_boost'] = ord(decoded.read(1)) # TODO
        data['decalcification'] = decoded.read(1) # TODO
        data['valve_maximum'] = ord(decoded.read(1)) * (100 / 255)
        data['valve_offset'] = ord(decoded.read(1)) * (100 / 255)
        data['program'] = decoded.read() # TODO
    return data

def handle_output_L(line):
    data = {}
    encoded = line.strip()
    decoded = BytesIO(base64.decodebytes(encoded))
    data = {}
    while True:
        device = {}
        try:
            device['len'] = ord(decoded.read(1))
        except TypeError:
            break
        device['rf_address'] = binascii.b2a_hex(decoded.read(3))
        device['?1'] = ord(decoded.read(1))
        device['flags_1'] = ord(decoded.read(1)) # TODO
        device['flags_2'] = ord(decoded.read(1)) # TODO
        if device['len'] > 6:
            device['valve_position'] = ord(decoded.read(1)) # TODO ? in perc?
            device['temperature_setpoint'] = ord(decoded.read(1)) / 2
            device['date_until'] = decoded.read(2)
            device['time_until'] = decoded.read(1)
        data[device['rf_address']] = device
    return data

def handle_output_default(line):
    print('handling default')
    print(line)

OUTPUT_SIGNATURES = {
    b'H:': handle_output_H,
    b'M:': handle_output_M,
    b'C:': handle_output_C,
    b'L:': handle_output_L,
}
DEFAULT_OUTPUT = handle_output_default

def handle_output(line):
    if not line:
        return None, None
    func = OUTPUT_SIGNATURES.get(line[:2], DEFAULT_OUTPUT)
    return line.decode()[0], func(line[2:])

def start(host, port):
    port = int(port)
    print('Connecting to %s:%s' % (host, port))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.settimeout(2)
    got = b''
    out = defaultdict(list)
    while True:
        try:
            got += s.recv(100000)
        except socket.timeout:
            break
    for line in got.split(b'\r\n'):
        key, value = handle_output(line)
        if not key:
            continue
        out[key].append(value)
    return out

