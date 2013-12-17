import sys
import socket
import base64
import binascii
from pprint import pprint
from io import BytesIO

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
        return
    func = OUTPUT_SIGNATURES.get(line[:2], DEFAULT_OUTPUT)
    return func(line[2:])

def start(host, port):
    port = int(port)
    print('Connecting to %s:%s' % (host, port))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.settimeout(2)
    got = b''
    while True:
        try:
            got += s.recv(100000)
        except socket.timeout:
            break
    for line in got.split(b'\r\n'):
        handle_output(line)

if __name__ == '__main__':

    assert handle_output_H(
        b'JEQ0543545,03f6c9,0113,00000000,2663651e,00,32,0d0c0f,000c,03,0000\r\n',
    ) == {
        'firmware_version': '0113',
        'rf_address': '03f6c9',
        'serial': 'JEQ0543545',
    }

    assert handle_output_M(
        b'00,01,VgICAg1PYnl2YWNpIHBva29qCLbSAQdQcmVkc2luCwS+AwILBL5LRVEwNTcxNjc0C3RvcGVuaSB1IHdjAQIIttJLRVEwNjM0NjA3CVBvZCBva25lbQIFAbSRSkVRMDMwNTIwNQpFY28gU3dpdGNoAAE=\r\n'
    ) == {
        '?0': 86,
        '?1': 2,
        'room_count': 2,
        'rooms': {
            1: {
                'id': 1,
                'name': b'Predsin',
                'name_len': 7,
                'rf_address': b'0b04be',
            },
            2: {
                'id': 2,
                'name': b'Obyvaci pokoj',
                'name_len': 13,
                'rf_address': b'08b6d2',
            }
        },
        'devices_count': 3,
        'devices': [
            {
                'name': b'topeni u wc',
                'name_len': 11,
                'rf_address': b'0b04be',
                'room_id': 1,
                'serial': b'KEQ0571674',
                'type': 2,
            }, {
                'name': b'Pod oknem',
                'name_len': 9,
                'rf_address': b'08b6d2',
                'room_id': 2,
                'serial': b'KEQ0634607',
                'type': 2,
            }, {
                'name': b'Eco Switch',
                'name_len': 10,
                'rf_address': b'01b491',
                'room_id': 0,
                'serial': b'JEQ0305205',
                'type': 5,
            }
        ],
        '?2': b'\x01',

    }

    assert handle_output_C(
        b'03f6c9,7QP2yQATAf9KRVEwNTQzNTQ1AQsABEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAsABEAAAAAAAAAAQQAAAAAAAAAAAAAAAAAAAAAAAAAAAGh0dHA6Ly93d3cubWF4LXBvcnRhbC5lbHYuZGU6ODAvY3ViZQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAENFVAAACgADAAAOEENFU1QAAwACAAAcIA==\r\n'
    ) == {
        '?1': b'1301ff',
        'data_len': 237,
        'rf_address': b'03f6c9',
        'serial': b'JEQ0543545',
        'type': 0
    }

    assert handle_output_C(
        b'0b04be,0gsEvgIBEP9LRVEwNTcxNjc0LCE9CQcYA1CH/wBETlxmWPxVFEUgRSBFIEUgRSBFIEUgRSBFIEROXGZY/FUURSBFIEUgRSBFIEUgRSBFIEUgRE5cZlj8VRRFIEUgRSBFIEUgRSBFIEUgRSBETlxmWPxVFEUgRSBFIEUgRSBFIEUgRSBFIEROXGZY/FUURSBFIEUgRSBFIEUgRSBFIEUgRE5cZlj8VRRFIEUgRSBFIEUgRSBFIEUgRSBETlxmWPxVFEUgRSBFIEUgRSBFIEUgRSBFIA==',
    ) == {
        '?1': b'0110ff',
        'data_len': 210,
        'decalcification': b'\x87',
        'duration_boost': 80,
        'duration_window_open': 3,
        'program': b'DN\\fX\xfcU\x14E E E E E E E E E DN\\fX\xfcU\x14E E E E E E E E E DN\\fX\xfcU\x14E E E E E E E E E DN\\fX\xfcU\x14E E E E E E E E E DN\\fX\xfcU\x14E E E E E E E E E DN\\fX\xfcU\x14E E E E E E E E E DN\\fX\xfcU\x14E E E E E E E E E ',
        'rf_address': b'0b04be',
        'serial': b'KEQ0571674',
        'temperature_comfort': 22.0,
        'temperature_eco': 16.5,
        'temperature_offset': 0.0,
        'temperature_setpoint_max': 30.5,
        'temperature_setpoint_min': 4.5,
        'temperature_window_open': 12.0,
        'type': 2,
        'valve_maximum': 100.0,
        'valve_offset': 0.0,
    }

    assert handle_output_C(
        b'08b6d2,0gi20gICEABLRVEwNjM0NjA3LiE9CQcYA1AM/wBETlxmWwhVFEUgRSBFIEUgRSBFIEUgRSBFIEROXGZbCFUURSBFIEUgRSBFIEUgRSBFIEUgRE5cZlsIVRRFIEUgRSBFIEUgRSBFIEUgRSBETlxmWwhVFEUgRSBFIEUgRSBFIEUgRSBFIEROXGZbCFUURSBFIEUgRSBFIEUgRSBFIEUgRE5cZlsIVRRFIEUgRSBFIEUgRSBFIEUgRSBETlxmWwhVFEUgRSBFIEUgRSBFIEUgRSBFIA=='
    ) == {
        '?1': b'021000',
        'data_len': 210,
        'decalcification': b'\x0c',
        'duration_boost': 80,
        'duration_window_open': 3,
        'program': b'DN\\f[\x08U\x14E E E E E E E E E DN\\f[\x08U\x14E E E E E E E E E DN\\f[\x08U\x14E E E E E E E E E DN\\f[\x08U\x14E E E E E E E E E DN\\f[\x08U\x14E E E E E E E E E DN\\f[\x08U\x14E E E E E E E E E DN\\f[\x08U\x14E E E E E E E E E ',
        'rf_address': b'08b6d2',
        'serial': b'KEQ0634607',
        'temperature_comfort': 23.0,
        'temperature_eco': 16.5,
        'temperature_offset': 0.0,
        'temperature_setpoint_max': 30.5,
        'temperature_setpoint_min': 4.5,
        'temperature_window_open': 12.0,
        'type': 2,
        'valve_maximum': 100.0,
        'valve_offset': 0.0,
    }

    assert handle_output_C(
        b'C:01b491,EQG0kQUAEg9KRVEwMzA1MjA1'
    ) == {
        '?1': b'00120f',
        'data_len': 17,
        'rf_address': b'01b491',
        'serial': b'JEQ0305205',
        'type': 5
    }

    assert handle_output_L(
        b'CwsEvvYSGAAiANsACwi20lwSGAAiAOEABgG0kVwSEF=='
    ) == {
        b'01b491': {
            '?1': 92,
            'flags_1': 18,
            'flags_2': 16,
            'len': 6,
            'rf_address': b'01b491',
        },
        b'08b6d2': {
            '?1': 92,
            'date_until': b'\x00\xe1',
            'flags_1': 18,
            'flags_2': 24,
            'len': 11,
            'rf_address': b'08b6d2',
            'temperature_setpoint': 17.0,
            'time_until': b'\x00',
            'valve_position': 0,
        },
        b'0b04be': {
            '?1': 246,
            'date_until': b'\x00\xdb',
            'flags_1': 18,
            'flags_2': 24,
            'len': 11,
            'rf_address': b'0b04be',
            'temperature_setpoint': 17.0,
            'time_until': b'\x00',
            'valve_position': 0,
        },
    }
