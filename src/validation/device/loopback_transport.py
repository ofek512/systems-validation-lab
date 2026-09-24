from validation.device.transport_seam import TransportSeam
from validation.device.fake_firmware import FakeFirmware

class LoopbackTransport(TransportSeam):
    def __init__(self, firmware: FakeFirmware):
        self._isOpen = False
        self._firmware = firmware
        self.pipe = []

    def open(self) -> None:
        self._isOpen = True
        return #Its a fake device, maybe a bool for open or not open so if its closed
               #we cant do operations
    def close(self) -> None:
        self._isOpen = False

    def isOpen(self) -> bool:
        if self._isOpen:
            return True
        return False    

    def write_line(self, text: str) -> None:
        if not self.isOpen():
            raise RuntimeError("transport is not open")
        self.pipe.append(self._firmware.handle_request(text))

    def read_line(self, timeout: float) -> str | None:
        if not self.isOpen():
            raise RuntimeError("transport is not open")
        if not self.pipe:
            raise RuntimeError("no response pending")
        return self.pipe.pop()
