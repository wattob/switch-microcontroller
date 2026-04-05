import time
import serial

PORT = 'COM5'
BAUD = 9600

SWITCH_REPORT_INTERVAL = 0.1
SWITCH_REPORT_THRESHOLD = 5.0  # only send keepalive for waits longer than this
RELEASE_BYTE = b'.'
RELEASE_DURATION = 0.05
INTER_PRESS_GAP = 0.75         # 0.05 + 0.75 = 0.8s total per press, matching original


# --- Core helpers ---

def send(ser, byte):
    data = byte.encode() if isinstance(byte, str) else byte
    ser.write(data)
    ser.flush()


def press(ser, button, hold=0.4, release=RELEASE_DURATION, gap=INTER_PRESS_GAP):
    print(f"Press {button!r} (hold={hold}s, release={release}s, gap={gap}s)")
    end_time = time.time() + hold
    while time.time() < end_time:
        send(ser, button)
        remaining = end_time - time.time()
        time.sleep(min(SWITCH_REPORT_INTERVAL, max(0, remaining)))
    wait(release, ser=ser)
    if gap > 0:
        wait(gap, ser=ser)


def wait(seconds, ser=None):
    if ser and seconds > SWITCH_REPORT_THRESHOLD:
        print(f"Wait {seconds}s (keeping Switch connected)")
        end_time = time.time() + seconds
        while time.time() < end_time:
            send(ser, RELEASE_BYTE)
            remaining = end_time - time.time()
            time.sleep(min(SWITCH_REPORT_INTERVAL, max(0, remaining)))
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

        if action == "press":
            if len(step) == 2:
                _, button = step
                press(ser, button)
            elif len(step) == 3:
                _, button, duration = step
                press(ser, button, hold=float(duration))
            elif len(step) == 4:
                _, button, hold, release = step
                press(ser, button, hold=float(hold), release=float(release))
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
                press_cycle = RELEASE_DURATION + INTER_PRESS_GAP
                hold_time = max(0.05, (usable_time / count) - press_cycle)
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
    ("press", "H"),
    ("press", "A"),
    ("press", "A"),
    ("wait", 1.25),
    ("press", "H", 0.1),

    ("wait", 2),
    ("press", "A"),

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
        # Send neutral reports for 2s to let Switch finish handshake
        print("Waiting for Switch to register controller...")
        end_time = time.time() + 2.0
        while time.time() < end_time:
            send(ser, RELEASE_BYTE)
            time.sleep(SWITCH_REPORT_INTERVAL)
        run_sequence(ser, sequence)
        print("Sequence completed!")


if __name__ == "__main__":
    main()