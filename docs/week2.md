# Week 2 Architecture – Real Hardware Integration

## Goal of Week 2

Week 2 is about replacing the simulated DUT with a real physical device without changing the validation logic.

Main question:

> Can the same validation tests that worked with FakeHardware also work with a real ESP32 while keeping all serial/USB details hidden from the tests?

Conceptually:

Validation Tests
       |
       v
Device Interface
       ^
       |
   +---+---------+
   |             |
FakeHardware   Esp32Device
                  |
                  v
             Serial / USB
                  |
                  v
                ESP32

The validation tests should continue using high-level operations such as:

device.connect()
device.ping()
device.get_version()
device.get_status()
device.get_temp()
device.set_led(1)
device.get_led()
device.reset()
device.disconnect()

The tests should NOT know about:

- COM ports
- /dev/ttyUSB0
- baud rates
- serial.write()
- serial.read()
- newline characters
- byte conversion
- wire-format parsing

Those belong inside Esp32Device.

---

# Main Principle

Week 1 answered:

> What does the validation system expect a device to be capable of doing?

Week 2 answers:

> How can a real physical ESP32 satisfy that same contract?

The core rule is:

Validation intent stays the same.
Hardware-specific implementation changes.

For example, the validation test may call:

device.get_temp()

With FakeHardware:

get_temp()
    -> return self.temp

With Esp32Device:

get_temp()
    -> send command to ESP32
    -> receive response
    -> parse response
    -> return temperature

The validation test should not care which implementation is underneath.

---

# Main Components

## 1. Esp32Device

Esp32Device is the Python-side representation of the real ESP32.

Its responsibility is to translate high-level operations into communication with the physical device.

Example:

Validation test:

device.get_temp()

Esp32Device internally:

send "!GET_TEMP"
        |
        v
wait for response
        |
        v
receive something such as "TEMP:36"
        |
        v
parse it
        |
        v
return 36

The validation test should receive:

36

It should NOT receive:

"TEMP:36\r\n"

Serial/protocol details stay inside Esp32Device.

---

# 2. Communication Protocol

The computer and the ESP32 need to agree on how they communicate.

This agreement is the protocol.

It should define things such as:

- Which commands exist?
- How does a command begin/end?
- What responses should look like?
- What does an error response look like?
- How does the host know when a complete response has arrived?

Possible commands:

!PING
!GET_VERSION
!GET_STATUS
!GET_TEMP
!SET_LED 0
!SET_LED 1
!GET_LED
!RESET

Possible protocol examples:

Request:
!PING

Response:
PONG


Request:
!GET_VERSION

Response:
VERSION:1.0


Request:
!GET_TEMP

Response:
TEMP:36


Request:
!SET_LED 1

Response:
OK


Request:
!GET_LED

Response:
LED:1


Invalid request:

Response:
ERROR:UNKNOWN_COMMAND

The exact text format is up to the implementation.

The important thing is that both sides follow the same rules.

---

# 3. Serial Communication

Initially the PC and ESP32 will communicate through USB serial.

Conceptually:

Esp32Device
     |
     v
Serial connection
     |
     v
USB
     |
     v
ESP32

The serial-related code is responsible for:

- opening the port
- closing the port
- sending data
- receiving data
- waiting for responses
- respecting timeouts

The rest of the validation platform should not need to understand any of this.

---

# 4. Parsing

The ESP32 may return raw text.

The validation system should work with meaningful values.

Example:

ESP32 sends:

TEMP:36

Esp32Device parses it and returns:

36

Then the validation test can do something conceptually like:

temperature = device.get_temp()

verify temperature is inside expected range

The validation test should not need to strip:

\r
\n
TEMP:
etc.

That is Esp32Device's responsibility.

---

# 5. FakeHardware vs Esp32Device

By Week 2 there are two device implementations:

FakeHardware
Esp32Device

Both should satisfy the same device contract.

Conceptually:

DeviceInterface
      ^
      |
  +---+---------+
  |             |
FakeHardware   Esp32Device

FakeHardware implements operations using Python variables.

Example:

ping()
    -> return self.pong

Esp32Device implements the same operation using real communication.

Example:

ping()
    -> send !PING
    -> read response
    -> return response

The caller should use both in approximately the same way.

---

# Device Selection

The validation tests should not create FakeHardware or Esp32Device directly.

Something outside the tests should decide which implementation is used.

Conceptually:

Configuration / test setup
          |
          |
      Which device?
       /        \
      /          \
   fake          esp32
    |              |
    v              v
FakeHardware   Esp32Device
      \          /
       \        /
         device
           |
           v
   validation tests

For Week 2, this selection mechanism can stay simple.

There is no need for a complicated DeviceManager or factory architecture yet.

The important property is:

The validation test receives a device.

It should not need to know how that device was created.

---

# Connection Semantics

One architectural question to decide is:

What does device.connect() actually promise?

Possible interpretation 1:

"The serial port successfully opened."

Possible interpretation 2:

"The serial port opened and the expected DUT responded."

For example:

connect()
    |
    v
open serial port
    |
    v
send PING
    |
    v
receive PONG
    |
    v
connection successful

The exact choice is yours.

What matters is that the behavior is intentional and documented.

---

# Disconnect

disconnect() should release whatever resources were acquired during connect().

For FakeHardware this may simply mean:

connected = False

For Esp32Device it may mean:

close serial connection

After disconnecting, device operations should behave intentionally.

For example:

device.ping()

while disconnected should not silently behave as if everything is fine.

---

# Timeout Behavior

Real hardware can fail to respond.

Unlike FakeHardware, an ESP32 may:

- respond immediately
- respond slowly
- never respond
- reset
- disconnect
- send incomplete data

No command should wait forever.

Conceptually:

send command
     |
     +---- response arrives ----> continue
     |
     +---- timeout occurs ------> controlled failure

The exact timeout value is not important yet.

The important requirement is that a timeout exists.

---

# Error Handling

Week 2 should start distinguishing important communication errors.

Examples:

- device not connected
- serial port unavailable
- serial port cannot be opened
- response timeout
- malformed response
- unexpected response
- unsupported command
- device disconnected mid-operation

The goal is not to build a huge exception hierarchy.

The goal is to avoid behavior such as:

- random None returns
- hanging forever
- low-level errors leaking everywhere
- unclear failures

The caller should be able to understand why an operation failed.

---

# ESP32 Firmware

The ESP32 firmware should remain intentionally simple.

Its purpose is to act as a DUT for the validation platform.

Conceptually:

start
  |
  v
initialize state
  |
  v
wait for incoming command
  |
  v
parse command
  |
  v
perform requested action
  |
  v
send response
  |
  v
wait for next command

For example:

Incoming command
      |
      v
 Command parser
      |
 +----+---------+---------+
 |              |         |
PING         GET_TEMP   SET_LED
 |              |         |
 v              v         v
return PONG   get temp   change LED
 |              |         |
 +--------------+---------+
                |
                v
         send response

The firmware is supporting infrastructure.

Do NOT turn Week 2 into:

- Wi-Fi project
- Bluetooth project
- RTOS experiment
- OTA system
- web server on ESP32
- complicated embedded architecture

Unless a real validation requirement later justifies one of those things.

---

# Physical State

At least one operation should ideally change actual device state.

The easiest example is the LED.

Example:

device.set_led(1)
        |
        v
Esp32Device sends command
        |
        v
ESP32 changes LED state
        |
        v
device.get_led()
        |
        v
returns 1
        |
        v
validation test checks result

This demonstrates:

request
    ->
real hardware action
    ->
state observation
    ->
validation

That is more meaningful than only returning fixed strings.

---

# Reset

Reset becomes more realistic in Week 2.

With FakeHardware, reset may simply change Python state.

With the physical ESP32:

device.reset()

may cause:

send reset command
      |
      v
ESP32 reboots
      |
      v
communication temporarily disappears
      |
      v
ESP32 boots
      |
      v
device becomes available again

Questions to consider:

- Does reset() only trigger the reset?
- Does reset() wait until the device is READY again?
- Should another function wait for readiness?
- How long should booting be allowed to take?
- What happens if the device never comes back?

These are useful design questions.

They do not all require perfect solutions during Week 2.

---

# Pre-Hardware Work

If the ESP32 has not arrived yet, most host-side architecture can still be written.

Possible work:

- create Esp32Device
- make Esp32Device satisfy DeviceInterface
- define command strings
- define response formats
- define parsing logic
- define connect/disconnect behavior
- define timeout behavior
- define communication errors
- test command formatting
- test response parsing
- simulate serial communication

The goal is:

When the ESP32 arrives, hardware integration should mostly mean replacing simulated serial communication with an actual serial port.

---

# Simulated Serial Transport

Before the ESP32 arrives, the serial transport can be simulated.

Example:

Esp32Device sends:

!PING

Simulated serial returns:

PONG

Esp32Device.ping() should then return:

PONG

This allows host-side testing of:

- correct commands
- response parsing
- timeout behavior
- malformed responses
- unexpected responses
- connection behavior

Important distinction:

FakeHardware simulates the DUT itself.

A fake/mock serial transport simulates only the communication channel used by Esp32Device.

Those are different concepts.

Architecture:

Validation Test
      |
      v
Esp32Device
      |
      v
Fake Serial Transport
      |
      v
simulated protocol responses

Later:

Validation Test
      |
      v
Esp32Device
      |
      v
Real Serial Transport
      |
      v
ESP32

Esp32Device should ideally remain mostly unchanged.

---

# Responsibility Boundaries

## DeviceInterface

Responsible for:

Defining what operations a supported DUT must expose.

Example:

connect()
disconnect()
ping()
get_version()
get_status()
get_temp()
set_led()
get_led()
reset()

It does NOT contain serial implementation.

---

## FakeHardware

Responsible for:

- implementing the device contract using simulated state
- making development possible without physical hardware
- allowing intentionally good/bad device behavior

---

## Esp32Device

Responsible for:

- implementing the same device contract
- opening/closing real communication
- translating high-level methods into protocol commands
- sending commands
- receiving responses
- parsing responses
- handling hardware communication failures

It should NOT decide:

- whether temperature is acceptable
- whether firmware version is expected
- whether a validation test passes

Those belong to validation tests.

---

## Validation Tests

Responsible for:

- requesting device actions
- observing returned values
- comparing actual behavior against expected behavior
- deciding PASS or FAIL

They should NOT know:

- COM port
- baud rate
- serial protocol framing
- response prefixes
- USB implementation

---

## ESP32 Firmware

Responsible for:

- maintaining device-side state
- reading incoming commands
- interpreting protocol commands
- performing requested actions
- returning protocol responses

It should NOT know the validation expectations.

For example:

The ESP32 may report:

TEMP:36

It should not decide:

"36 means PASS"

That is validation logic.

---

# Example Complete Flow

Temperature example:

Validation Test
      |
      | device.get_temp()
      v
Esp32Device
      |
      | serial command: !GET_TEMP
      v
ESP32
      |
      | TEMP:36
      v
Esp32Device
      |
      | parse response
      v
36
      |
      v
Validation Test
      |
      | check expected temperature range
      v
PASS / FAIL

---

# Suggested Project Layout

device-validation-platform/
|
├── src/
│   └── validation/
│       └── device/
│           ├── device_interface.py
│           ├── fake_hardware.py
│           └── esp32_device.py
|
├── validation_tests/
│   ├── test_ping.py
│   ├── test_version.py
│   ├── test_temperature.py
│   └── test_state.py
|
├── firmware/
│   └── esp32/
|
├── tests/
│   └── unit/
|
└── docs/
    ├── week1_architecture.md
    └── week2_architecture.md

Exact layout is not mandatory.

Responsibilities matter more than exact filenames.

---

# Week 2 Core Requirements

By the end of Week 2:

1. A real ESP32 device implementation exists.

2. Esp32Device satisfies the same high-level contract as FakeHardware.

3. A simple command/response protocol exists.

4. Esp32Device translates high-level operations into protocol commands.

5. Raw responses are parsed inside Esp32Device.

6. Validation tests do not contain serial-specific logic.

7. Validation tests can run against FakeHardware.

8. The same logical validation tests can run against Esp32Device.

9. Device selection happens outside the validation tests.

10. Communication has finite timeouts.

11. Connection failures are handled intentionally.

12. At least one malformed/unexpected response is handled intentionally.

13. At least one device state-changing operation exists.

14. Real ESP32 communication works once the hardware arrives.

---

# Week 2 Non-Goals

Do NOT add these yet unless some concrete requirement unexpectedly demands them:

- FastAPI
- database
- frontend
- scheduler
- worker queue
- multiple DUTs
- cloud hosting
- Docker orchestration
- authentication
- AI
- Redis
- Kafka
- Kubernetes
- complicated ESP32 networking
- Wi-Fi management
- Bluetooth functionality

These are future problems.

---

# Questions to Ask Yourself During Week 2

## 1. Does my validation test know this is an ESP32?

Ideally very little.

It should mainly know it has a device with the required operations.

---

## 2. Does my validation test contain serial code?

If yes, ask whether that code belongs in Esp32Device instead.

---

## 3. Does Esp32Device return raw wire-format strings?

Ask whether parsing should happen before returning data to the caller.

---

## 4. What does connect() actually guarantee?

Opening the port?

Or successful communication with the DUT?

---

## 5. What happens when the DUT never answers?

There should be a timeout.

---

## 6. What happens if the response is malformed?

Example:

Expected:

TEMP:36

Received:

BANANA

The system should fail intentionally rather than behave unpredictably.

---

## 7. What happens when the device resets?

Think about temporary communication loss and recovery.

---

## 8. Can I replace FakeHardware with Esp32Device without rewriting validation tests?

If not, investigate why.

---

## 9. Am I adding something because I need it?

Avoid adding infrastructure only because it sounds professional.

---

## 10. Which layer owns this responsibility?

Always ask whether something belongs to:

- validation tests
- device contract
- Esp32Device
- serial transport
- ESP32 firmware

---

# Definition of Done

Week 2 is successful when this works conceptually:

                Device Contract
                 ^           ^
                 |           |
                 |           |
          FakeHardware    Esp32Device
                 ^           ^
                 |           |
                 +-----+-----+
                       |
                       v
                Validation Tests

You should be able to run the same logical tests against the fake device and the real physical ESP32.

Example:

Run against FakeHardware
        |
        v
tests execute
        |
        v
PASS / FAIL


Run against ESP32
        |
        v
same validation logic
        |
        v
real serial communication
        |
        v
real physical DUT
        |
        v
PASS / FAIL

Then intentionally create at least one failure:

- unplug the device
- produce wrong response
- cause timeout
- invalid LED state
- malformed protocol response

and observe a clear, controlled result.

The main thing Week 2 proves is:

> The architecture can move from simulated hardware to real hardware without forcing hardware-specific details into the validation system.