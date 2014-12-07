from flask import Flask, request
from flask.ext.restful import Resource, Api
from smbus import SMBus

app = Flask(__name__)
api = Api(app)


class PCF8574(object):

    def __init__(self, bus_id, address, value=0x00):
        super().__init__()
        self.__bus = SMBus(bus_id)
        self.__address = address
        self.__value = 0
        self.value = value

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


class WriteByteI2C(Resource):
    def get(self, bus_id, address, value):
        bus_id = int(bus_id, 16)
        address = int(address, 16)
        value = int(value, 16)

        PCF8574(bus_id, address, value)

        return {'bus_id': bus_id,
                'address': address,
                'value': value
                }


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
            PCF8574(1, 0x20)
        )
    }

    def get(self, address, value):
        address = int(address, 16)
        if address not in WriteByteVirtual.outputs:
            return {}
        vInput = WriteByteVirtual.outputs[address]
        value = int(value, 16)

        changing_states = (value & (~vInput.last_states & 0xff))

        vInput.output.flipBits(changing_states)
        vInput.last_states = value

        return {'output': vInput.output.value
                }

api.add_resource(WriteByteI2C,
                 '/physical/0x<string:bus_id>/0x<string:address>/0x<string:value>')
api.add_resource(WriteByteVirtual,
                 '/virtual/0x<string:address>/0x<string:value>')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

