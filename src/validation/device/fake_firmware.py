from validation.device.device_interface import LedState, DeviceStatus, InvalidCommandError
from enum import Enum

class FakeFirmware():
    # commands not listed here take no argument; any parsed arg for them is dropped
    _COMMANDS_WITH_ARG = frozenset({"SET_LED"})
    # value-response commands and their wire tag; PING/SET_LED/RESET are special-cased below
    _TAGS = {
        "GET_VERSION": "VERSION",
        "GET_STATUS": "STATUS",
        "GET_TEMPERATURE": "TEMP",
        "GET_LED": "LED",
    }

    def __init__(self, firmware_version="1.0"):
        self.firmware_version = firmware_version
        self.temp = 36
        self.led_state = LedState.OFF
        self.status = DeviceStatus.READY
        self.pong = "PONG"
        self.boot_count = 0

        self._handlers = {
            "PING": self._handle_ping,
            "GET_VERSION": self._handle_get_version,
            "GET_STATUS": self._handle_get_status,
            "GET_TEMPERATURE": self._handle_get_temperature,
            "SET_LED": self._handle_set_led,
            "GET_LED": self._handle_get_led,
            "RESET": self._handle_reset
        }

        self._pending_misbehavior = None   # (kind, payload) tuple, consumed by the next call
        self._last_response = None         # what the previous command actually answered

    # --- test hooks: each arms exactly one misbehavior for the *next* handle_request call ---

    def simulate_silence(self) -> None:
        self._pending_misbehavior = ("SILENCE", None)

    def simulate_garbage(self, text: str = "%$GARBAGE$%") -> None:
        self._pending_misbehavior = ("GARBAGE", text)

    def simulate_trailing_cr(self) -> None:
        self._pending_misbehavior = ("TRAILING_CR", None)

    def simulate_desync(self) -> None:
        self._pending_misbehavior = ("DESYNC", None)

    def handle_request(self, line: str) -> str | None:
        misbehavior = self._pending_misbehavior
        self._pending_misbehavior = None  # one-shot: reset before acting on it

        if misbehavior is None:
            response = self._dispatch(line)
            self._last_response = response
            return response

        kind, payload = misbehavior

        if kind == "SILENCE":
            return None  # device received the command but never answers

        if kind == "GARBAGE":
            return payload  # wrong prefix / unparseable text instead of a real reply

        if kind == "DESYNC":
            stale_response = self._last_response
            self._dispatch(line)          # device still processes the command internally...
            return stale_response          # ...but the host reads the previous answer instead

        # kind == "TRAILING_CR"
        response = self._dispatch(line)
        self._last_response = response
        return response if response is None else response + "\r"

    def _dispatch(self, line: str) -> str | None:
        parsed = self._parse_request(line)
        if parsed is None:
            return None

        command, arg = parsed
        handler = self._handlers.get(command)
        if handler is None:
            return "ERROR:UNKNOWN_COMMAND"

        try:
            if command in self._COMMANDS_WITH_ARG:
                if arg not in ("ON", "OFF"):
                    return "ERROR:BAD_ARG"
                result = handler(LedState(arg))
            else:
                result = handler()
        except InvalidCommandError:
            return "ERROR:BAD_ARG"

        if isinstance(result, Enum):
            result = result.value

        if command == "PING":
            return result
        if result is None:
            return "OK"

        return f"{self._TAGS[command]}:{result}"

    def _parse_request(self, line: str) -> tuple[str, str | None] | None:
        if not line.startswith("!"):
            return None
        command, sep, arg = line[1:].partition(" ")
        if command not in self._COMMANDS_WITH_ARG:
            return command, None
        return command, (arg if sep else None)

    def _handle_ping(self) -> str:
        return self.pong

    def _handle_get_status(self) -> DeviceStatus:
        return self.status

    def _handle_get_version(self) -> str:
        return self.firmware_version

    def _handle_get_temperature(self) -> float:
        return self.temp

    def _handle_get_led(self) -> LedState:
        return self.led_state

    def _handle_set_led(self, state: LedState) -> None:
        if not isinstance(state, LedState):
            raise InvalidCommandError(f"expected LedState, got {state!r}")
        self.led_state = state

    def _handle_reset(self) -> None:
        self.led_state = LedState.OFF
        self.status = DeviceStatus.READY
        self.boot_count += 1

    