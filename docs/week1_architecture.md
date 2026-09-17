# Week 1 Architecture – Validation Core

## Goal of Week 1

The purpose of Week 1 is to build the smallest useful validation architecture.

The goal is **not** to emulate an ESP32 in detail and not to build the final validation platform.

The goal is to prove that the system can:

1. Represent a device through software.
2. Interact with that device through a clean interface.
3. Define validation tests separately from device behavior.
4. Detect both correct and incorrect device behavior.
5. Handle basic device failures intentionally.
6. Be designed so that the fake device can later be replaced by real hardware without rewriting the validation logic.

The central architectural idea is:

```text
Validation Test
      │
      ▼
Device Contract
      │
      ▼
Fake Hardware
```

Later this should become:

```text
Validation Test
      │
      ▼
Device Contract
      │
      ├── Fake Hardware
      │
      └── Real ESP32
```

The validation tests should ideally not care which implementation is being used.

---

# Main Architecture Principle

The most important separation is between:

```text
WHAT the device should do
```

and:

```text
HOW the device actually does it
```

A validation test may care that:

```text
PING → PONG
```

but it should not care whether `PING` was sent through:

```text
Python method call
Serial
USB
TCP
SSH
```

The communication mechanism belongs to the device implementation.

The expected behavior belongs to the validation logic.

---

# Main Components

## 1. Device Contract / Interface

The device interface defines what operations the validation system is allowed to perform on a device.

Possible operations include:

```text
connect
disconnect
send_command
reset
```

The exact set should remain small.

Do not add methods because they sound useful.

Add methods because the validation system has a real need for them.

The device interface is responsible for providing a consistent way to control a device.

It is not responsible for deciding whether device behavior is correct.

Example responsibility:

```text
send_command("PING")
→ returns "PONG"
```

The device layer returns what happened.

The validation layer decides whether that result is acceptable.

---

# 2. Fake Hardware

The fake hardware is a simulated DUT.

It exists so that the validation architecture can be developed before physical hardware is introduced.

It should behave like a very small controllable device.

Possible internal state:

```text
connected
firmware_version
temperature
led_state
status
boot_count
```

Possible supported commands:

```text
PING
GET_VERSION
GET_TEMP
GET_STATUS
SET_LED
GET_LED
RESET
```

The fake device does not need to model every ESP32 capability.

It only needs enough behavior to support meaningful validation scenarios.

---

# Why the Fake Device Should Have State

A fake device that always returns fixed values is useful only for the simplest tests.

A stateful fake allows more interesting validation.

Example:

```text
Initial state:

LED = OFF
```

Engineer sends:

```text
SET_LED ON
```

Then:

```text
GET_LED
```

returns:

```text
ON
```

Then:

```text
RESET
```

may return the device to:

```text
LED = OFF
```

This allows validation to test not only command responses but state transitions.

---

# Fake Hardware Should Also Support Failure

The fake device should eventually allow intentionally incorrect behavior.

Possible scenarios:

```text
device disconnected
wrong firmware version
unrealistic temperature
unexpected command response
device in ERROR state
timeout / no response
```

This is important because the validation system must prove that it can detect bad behavior.

A validation framework that only succeeds against a perfectly behaving fake device proves very little.

---

# 3. Validation Tests

Validation tests represent expected device behavior.

The basic pattern is:

```text
Perform action
      ↓
Observe result
      ↓
Compare against expectation
      ↓
PASS / FAIL
```

Example:

```text
Action:
PING

Observed:
PONG

Expected:
PONG

Result:
PASS
```

Another example:

```text
Action:
GET_TEMP

Observed:
150°C

Expected:
temperature within valid operating range

Result:
FAIL
```

The test contains the expectation.

The fake hardware contains the actual value.

This separation must remain clear.

---

# Device State vs Validation Expectation

This distinction is one of the most important parts of Week 1.

The device may contain:

```text
temperature = 25
```

The test may contain:

```text
0 <= temperature <= 80
```

The device may contain:

```text
firmware_version = "1.3.0"
```

The test may expect:

```text
firmware_version == "1.3.0"
```

The device should not know what result counts as PASS.

The validation layer should not directly control internal device state unless it is intentionally configuring a test scenario.

---

# 4. Validation Result

Even in Week 1, it is useful to think about the output of a test.

A result should conceptually contain information such as:

```text
test name
status
expected value
actual value
error information
```

For example:

```text
Test: test_ping

Expected:
PONG

Actual:
INVALID

Result:
FAIL
```

The exact representation can remain simple.

The main goal is that failures are understandable.

A result that only says:

```text
FAILED
```

is much less useful than:

```text
Expected firmware 1.2.0
Received firmware 1.1.0
```

---

# Possible Week 1 Project Structure

The exact structure is not mandatory, but responsibilities should stay separated.

Example:

```text
device-validation-platform/
│
├── README.md
│
├── docs/
│   └── week1_architecture.md
│
├── src/
│   └── validation/
│       │
│       ├── device/
│       │   ├── fake_hardware.py
│       │   └── device_interface.py
│       │
│       └── models/
│
├── validation_tests/
│   ├── test_ping.py
│   ├── test_version.py
│   ├── test_temperature.py
│   └── test_state.py
│
└── tests/
    └── unit/
```

The structure may evolve.

The important distinction is between:

```text
tests of the validation platform
```

and:

```text
tests that validate the DUT
```

These are different things.

---

# Unit Tests vs Validation Tests

This distinction should be understood early.

## Unit Tests

These test your own framework code.

Example:

```text
Does FakeHardware.reset() correctly restore its state?
```

You are testing your software implementation.

---

## Validation Tests

These test the behavior of the DUT.

Example:

```text
After reset, should the device report READY?
```

You are testing the device.

Today both may use the same fake object.

Later the validation tests should run against real hardware.

---

# Responsibility Boundaries

A useful way to think about the architecture is:

## Fake Hardware

Responsible for:

```text
maintaining simulated device state
accepting supported commands
returning responses
simulating failure conditions
```

Not responsible for:

```text
deciding PASS / FAIL
knowing expected firmware
knowing valid temperature ranges
producing validation reports
```

---

## Device Interface

Responsible for:

```text
providing a consistent device API
hiding communication details
```

Not responsible for:

```text
validation rules
test expectations
scheduling
database storage
```

---

## Validation Test

Responsible for:

```text
performing an action
checking an expectation
reporting success or failure
```

Not responsible for:

```text
how serial communication works
how jobs are scheduled
where results are stored permanently
```

---

# What Week 1 Should NOT Contain

Avoid introducing these unless a real need appears:

```text
FastAPI
database
job scheduler
multiple workers
Docker
frontend
firmware flashing
authentication
cloud deployment
AI
Kafka
Redis
Kubernetes
```

These belong to later milestones.

Week 1 should remain small enough that every architectural decision is understandable.

---

# Questions to Ask While Implementing

Whenever adding something, ask:

## Does this belong to the device or the test?

Example:

```text
firmware_version = "1.2"
```

Device.

```text
expected_version = "1.2"
```

Test.

---

## Does the validation logic know too much about the hardware?

If a validation test contains things like:

```text
/dev/ttyUSB0
baudrate
serial.read(...)
```

the abstraction is leaking.

---

## Is this method needed yet?

Before adding:

```text
get_voltage()
get_cpu_usage()
get_wifi_status()
```

ask:

> Which validation scenario requires this?

If there is no answer, do not add it yet.

---

## Can I simulate failure?

For each important behavior, consider whether you can produce:

```text
normal case
incorrect case
unavailable/error case
```

The fake hardware should help with this.

---

## What should remain unchanged next week?

When real hardware is introduced, ideally:

```text
validation intent
test structure
expected behaviors
```

should mostly remain unchanged.

The main change should be the device implementation.

That is one of the strongest signals that the abstraction is working.

---

# Example Behavioral Scenarios

The exact tests are up to the implementation, but Week 1 should support different types of validation.

## Stateless behavior

```text
PING
↓
PONG
```

Simple request/response.

---

## Metadata

```text
GET_VERSION
↓
1.2.0
```

Validation compares against expected metadata.

---

## Range validation

```text
GET_TEMP
↓
27
```

Validation checks whether the result falls within an acceptable range.

---

## State change

```text
SET_LED ON
↓
GET_LED
↓
ON
```

The test verifies that an action changed device state.

---

## Lifecycle behavior

```text
SET_LED ON
↓
RESET
↓
GET_LED
↓
OFF
```

The test verifies state after reset.

---

## Failure behavior

```text
Device disconnected
↓
command attempted
↓
controlled failure
```

The framework should not behave unpredictably.

---

# Definition of Done for Week 1

Week 1 is successful if the architecture demonstrates:

- A fake DUT exists.
- The fake DUT has some meaningful internal state.
- A small set of commands represents different behavioral patterns.
- Validation code interacts with the device through a clear boundary.
- Tests determine PASS / FAIL rather than the device itself.
- Good device behavior produces passing validation.
- Intentionally bad behavior produces failing validation.
- At least one device/error scenario is handled intentionally.
- Failures provide useful information.
- The architecture could reasonably support a real ESP32 implementation next.
- No unnecessary infrastructure has been introduced.

The code does not need to be large.

A small implementation with clean responsibilities is preferable to a large implementation with unclear boundaries.

---

# End-of-Week Design Review

Before moving to physical hardware, be able to answer:

1. What exactly is a device from the perspective of this system?
2. What operations does the validation system need from a device?
3. Why does the fake hardware exist?
4. What state belongs inside the fake hardware?
5. What expectations belong inside validation tests?
6. Who determines PASS or FAIL?
7. How can incorrect device behavior be simulated?
8. What happens if the device is unavailable?
9. If FakeHardware is replaced by an ESP32, what code should remain unchanged?
10. What current limitations justify the next milestone?

If these answers are clear, the purpose of Week 1 has been achieved.
