# Device Validation Platform

## Overview

The goal of this project is to build a system that can automatically test a physical device, collect and store the results, and clearly present what happened with minimal manual intervention.

The main focus of the project is **not the complexity of the device itself**, but the infrastructure around validating it.

A simple ESP32 or similar development board will be used as the Device Under Test (DUT). This keeps the hardware side manageable while allowing the project to focus on automation, scheduling, reliability, test execution, result storage, and reporting.

---

## The Problem

In a simple or poorly automated validation environment, the workflow might look like this:

```text
Engineer connects device
        ↓
Flashes firmware manually
        ↓
Runs test script manually
        ↓
Looks at terminal output
        ↓
Decides PASS / FAIL
        ↓
Maybe copies result somewhere
```

This approach may be acceptable for:

```text
1 engineer
1 device
5 tests
```

but it does not scale well when dealing with:

```text
many engineers
many devices
many firmware versions
hundreds or thousands of tests
continuous validation
```

At larger scale, engineers should not need to manually operate the hardware for every validation run.

The validation infrastructure should handle most of the process automatically.

---

# Project Goal

The system should allow an engineer to request a validation run and have the platform automatically handle the rest.

Conceptually, the final architecture will look approximately like this:

```text
                  Engineer
                     │
                     ▼
               Web Interface
                     │
                     ▼
                    API
                     │
                     ▼
               Job Scheduler
                     │
                     ▼
                   Worker
                     │
              Device Interface
                     │
                     ▼
                    DUT
                     │
                Test Output
                     │
                     ▼
                 Database
                     │
                     ▼
            Results / Dashboard
```

The engineer should be able to request something similar to:

```text
Run the regression suite
on ESP32-01
using firmware version 1.4.2
```

The system should then take responsibility for executing and recording that request.

---

# High-Level Flow

The project aims to change the validation process from this:

```text
Human
  │
  ├── connects hardware
  ├── runs commands
  ├── watches output
  ├── determines PASS / FAIL
  └── records results
```

into this:

```text
Human
  │
  └── requests validation
          │
          ▼
       System
          │
          ├── selects / locks DUT
          ├── prepares the device
          ├── executes tests
          ├── monitors the device
          ├── handles timeouts and errors
          ├── records logs and output
          ├── determines test results
          └── presents a report
```

The human becomes responsible mainly for **requesting and analyzing validation**, rather than manually performing every step.

---

# Main Components

## Device Under Test — DUT

The DUT is the physical hardware being validated.

For this project, the DUT will initially be an ESP32 or similar development board.

The firmware may expose simple commands such as:

```text
PING
GET_VERSION
SELF_TEST
RESET
GET_STATUS
```

The device itself is intentionally simple.

The important part of the project is the system responsible for controlling, testing, monitoring, and validating it.

---

## Device Interface

The Device Interface is a Python abstraction between the validation system and the physical hardware.

Tests should be able to perform operations such as:

```python
device.connect()
device.send(...)
device.reset()
device.disconnect()
```

instead of dealing directly with low-level implementation details such as:

```text
/dev/ttyUSB0
baudrate = 115200
pyserial.read_until(...)
```

This separation means that the validation logic does not need to know exactly how the hardware communicates.

For example, the same test could theoretically run against:

```text
FakeDevice
SerialDevice
NetworkDevice
```

as long as they expose the same expected interface.

---

## Tests

Tests verify individual behaviors of the DUT.

For example:

```text
Send PING
Expect PONG
```

or:

```text
Reset device
Wait for boot
Verify device responds within 10 seconds
```

A test should mainly answer one question:

> Did this specific behavior work correctly?

Tests will initially be written and executed using `pytest`.

---

## Test Suite

A Test Suite is a collection of tests that are intended to run together.

For example:

```text
Smoke Suite

- device responds
- firmware version is readable
- basic command works
```

or:

```text
Regression Suite

- communication tests
- reset tests
- functional tests
- error handling tests
```

This allows an engineer to request:

```text
Run the regression suite
```

instead of manually selecting individual tests.

---

## Validation Run

A Validation Run represents one execution of a test suite.

For example:

```text
Run ID: 142

Device: ESP32-01
Firmware: 1.4.2
Suite: regression

Start Time: 14:32
End Time: 14:38

Result: FAILED
```

This distinction is important because the same test or suite may be executed many times against different:

```text
devices
firmware versions
configurations
dates
```

The system should preserve the history of these executions.

---

## API

The API provides a controlled way for software to interact with the validation platform.

For example, the hardware may physically sit on a computer at home while the engineer requests a validation run from another machine.

The API could eventually expose operations such as:

```text
POST /runs
GET  /runs
GET  /runs/{id}

GET  /devices
POST /devices/{id}/reset
```

The API is not responsible for directly executing long-running tests.

Its job is mainly to:

```text
receive requests
validate requests
create jobs
return status/results
```

---

## Job Scheduler

The Job Scheduler is responsible for deciding **what should run and when**.

For example, an engineer may request many validation jobs:

```text
Job 1:
Firmware A + Smoke Suite

Job 2:
Firmware A + Regression Suite

Job 3:
Firmware B + Regression Suite
```

The scheduler must determine when each job can execute.

Eventually it may need to consider things such as:

```text
device availability
device reservations
job priority
queue order
firmware requirements
parallel execution
```

A simple scheduling policy is enough initially.

The important part is separating:

> requesting work

from

> deciding when the work can run.

---

## Worker

The Worker is responsible for actually performing validation work.

For example:

```text
Worker receives job

"Run regression suite
 on ESP32-01
 using firmware 1.4.2"
```

The worker may then:

```text
reserve device
connect to device
prepare / flash firmware
execute tests
collect logs
handle failures
store results
release device
```

The worker performs the long-running work so that the API does not need to remain blocked while tests execute.

---

## Database

The database stores information that must survive after a validation run finishes.

Possible stored information includes:

```text
devices
firmware versions
validation runs
individual test results
timestamps
execution durations
error messages
logs
```

This allows the system to answer questions such as:

```text
Which firmware version introduced this failure?

When did this test first start failing?

Is one DUT failing more often than the others?

How long does this test normally take?

What happened during run #142?
```

The initial database will likely be PostgreSQL once persistent storage becomes necessary.

---

## Web Interface

The Web Interface provides a simple human-facing view of the validation system.

An engineer should eventually be able to see something like:

```text
Device: ESP32-01
Status: ONLINE
Firmware: 1.4.2

[ Run Smoke Suite ]
[ Run Regression Suite ]

Recent Runs

#142    FAILED
#141    PASSED
#140    PASSED
```

The interface does not perform validation itself.

It allows the engineer to interact with and inspect the underlying system.

---

# Logical Layers

The system can be thought of as four main layers:

```text
┌───────────────────────────┐
│ User Layer                │
│ Web UI / CLI              │
├───────────────────────────┤
│ Control Layer             │
│ API / Scheduler / Jobs    │
├───────────────────────────┤
│ Validation Layer          │
│ Tests / Worker / Results  │
├───────────────────────────┤
│ Hardware Layer            │
│ Device Interface / DUT    │
└───────────────────────────┘
```

### User Layer

How engineers interact with the system.

### Control Layer

Determines what work should happen and when.

### Validation Layer

Executes validation and interprets results.

### Hardware Layer

Handles communication with the actual physical DUT.

---

# Design Philosophy

The project should grow from actual requirements rather than adding technologies simply because they are popular.

For every new component or technology, the following questions should be asked:

```text
What problem does this solve?

Which component should be responsible for it?

What happens if it fails?

What is the smallest implementation that proves the idea?

Does this improve the system or only make the architecture more complicated?
```

For example:

A distributed message broker is unnecessary if a simple queue solves the current problem.

A complex frontend is unnecessary if a minimal dashboard allows engineers to understand validation results.

The project should become more complex only when the simpler design exposes a real limitation.

---

# Initial Scope

The project will start much smaller than the final architecture.

The first version may simply look like:

```text
pytest
   │
   ▼
Device Interface
   │
   ▼
Fake Device
```

Then:

```text
pytest
   │
   ▼
Device Interface
   │
   ▼
Physical ESP32
```

From there, additional components can be introduced as limitations appear:

```text
Need historical results
→ add persistence

Need remote execution
→ add API

Need asynchronous execution
→ add jobs and workers

Need many devices
→ add scheduling and device locking

Need easier human interaction
→ add web interface
```

The goal is therefore not to implement the final architecture immediately.

The goal is to **grow toward it while understanding why every piece exists**.
