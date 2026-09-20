"""Unit tests for the ValidationResult data shape itself."""

from validation.models.validation_result import ResultStatus, ValidationResult


def test_error_information_defaults_to_none():
    result = ValidationResult(
        test_name="dummy",
        status=ResultStatus.PASS,
        expected_value="PONG",
        actual_value="PONG",
    )

    assert result.error_information is None


def test_fields_are_stored_as_given():
    result = ValidationResult(
        test_name="dummy",
        status=ResultStatus.FAIL,
        expected_value="PONG",
        actual_value="INVALID",
        error_information="unexpected reply",
    )

    assert result.status is ResultStatus.FAIL
    assert result.expected_value == "PONG"
    assert result.actual_value == "INVALID"
    assert result.error_information == "unexpected reply"
