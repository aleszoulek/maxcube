class MaxCube(object):
    def __init__(self, address, serial, firmware_version):
        self.address = address
        self.serial = serial
        self.firmware_version = firmware_version

    @classmethod
    def from_dict(cls, data):
        return cls(address=data['rf_address'], serial=data['serial'], firmware_version=data['firmware_version'])

