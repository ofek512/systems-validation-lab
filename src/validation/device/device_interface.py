from abc import ABC, abstractmethod
from enum import Enum

class LedState(Enum):
    OFF = "OFF"
    ON = "ON"


class DeviceStatus(Enum):
    READY = "READY"
    ERROR = "ERROR"

class DeviceError(Exception):
    """Base for failures reported to validation"""

class DeviceNotConnectedError(DeviceError):
    pass

class InvalidCommandError(DeviceError):
    pass

class DeviceInterface(ABC):
    @abstractmethod
    def connect(self) -> None:
        ...
    @abstractmethod
    def disconnect(self) -> None:
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        ...
    
    @abstractmethod
    def ping(self) -> str:
        ...
    @abstractmethod
    def get_version(self) -> str:
        ...
    @abstractmethod
    def get_status(self) -> DeviceStatus:
        ...
    @abstractmethod
    def get_temperature(self) -> float:
        ...
    @abstractmethod
    def set_led(self, state: LedState) -> None:
        ...
    @abstractmethod
    def get_led(self) -> LedState:
        ...
    @abstractmethod
    def reset(self) -> None:
        ...