"""State-change validation: SET_LED must be observable via GET_LED."""

import pytest

from validation.device.device_interface import InvalidCommandError, LedState
from validation.device.fake_hardware import FakeHardware
from validation.models.validation_result import ResultStatus, ValidationResult


def test_led_defaults_to_off():
    device = FakeHardware()
    device.connect()

    expected = LedState.OFF
    actual = device.get_led()

    result = ValidationResult(
        test_name="test_led_defaults_to_off",
        status=ResultStatus.PASS if actual is expected else ResultStatus.FAIL,
        expected_value=expected,
        actual_value=actual,
    )

    assert result.status is ResultStatus.PASS, result


def test_set_led_on_is_reflected_by_get_led():
    device = FakeHardware()
    device.connect()

    device.set_led(LedState.ON)

    expected = LedState.ON
    actual = device.get_led()

    result = ValidationResult(
        test_name="test_set_led_on_is_reflected_by_get_led",
        status=ResultStatus.PASS if actual is expected else ResultStatus.FAIL,
        expected_value=expected,
        actual_value=actual,
    )

    assert result.status is ResultStatus.PASS, result


def test_set_led_rejects_invalid_state():
    device = FakeHardware()
    device.connect()

    with pytest.raises(InvalidCommandError):
        device.set_led(1)  # wire-style int instead of LedState
