class MaxCube(object):
    def __init__(self, address, serial, firmware_version):
        self.address = address
        self.serial = serial
        self.firmware_version = firmware_version
        self.rooms = {}
        self.devices = []

    def add_room(self, room):
        self.rooms[room.id] = room
        room.cube = self

    def add_device(self, device):
        self.devices.append(device)
        device.cube = self
        if device.room_id:
            self.rooms[device.room_id].add_device(device)


class Room(object):
    def __init__(self, id, address, name):
        self.id = id
        self.address = address
        self.name = name
        self.cube = None
        self.devices = []

    def add_device(self, device):
        self.devices.append(device)
        device.room = self


class Device(object):
    def __init__(self, address, serial, room_id, name):
        self.address = address
        self.serial = serial
        self.room_id = room_id
        self.name = name
        cube = None
        room = None

    @classmethod
    def get_device_type(cls, type_code):
        return {c.type_code: c for c in cls.__subclasses__()}.get(type_code, cls)

    @classmethod
    def from_dict(cls, data):
        return cls(address=data['rf_address'], serial=data['serial'], room_id=data['room_id'], name=data['name'])


class Valve(Device):
    type_code = 2


class Switch(Device):
    type_code = 5


class WindowSensor(Device):
    type_code = 4


def from_parsed_data(data):
    print(data)
    header = data['H'][0]
    meta = data['M'][0]
    cube = MaxCube(address=header['rf_address'], serial=header['serial'], firmware_version=header['firmware_version'])
    for room in meta['rooms'].values():
        cube.add_room(Room(id=room['id'], address=room['rf_address'], name=room['name']))
    for device in meta['devices']:
        klass = Device.get_device_type(device['type'])
        cube.add_device(klass.from_dict(device))
    return cube

