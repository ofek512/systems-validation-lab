"""Stateless request/response behavior, and the device-unavailable failure scenario."""

import pytest

from validation.device.device_interface import DeviceNotConnectedError
from validation.device.fake_hardware import FakeHardware
from validation.models.validation_result import ResultStatus, ValidationResult


def test_ping_returns_pong():
    device = FakeHardware()
    device.connect()

    expected = "PONG"
    actual = device.ping()

    result = ValidationResult(
        test_name="test_ping_returns_pong",
        status=ResultStatus.PASS if actual == expected else ResultStatus.FAIL,
        expected_value=expected,
        actual_value=actual,
    )

    assert result.status is ResultStatus.PASS, result


def test_ping_when_disconnected_raises():
    device = FakeHardware()  # never connected

    with pytest.raises(DeviceNotConnectedError):
        device.ping()
