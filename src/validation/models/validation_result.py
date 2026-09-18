from dataclasses import dataclass
from enum import Enum
from typing import Any

class ResultStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"

@dataclass
class ValidationResult:
    test_name: str
    status: ResultStatus
    expected_value: Any
    actual_value: Any
    error_information: str | None = None