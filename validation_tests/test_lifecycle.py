"""Lifecycle validation: RESET must return the device to its boot state."""

from validation.device.device_interface import DeviceStatus, LedState
from validation.device.fake_hardware import FakeHardware
from validation.models.validation_result import ResultStatus, ValidationResult


def test_reset_restores_boot_state():
    device = FakeHardware()
    device.connect()
    device.set_led(LedState.ON)
    device.inject_status(DeviceStatus.ERROR)

    device.reset()

    checks = {
        "led_state": (device.get_led(), LedState.OFF),
        "status": (device.get_status(), DeviceStatus.READY),
    }

    for name, (actual, expected) in checks.items():
        result = ValidationResult(
            test_name=f"test_reset_restores_boot_state[{name}]",
            status=ResultStatus.PASS if actual is expected else ResultStatus.FAIL,
            expected_value=expected,
            actual_value=actual,
        )
        assert result.status is ResultStatus.PASS, result
