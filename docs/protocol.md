# DUT Serial Protocol — v1.0

Command protocol spoken between the host (`Esp32Device`) and the DUT firmware.

## Scope and assumptions

- Transport: UART over USB, 115200 baud, 8N1, no flow control.
- Encoding: ASCII, printable characters only. Max line length 64 bytes including terminator.
- The host always initiates. The device never sends unsolicited data, except boot output
  immediately after reset (see Reset).
- Exactly one request is outstanding at a time. No pipelining.

## Framing

- Every message, both directions, ends with `\n`.
- The device must emit `\n`. The host must tolerate and strip a preceding `\r`.
- One request produces exactly one response line.
- A read that ends without `\n` is incomplete and must be treated as a timeout, never as data.

## Requests

```text
!<COMMAND>[ <arg>]\n
```

- `!` is mandatory. A line without it is ignored silently (it is echo or noise, not a command).
- Commands are uppercase. Command names and argument values are case-sensitive.
- A single space separates command from argument. At most one argument.

## Responses

| Kind            | Shape           | Example             |
| --------------- | --------------- | ------------------- |
| Value           | `<TAG>:<value>` | `TEMP:36`           |
| Acknowledgement | `OK`            | after `!SET_LED ON` |
| Liveness        | `PONG`          | after `!PING`       |
| Error           | `ERROR:<CODE>`  | `ERROR:BAD_ARG`     |

Value responses are tagged so the host can detect a stale reply from a previously
timed-out command and resynchronise. `PONG` is untagged by convention; it carries no value.

## Errors

| Code                    | Meaning                                                |
| ----------------------- | ------------------------------------------------------ |
| `ERROR:UNKNOWN_COMMAND` | `!` line whose command name is not in this document    |
| `ERROR:BAD_ARG`         | known command, missing/extra/unparseable argument      |
| `ERROR:NOT_READY`       | command cannot be served in the device's current state |

## Timeouts and recovery

- Host timeout: 1000 ms per command, measured from end of write to receipt of `\n`.
- On timeout the host discards the input buffer before issuing the next command.
- A response whose tag does not match the command just sent is discarded, and the host
  keeps reading until the timeout expires.

---

## Commands

### !PING

```text
Request:  !PING
Response: PONG
```

Parameters: none
Values: none
Errors: none — `!PING` is answered in every state, including `ERROR`
Notes: liveness only. A `PONG` means the link works, not that the device is healthy.

### !GET_VERSION

```text
Request:  !GET_VERSION
Response: VERSION:<value>
```

Parameters: none
Values: `<value>` — `MAJOR.MINOR.PATCH`, decimal, no leading zeros, e.g. `1.2.0`
Errors: none
Notes: identifies firmware only, not the board. Serial number is deferred to v1.1.

### !GET_STATUS

```text
Request:  !GET_STATUS
Response: STATUS:<value>
```

Parameters: none
Values: `<value>` — `READY` | `ERROR`
Errors: none
Notes: `!GET_STATUS` is the diagnostic command and must be answerable in every state.
It therefore never returns `ERROR:NOT_READY` — an unhealthy device reports
`STATUS:ERROR`, which is a successful response carrying bad news.

### !GET_TEMPERATURE

```text
Request:  !GET_TEMPERATURE
Response: TEMP:<value>
```

Parameters: none
Values: `<value>` — signed integer, degrees Celsius, `-40`..`125`
Errors: `ERROR:NOT_READY` if the sensor is uninitialised or the device is in `ERROR`
Notes: the range above is what the wire can encode. Whether a reading is _acceptable_
is decided by the validation layer, not here.

### !SET_LED

```text
Request:  !SET_LED <state>
Response: OK
```

Parameters: `<state>` — `ON` | `OFF`
Values: none
Errors: `ERROR:BAD_ARG` if `<state>` is absent or not `ON`/`OFF`;
`ERROR:NOT_READY` if the device is in `ERROR`
Notes: values match `LedState` exactly, so no numeric mapping exists on the wire.
Setting the LED to its current state is not an error.

### !GET_LED

```text
Request:  !GET_LED
Response: LED:<value>
```

Parameters: none
Values: `<value>` — `ON` | `OFF`
Errors: `ERROR:NOT_READY` if the device is in `ERROR`
Notes: none.

### !RESET

```text
Request:  !RESET
Response: OK
```

Parameters: none
Values: none
Errors: `ERROR:NOT_READY` never applies — reset is the escape from `ERROR`
Notes: see Reset semantics.

---

## Reset semantics

`OK` means _the reset was accepted_, not _the device is back_. After sending it the
device reboots and emits bootloader output at an unrelated baud rate, which arrives as
garbage bytes.

The host must therefore:

1. read the `OK`,
2. wait for the boot window (500 ms),
3. discard the input buffer,
4. poll `!PING` until `PONG` arrives or 3000 ms elapse.

Only then is `reset()` complete. Post-reset state is `LED:OFF`, `STATUS:READY`.

Connect follows the same rule: opening the port toggles DTR/RTS and resets most ESP32
boards, so `connect()` performs steps 2–4 above before any other command.

## Host-side only

`connect()`, `disconnect()` and `is_connected()` have no wire command. They manage the
serial port, which is host state. `connect()` uses `!PING` as its handshake, so a
successful connect means _the port opened and the expected DUT answered_.

## Error mapping

| Wire situation                   | Host exception            |
| -------------------------------- | ------------------------- |
| `ERROR:UNKNOWN_COMMAND`          | `InvalidCommandError`     |
| `ERROR:BAD_ARG`                  | `InvalidCommandError`     |
| `ERROR:NOT_READY`                | `DeviceError`             |
| no response within timeout       | `DeviceError`             |
| malformed or mistagged response  | `DeviceError`             |
| command issued while port closed | `DeviceNotConnectedError` |

## Versioning

New commands may be added in a minor version. Existing request syntax, response tags and
error codes are fixed within a major version. A host that receives an unrecognised tag
must treat it as a malformed response rather than guessing.

## Open questions

- The last three rows of the error mapping all collapse to bare `DeviceError`, which loses
  information a validation report needs. Likely additions: `DeviceTimeoutError`,
  `ProtocolError`, `DeviceNotReadyError`.
- `boot_count` exists in `FakeHardware` but has no command, so reset counting cannot be
  validated on real hardware. Add `!GET_BOOT_COUNT` or drop the field.
- Temperature is an integer on the wire but `DeviceInterface.get_temperature()` returns
  `float`. Fixed-point (`TEMP:365` = 36.5 °C) is deferred until a real sensor justifies it.
- No self-test command yet, though `README.md` anticipates one.
