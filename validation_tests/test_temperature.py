"""Range validation: temperature must stay within the safe operating window."""

from validation.device.fake_hardware import FakeHardware
from validation.models.validation_result import ResultStatus, ValidationResult

MIN_TEMP = 0
MAX_TEMP = 80


def _check_range(test_name: str, actual: float) -> ValidationResult:
    passed = MIN_TEMP <= actual <= MAX_TEMP
    return ValidationResult(
        test_name=test_name,
        status=ResultStatus.PASS if passed else ResultStatus.FAIL,
        expected_value=f"{MIN_TEMP} <= temperature <= {MAX_TEMP}",
        actual_value=actual,
    )


def test_temperature_within_range():
    device = FakeHardware()
    device.connect()

    result = _check_range("test_temperature_within_range", device.get_temperature())

    assert result.status is ResultStatus.PASS, result


def test_temperature_out_of_range_is_detected():
    # relies on inject_temperature, which has no real-device equivalent
    device = FakeHardware()
    device.connect()
    device.inject_temperature(150)

    result = _check_range(
        "test_temperature_out_of_range_is_detected", device.get_temperature()
    )

    assert result.status is ResultStatus.FAIL
