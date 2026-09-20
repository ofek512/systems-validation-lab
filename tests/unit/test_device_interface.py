"""Unit tests proving the ABC enforces the full device contract."""

import pytest

from validation.device.device_interface import DeviceInterface


def test_cannot_instantiate_interface_directly():
    with pytest.raises(TypeError):
        DeviceInterface()


def test_incomplete_implementation_cannot_be_instantiated():
    class IncompleteDevice(DeviceInterface):
        def connect(self) -> None:
            ...
        # every other abstract method is intentionally left unimplemented

    with pytest.raises(TypeError):
        IncompleteDevice()
