"""Metadata validation: firmware version must match the expected release."""

from validation.device.fake_hardware import FakeHardware
from validation.models.validation_result import ResultStatus, ValidationResult


def test_version_matches_expected_release():
    device = FakeHardware(firmware_version="1.2.0")
    device.connect()

    expected = "1.2.0"
    actual = device.get_version()

    result = ValidationResult(
        test_name="test_version_matches_expected_release",
        status=ResultStatus.PASS if actual == expected else ResultStatus.FAIL,
        expected_value=expected,
        actual_value=actual,
    )

    assert result.status is ResultStatus.PASS, result


def test_wrong_version_is_detected():
    device = FakeHardware(firmware_version="1.1.0")
    device.connect()

    expected = "1.2.0"
    actual = device.get_version()

    result = ValidationResult(
        test_name="test_wrong_version_is_detected",
        status=ResultStatus.PASS if actual == expected else ResultStatus.FAIL,
        expected_value=expected,
        actual_value=actual,
    )

    assert result.status is ResultStatus.FAIL
