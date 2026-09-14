# Need to implement:
# !PING !GET_VERSION, !GET_STATUS !GET_TEMP !SET_LED <0|1> !GET_LED !RESET
# firmware_version
# temperature
# led_state
# status READY or ERROR

class FakeHardware:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, firmware_version=1):
        if not hasattr(self, "_initialized"):
            self.firmware_version = firmware_version
            self.temp = 36
            self.led_state = 0
            self.status = "READY"
            self.pong = "PONG"

            self._initialized = True

    def ping(self):
        return self.pong

    def get_status(self):
        return self.status

    def get_version(self):
        return self.firmware_version

    def get_temp(self):
        return self.temp

    def get_led(self):
        return self.led_state

    def set_led(self, state=0):
        if state != 0 or state != 1:
            print("Invalid state number. Exiting")
            return
        self.led_state = state

    def reset(self):
        #No idea what this will do here
        return
    
