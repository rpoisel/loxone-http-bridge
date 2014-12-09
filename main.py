from flask import Flask, request
from flask.ext.restful import Resource, Api
from smbus import SMBus

app = Flask(__name__)
api = Api(app)


class PCF8574(object):

    def __init__(self, bus_id, address):
        super().__init__()
        self.__bus = SMBus(bus_id)
        self.__address = address
        self.__value = self.__getRealValue()

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__bus.write_byte(self.__address,
                              (~value) & 0xff
                              )
        self.__value = value

    def flipBits(self, changeBits):
        self.value ^= changeBits

    def __getRealValue(self):
        value = self.__bus.read_byte(self.__address)
        return (~value) & 0xff


i2c_io = {
        0x01: {
            0x20: PCF8574(0x01, 0x20)
        }
}


class WritePcf8574(Resource):

    def get(self, bus_id, address, value):
        bus_id = int(bus_id, 16)
        address = int(address, 16)
        value = int(value, 16)

        if bus_id in i2c_io and address in i2c_io[bus_id]:
            pcf = i2c_io[bus_id][address]
            pcf.value = value

            return {'bus_id': bus_id,
                    'address': address,
                    'value': value
                    }
        else:
            return {'error': 'IO not found.'}


class ReadPcf8574(Resource):

    def get(self, bus_id, address):
        bus_id = int(bus_id, 16)
        address = int(address, 16)

        if bus_id in i2c_io and address in i2c_io[bus_id]:
            pcf = i2c_io[bus_id][address]

            return {'bus_id': bus_id,
                    'address': address,
                    'value': pcf.value
                    }
        else:
            return {'error': 'IO not found.'}


class WriteByteVirtual(Resource):

    outputs = {
        0x00: i2c_io[0x01][0x20]
    }

    def get(self, address, value):
        address = int(address, 16)
        if address not in WriteByteVirtual.outputs:
            return {'error': 'Virtual IO not found.'}
        vOutput = WriteByteVirtual.outputs[address]
        value = int(value, 16)

        vOutput.value = value

        return {'output': vOutput.value}


class ReadByteVirtual(Resource):

    inputs = {
        0x00: i2c_io[0x01][0x20]
    }

    def get(self, address):
        address = int(address, 16)
        if address not in ReadByteVirtual.inputs:
            return {'error': 'Virtual IO not found.'}
        vInput = ReadByteVirtual.inputs[address]

        return {'input': vInput.value}


api.add_resource(WritePcf8574,
                 '/physical/0x<string:bus_id>/0x<string:address>/0x<string:value>')
api.add_resource(ReadPcf8574,
                 '/physical/0x<string:bus_id>/0x<string:address>')
api.add_resource(WriteByteVirtual,
                 '/virtual/0x<string:address>/0x<string:value>')
api.add_resource(ReadByteVirtual,
                 '/virtual/0x<string:address>')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

