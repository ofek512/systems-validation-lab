# Week 2 – Working Reference

A short reference for *what to do next* and *how serial protocols actually work*.
Not a spec. The spec is `docs/protocol.md`, which you write in step 1.

---

## Part A – Workflow

### Step 1 — Write `docs/protocol.md`

Before any code. One page. It must answer:

- How does the host know a response is **complete**?
- What does an unknown command return?
- What happens if the device says nothing at all?
- Is a response self-describing (`TEMP:36`) or bare (`36`)?
- One command → one response, always?
- How would you add a new command later without breaking an old host?

**Done when:** someone else could implement the firmware from your doc alone.

---

### Step 2 — Define the transport seam

A tiny abstract class, separate from `DeviceInterface`:

```text
write_line(text: str) -> None
read_line(timeout: float) -> str
open() / close()
```

That is the entire contract between "protocol logic" and "wires".

**Done when:** `Esp32Device` could be written against it with no `import serial` anywhere.

---

### Step 3 — `LoopbackTransport` + `FakeFirmware`

`FakeFirmware` is a Python object that consumes protocol *text* and returns protocol
*text* — it implements `docs/protocol.md`, nothing else.

It must also be able to misbehave on demand:

- reply nothing (timeout)
- reply `ERROR:UNKNOWN_COMMAND`
- reply with garbage / wrong prefix
- reply with a trailing `\r`
- reply the *previous* command's answer (desync)

**Note the distinction:**

| | fakes what | lives where |
|---|---|---|
| `FakeHardware` | the *device contract* | `src/validation/device/` |
| `FakeFirmware` | the *wire protocol* | `src/validation/device/` (transport side) |

These are different fakes at different layers. That's the point of the week.

---

### Step 4 — `Esp32Device(DeviceInterface)`

Only responsibilities:

1. build a command string
2. hand it to the transport
3. read a line back
4. validate + parse it
5. return a Python value, or raise a `DeviceError` subclass

Decide explicitly:
- what `connect()` promises (port open? or port open **and** PING answered?)
- what `reset()` promises (reset requested? or device back and ready?)
- what happens if a call is made while disconnected

---

### Step 5 — Unit tests in `tests/unit/`

Against `LoopbackTransport`. This is where the real learning is. Cover:

- happy path for every command
- `TEMP:abc` → what happens?
- `ERROR:BUSY` → which exception?
- silence → timeout → which exception?
- `TEMP:36\r\n` → does `36.0` come out clean?
- call while disconnected

---

### Step 6 — Device selection

Tests must stop doing `FakeHardware()` directly.

Add a `conftest.py` with:
- a `--device=fake|loopback|esp32` pytest option
- a `device` fixture that builds the right one and connects/disconnects it

Then convert `validation_tests/` to take `device` as a fixture.

**This will break `test_temperature.py`** — it calls `inject_temperature(150)`, which no
real device supports. Decide: does fault injection belong in `validation_tests/` at all,
or do those tests move to `tests/unit/`? Write down why.

---

### Step 7 — `SerialTransport` (needs pyserial, not the board)

Real `pyserial`, pointed at a virtual COM pair (`com0com` on Windows, `socat` PTY on WSL).
Everything above it is already tested; only this layer is new.

---

### Step 8 — Real ESP32 (when it arrives)

Flash firmware implementing `docs/protocol.md`. Nothing in steps 1–6 should change.
If it does change, the abstraction was wrong — and finding that out is the exam.

---

## Part B – How this actually works (no prior experience assumed)

### What an ESP32 is, for our purposes

A small microcontroller board. You plug it into USB. It runs a single program
(firmware) in an infinite loop — no OS, no filesystem, no shell. You cannot "log in"
to it. The only way to talk to it is the program you flashed.

Our firmware will be roughly:

```text
loop forever:
    read a line from serial
    look at the text
    print a line back
```

That's it. The "device" in our validation system is that loop.

### What "serial" is

A serial port is a byte pipe. Two directions, no structure, no messages, no packets.
You write bytes, the other side reads bytes. Nothing tells you where one message ends
and the next begins — **you** have to invent that. That invention is the protocol.

On Windows it appears as `COM3`, `COM7`, etc. On Linux `/dev/ttyUSB0`.
The USB cable carries it, but a USB-to-serial chip on the board makes it look like a
plain old serial port to your PC. That's why `pyserial` works over USB.

`baudrate` (e.g. `115200`) is the agreed bits-per-second. Both sides must pick the
same number or you get garbage bytes — not an error, just garbage. It is the single
most common "why is it broken" cause.

### Framing — the central idea

You send:

```text
!GET_TEMP\n
```

The device replies, and your `read()` might return:

```text
"TE"
```

…because that's all that had arrived when you asked. Then `"MP:3"`, then `"6\r\n"`.
Bytes arrive when they arrive.

So you need a rule for "a message is complete". The universal cheap rule is:
**a message ends at `\n`**. Read until you see one. That's framing.

`pyserial` gives you `read_until(b"\n")` for exactly this.

Consequence: `\n` can never appear *inside* a value. That's a real constraint your
protocol doc should state.

### Timeouts

The device may never answer — crashed, wrong baud, unplugged, bug. Without a timeout
your program hangs forever. With `pyserial`:

- `timeout=None` → block forever (never do this)
- `timeout=0` → return immediately with whatever's there (non-blocking)
- `timeout=1.0` → wait up to 1 second, then return what you got, possibly nothing

So `read_until(b"\n")` with a timeout can return an **incomplete** line. You must check
that what you got actually ends in `\n` before trusting it. Otherwise you'll parse half
a message and get a confusing error far from the real cause.

### Line endings

Arduino's `Serial.println("TEMP:36")` sends `TEMP:36\r\n` — carriage return *and*
newline. If you frame on `\n` and don't strip `\r`, you get `"TEMP:36\r"` and
`float("36\r")` may or may not work depending on where you split. Always `.strip()`
before parsing. This bites everyone once.

### Desynchronisation — the nastiest failure

Request/response over a byte pipe has no message IDs. If `!GET_TEMP` times out and
the reply arrives one second later, your *next* command `!GET_LED` reads `TEMP:36`
and believes it. Now every answer is one behind, forever, and nothing looks obviously
wrong.

Two defences, pick one and document it:
1. **Drain on timeout** — after a timeout, throw away everything in the input buffer.
2. **Self-describing responses** — `TEMP:36` for `!GET_TEMP`; if the prefix doesn't
   match what you asked, it's a stale reply → discard and keep reading.

This is why `TEMP:36` beats bare `36`, and worth saying so in your protocol doc.

### Boot noise and auto-reset

Two ESP32-specific surprises:

1. On power-up the ROM bootloader prints diagnostic junk at a *different* baud rate
   (74880). It will look like random bytes in your stream.
2. Opening the serial port toggles the DTR/RTS control lines, and on most ESP32 dev
   boards that wiring **resets the chip**. So the act of connecting reboots the device,
   which then emits boot noise.

Practical consequence: `connect()` should open the port, wait briefly, then flush the
input buffer before sending the first command. Otherwise your first `!PING` reads boot
garbage and "fails".

### Why the layering matters

```text
Esp32Device        protocol + parsing      "!GET_TEMP" -> 36.0
      |
  Transport        bytes, lines, timeouts
   /        \
SerialTransport   LoopbackTransport
      |                 |
   pyserial         FakeFirmware
```

Everything genuinely hard above — framing, parsing, error mapping, desync policy —
lives in `Esp32Device` and is testable today, with no board, in CI, deterministically.
`SerialTransport` stays small and boring, and is the only thing that needs hardware.

If `Esp32Device` opens the port itself, none of that is testable. That single decision
is most of the week's value.

---

## Self-check (end of week)

1. Where exactly does `"TEMP:36\r\n"` stop being a string and become `36.0`, and why there?
2. If `SerialTransport` were deleted, how much of the suite still runs?
3. What does `connect()` guarantee, in one sentence?
4. A validation test fails — how do you tell "device broken" from "parser broken"?
5. Why is `FakeHardware` still valuable now that `Esp32Device` exists?

---

## Rules for using the assistant this week

**Fair game:** how does X work, review my spec, critique my design, why does this hang,
what did I not consider.

**Not fair game:** write `Esp32Device`, write the `conftest.py`, write my tests.

Write it yourself first, then ask for a teardown.
