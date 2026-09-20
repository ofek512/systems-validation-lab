"""Health check: device must report READY under normal operation."""

from validation.device.device_interface import DeviceStatus
from validation.device.fake_hardware import FakeHardware
from validation.models.validation_result import ResultStatus, ValidationResult


def test_status_is_ready_after_connect():
    device = FakeHardware()
    device.connect()

    expected = DeviceStatus.READY
    actual = device.get_status()

    result = ValidationResult(
        test_name="test_status_is_ready_after_connect",
        status=ResultStatus.PASS if actual is expected else ResultStatus.FAIL,
        expected_value=expected,
        actual_value=actual,
    )

    assert result.status is ResultStatus.PASS, result


def test_error_status_is_detected():
    # relies on inject_status, which has no real-device equivalent
    device = FakeHardware()
    device.connect()
    device.inject_status(DeviceStatus.ERROR)

    expected = DeviceStatus.READY
    actual = device.get_status()

    result = ValidationResult(
        test_name="test_error_status_is_detected",
        status=ResultStatus.PASS if actual is expected else ResultStatus.FAIL,
        expected_value=expected,
        actual_value=actual,
    )

    assert result.status is ResultStatus.FAIL
