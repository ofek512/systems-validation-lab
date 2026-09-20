"""Unit tests for FakeHardware's own state machine (framework code, not the DUT)."""

import pytest

from validation.device.device_interface import (
    DeviceNotConnectedError,
    DeviceStatus,
    LedState,
)
from validation.device.fake_hardware import FakeHardware


def test_starts_disconnected():
    device = FakeHardware()
    assert device.is_connected() is False


def test_connect_sets_connected_state():
    device = FakeHardware()
    device.connect()
    assert device.is_connected() is True


def test_disconnect_clears_connected_state():
    device = FakeHardware()
    device.connect()
    device.disconnect()
    assert device.is_connected() is False


@pytest.mark.parametrize(
    "method",
    [
        FakeHardware.ping,
        FakeHardware.get_status,
        FakeHardware.get_version,
        FakeHardware.get_temperature,
        FakeHardware.get_led,
        FakeHardware.reset,
    ],
)
def test_operations_raise_when_disconnected(method):
    device = FakeHardware()
    with pytest.raises(DeviceNotConnectedError):
        method(device)


def test_set_led_raises_when_disconnected():
    device = FakeHardware()
    with pytest.raises(DeviceNotConnectedError):
        device.set_led(LedState.ON)


def test_reset_restores_led_and_status():
    device = FakeHardware()
    device.connect()
    device.set_led(LedState.ON)
    device.inject_status(DeviceStatus.ERROR)

    device.reset()

    assert device.get_led() is LedState.OFF
    assert device.get_status() is DeviceStatus.READY


def test_reset_increments_boot_count():
    device = FakeHardware()
    device.connect()

    before = device.boot_count
    device.reset()

    assert device.boot_count == before + 1


def test_inject_temperature_overrides_reading():
    device = FakeHardware()
    device.connect()

    device.inject_temperature(150)

    assert device.get_temperature() == 150


def test_inject_version_overrides_reading():
    device = FakeHardware()
    device.connect()

    device.inject_version("9.9.9")

    assert device.get_version() == "9.9.9"
