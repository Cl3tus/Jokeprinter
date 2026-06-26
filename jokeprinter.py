#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import requests
import random
import textwrap
import os
import threading
import queue
from escpos.printer import Usb

VENDOR_ID    = 0x4b43
PRODUCT_ID   = 0x3830
BUTTON_PIN   = 17
TEST_MODE    = False  # Set to True for Enter key testing
OFFLINE_MODE = False  # Set to True to force offline jokes
LINE_WIDTH   = 24
MAX_QUEUE    = 10     # Maximum jokes queued up at once
STARTUP_BEEP = True   # Set to False to disable startup beeps

DAD_JOKES_FILE = os.path.join(os.path.dirname(__file__), "jokes_dad.txt")
IT_JOKES_FILE  = os.path.join(os.path.dirname(__file__), "jokes_it.txt")

def load_jokes(filepath):
    try:
        with open(filepath, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Failed to load jokes from {filepath}: {e}")
        return []

OFFLINE_DAD_JOKES = load_jokes(DAD_JOKES_FILE)
OFFLINE_IT_JOKES  = load_jokes(IT_JOKES_FILE)

def wrap_text(text):
    lines = []
    for line in text.splitlines():
        if line.strip() == "":
            lines.append("")
        else:
            wrapped = textwrap.wrap(line, width=LINE_WIDTH)
            for w in wrapped:
                lines.append(w.center(LINE_WIDTH))
    return "\n".join(lines)

def beep(count=1, duration=2, delay=0.3):
    try:
        for _ in range(count):
            p = Usb(VENDOR_ID, PRODUCT_ID, 0, out_ep=0x03, in_ep=0x81)
            p._raw(bytes([0x1b, 0x42, 0x01, duration]))
            p.close()
            if count > 1:
                time.sleep(delay)
    except Exception as e:
        print(f"Beep error: {e}")

def has_internet():
    try:
        requests.get("https://icanhazdadjoke.com/", timeout=3)
        return True
    except Exception:
        return False

def get_dad_joke_online():
    response = requests.get(
        "https://icanhazdadjoke.com/",
        headers={"Accept": "application/json"},
        timeout=5
    )
    return "DAD JOKE", response.json()["joke"]

def get_it_joke_online():
    response = requests.get(
        "https://v2.jokeapi.dev/joke/Programming",
        timeout=5
    )
    data = response.json()
    if data["type"] == "single":
        return "IT JOKE", data["joke"]
    else:
        return "IT JOKE", f"{data['setup']}\n\n{data['delivery']}"

def get_dad_joke_offline():
    if OFFLINE_DAD_JOKES:
        return "DAD JOKE", random.choice(OFFLINE_DAD_JOKES)
    return "DAD JOKE", "Why can't ghosts lie? Because you can see right through them!"

def get_it_joke_offline():
    if OFFLINE_IT_JOKES:
        return "IT JOKE", random.choice(OFFLINE_IT_JOKES)
    return "IT JOKE", "Why do programmers prefer dark mode? Because light attracts bugs."

def get_joke():
    if OFFLINE_MODE:
        print("Offline mode: using local joke database...")
        fetcher = random.choice([get_dad_joke_offline, get_it_joke_offline])
        return fetcher()

    print("Checking internet connection...")
    if has_internet():
        print("Online: fetching joke from internet...")
        try:
            fetcher = random.choice([get_dad_joke_online, get_it_joke_online])
            return fetcher()
        except Exception as e:
            print(f"Online fetch failed: {e}, falling back to offline...")
    else:
        print("No internet, falling back to offline...")

    fetcher = random.choice([get_dad_joke_offline, get_it_joke_offline])
    return fetcher()

def print_joke():
    category, joke = get_joke()
    p = None
    try:
        p = Usb(VENDOR_ID, PRODUCT_ID, 0, out_ep=0x03, in_ep=0x81)
        p.set(align='center', bold=True, double_height=True, double_width=True)
        p.text(f"** {category} **\n\n")
        p.set(align='center', bold=False, double_height=False, double_width=False)
        p.text(wrap_text(joke) + "\n\n\n")
        p.cut()
        print(f"Printed [{category}]: {joke[:50]}...")
    except Exception as e:
        print(f"Print error: {e}")
    finally:
        try:
            if p:
                p.close()
        except:
            pass

def printer_worker(print_queue):
    """Runs in background thread, prints jokes from queue one by one."""
    while True:
        print_queue.get()
        print_joke()
        print_queue.task_done()

def main():
    print_queue = queue.Queue(maxsize=MAX_QUEUE)

    # Start background printer thread
    worker = threading.Thread(target=printer_worker, args=(print_queue,), daemon=True)
    worker.start()

    if TEST_MODE:
        print(f"Running in TEST MODE ({'OFFLINE' if OFFLINE_MODE else 'ONLINE with fallback'}) - press Enter to print a joke, Ctrl+C to quit.")
        if STARTUP_BEEP: beep(count=3, duration=2, delay=0.3)
        try:
            while True:
                input("Press Enter to print a joke...")
                if not print_queue.full():
                    print_queue.put(1)
                    print(f"Queued! ({print_queue.qsize()}/{MAX_QUEUE} in queue)")
                else:
                    print(f"Queue full! ({MAX_QUEUE} max), ignoring press.")
        except KeyboardInterrupt:
            print("\nBye!")
    else:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print(f"Joke printer ready ({'OFFLINE' if OFFLINE_MODE else 'ONLINE with fallback'})! Press the button.")
        if STARTUP_BEEP: beep(count=3, duration=2, delay=0.3)

        last_press = 0
        debounce_ms = 300  # ignore presses within 300ms of each other

        try:
            while True:
                if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                    now = time.time() * 1000
                    if now - last_press > debounce_ms:
                        last_press = now
                        if not print_queue.full():
                            print_queue.put(1)
                            print(f"Button pressed! ({print_queue.qsize()}/{MAX_QUEUE} in queue)")
                        else:
                            print(f"Queue full! ({MAX_QUEUE} max), ignoring press.")
                time.sleep(0.01)
        except KeyboardInterrupt:
            pass
        finally:
            GPIO.cleanup()

if __name__ == "__main__":
    main()
