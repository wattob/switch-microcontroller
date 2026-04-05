import time
import serial

PORT = 'COM5'
BAUD = 9600

SWITCH_REPORT_INTERVAL = 0.1
SWITCH_REPORT_THRESHOLD = 5.0
RELEASE_BYTE = b'.'
RELEASE_DURATION = 0.2
INTER_PRESS_GAP = 0.75


# --- Core helpers ---

def send(ser, byte):
    data = byte.encode() if isinstance(byte, str) else byte
    ser.write(data)
    ser.flush()


def neutral(ser, seconds):
    """Send neutral reports for a given duration — keeps Switch connected."""
    end_time = time.time() + seconds
    while time.time() < end_time:
        send(ser, RELEASE_BYTE)
        remaining = end_time - time.time()
        time.sleep(min(SWITCH_REPORT_INTERVAL, max(0, remaining)))


def tap(ser, button, gap=INTER_PRESS_GAP):
    """Send a single report with the button pressed, then release. True tap."""
    print(f"Tap {button!r}")
    send(ser, button)
    neutral(ser, RELEASE_DURATION + gap)


def press(ser, button, hold=0.4, gap=INTER_PRESS_GAP):
    """Press and hold a button for `hold` seconds, then release."""
    print(f"Press {button!r} (hold={hold}s, gap={gap}s)")

    # Hold
    end_time = time.time() + hold
    while time.time() < end_time:
        send(ser, button)
        remaining = end_time - time.time()
        time.sleep(min(SWITCH_REPORT_INTERVAL, max(0, remaining)))

    # Release + gap
    neutral(ser, RELEASE_DURATION + gap)


def wait(seconds, ser=None):
    if ser and seconds > SWITCH_REPORT_THRESHOLD:
        print(f"Wait {seconds}s (keeping Switch connected)")
        neutral(ser, seconds)
    else:
        print(f"Wait {seconds}s")
        time.sleep(seconds)


def wait_ms(ms, ser=None):
    print(f"Wait {ms}ms")
    wait(ms / 1000, ser=ser)


# --- Sequence Runner ---

def run_sequence(ser, sequence):
    for step in sequence:
        action = step[0]

        if action == "tap":
            _, button = step
            tap(ser, button)

        elif action == "press":
            if len(step) == 2:
                _, button = step
                press(ser, button)
            elif len(step) == 3:
                _, button, duration = step
                press(ser, button, hold=float(duration))
            elif len(step) == 4:
                _, button, hold, gap = step
                press(ser, button, hold=float(hold), gap=float(gap))
            else:
                raise ValueError(f"Invalid press step: {step}")

        elif action == "wait":
            _, seconds = step
            wait(float(seconds), ser=ser)

        elif action == "wait_ms":
            _, ms = step
            wait_ms(float(ms), ser=ser)

        elif action == "repeat":
            _, count, button, *rest = step
            total_time   = float(rest[0]) if len(rest) > 0 else None
            final_budget = float(rest[1]) if len(rest) > 1 else 0.0

            if total_time:
                usable_time = total_time - final_budget
                cycle = RELEASE_DURATION + INTER_PRESS_GAP
                hold_time = max(0.1, (usable_time / count) - cycle)
            else:
                hold_time = 0.4

            print(f"Repeat {button!r} x{count} (hold={hold_time:.3f}s, "
                  f"budget={total_time}s, reserved={final_budget}s)")
            for _ in range(count):
                press(ser, button, hold=hold_time)

        else:
            raise ValueError(f"Unknown action: {action}")


# --- Sequence ---

FINAL_PRESS_BUDGET = 0.8

sequence = [

    # ("tap", "A"),
    # ("wait", 1),
    # ("tap", "A"),
    # ("wait", 1.25),
    # ("tap", "H"),

    # ("wait", 2),
    ("tap", "A"),

    ("wait_ms", 30842),

    ("press", "A", 3),

    ("wait", 23.807),
    ("press", "A"),

    ("repeat", 8, "A", 10.406, FINAL_PRESS_BUDGET),
    ("press", "A"),
]


# --- Main ---

def main():
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        print("Starting sequence...")
        print("Waiting for Switch to register controller...")
        neutral(ser, 5.0)
        run_sequence(ser, sequence)
        print("Sequence completed!")


if __name__ == "__main__":
    main()