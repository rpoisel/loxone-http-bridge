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


class VirtualInput(object):

    def __init__(self, output):
        self.__last_states = 0x00
        self.__output = output

    @property
    def last_states(self):
        return self.__last_states

    @last_states.setter
    def last_states(self, last_states):
        self.__last_states = last_states

    @property
    def output(self):
        return self.__output


class WriteByteVirtual(Resource):

    outputs = {
        0x00: VirtualInput(
            i2c_io[0x01][0x20]
        )
    }

    def get(self, address, value):
        address = int(address, 16)
        if address not in WriteByteVirtual.outputs:
            return {'error': 'Virtual IO not found.'}
        vInput = WriteByteVirtual.outputs[address]
        value = int(value, 16)

        changing_states = (value & (~vInput.last_states & 0xff))

        if changing_states != 0x00:
            vInput.output.flipBits(changing_states)
        vInput.last_states = value

        return {'output': vInput.output.value}

api.add_resource(WritePcf8574,
                 '/physical/0x<string:bus_id>/0x<string:address>/0x<string:value>')
api.add_resource(ReadPcf8574,
                 '/physical/0x<string:bus_id>/0x<string:address>')
api.add_resource(WriteByteVirtual,
                 '/virtual/0x<string:address>/0x<string:value>')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

