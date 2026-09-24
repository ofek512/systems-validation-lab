from abc import ABC, abstractmethod


class TransportSeam(ABC):
    """Interface for implementations from fakeFirmware of actual ESP32"""
    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def write_line(self, text: str) -> None:
        ...

    @abstractmethod
    def read_line(self, timeout: float) -> str:
        ...
