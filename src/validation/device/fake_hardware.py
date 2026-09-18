# Need to implement:
# !PING !GET_VERSION, !GET_STATUS !GET_TEMP !SET_LED <0|1> !GET_LED !RESET
# firmware_version
# temperature
# led_state
# status READY or ERROR

from validation.device.device_interface import DeviceInterface, LedState, DeviceStatus, DeviceNotConnectedError, InvalidCommandError
from enum import Enum

class FakeHardware(DeviceInterface):

    def __init__(self, firmware_version="1.0"):
        self.firmware_version = firmware_version
        self.temp = 36
        self.led_state = LedState.OFF
        self.connection = False
        self.status = DeviceStatus.READY
        self.pong = "PONG"
        self.boot_count = 0

    def connect(self) -> None:
        self.connection = True

    def disconnect(self) -> None:
        self.connection = False

    def is_connected(self) -> bool:
        return self.connection
    
    def ping(self) -> str:
        if not self.connection:
            raise DeviceNotConnectedError("device is not connected")
        return self.pong

    def get_status(self) -> DeviceStatus:
        if not self.connection:
            raise DeviceNotConnectedError("device is not connected")
        return self.status

    def get_version(self) -> str:
        if not self.connection:
            raise DeviceNotConnectedError("device is not connected")
        return self.firmware_version

    def get_temperature(self) -> float:
        if not self.connection:
            raise DeviceNotConnectedError("device is not connected")
        return self.temp

    def get_led(self) -> LedState:
        if not self.connection:
            raise DeviceNotConnectedError("device is not connected")
        return self.led_state

    def set_led(self, state: LedState) -> None:
        if not self.connection:
            raise DeviceNotConnectedError("device is not connected")
        if not isinstance(state, LedState):
            raise InvalidCommandError(f"expected LedState, got {state!r}")
        self.led_state = state

    def reset(self) -> None:
        if not self.is_connected():
            raise DeviceNotConnectedError("device is not connected")
        self.led_state = LedState.OFF
        self.status = DeviceStatus.READY
        self.boot_count += 1

    def inject_temperature(self, value: float) -> None:
        self.temp = value

    def inject_status(self, status: DeviceStatus) -> None:
        self.status = status

    def inject_version(self, version: str) -> None:
        self.firmware_version = version
    
