from __future__ import annotations

import argparse
import contextlib
import sys
import time
from typing import Generator

import cv2
import numpy
import serial

import smtplib
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv
import os

# using the script 
# cd .\OneDrive\Documents\GitHub\switch-microcontroller\scripts\bdsp\
# open switch-microcontroller root
# cd .\scripts\bdsp\
# python3 .\starter_reset.py

# Use load_env to trace the path of .env
load_dotenv('../../.env') 

# find serial bus controller in Device Manager for COM Ports on your devices
SERIAL_DEFAULT = 'COM3' if sys.platform == 'win32' else '/dev/ttyUSB0'

def sendEmail(count):
    # Define email sender and receiver
    # Get the values of the variables from .env using the os library
    email_sender = os.environ.get("email_sender")
    email_password = os.environ.get("email_password")
    email_receiver = os.environ.get("email_receiver")
    starter_choice = os.environ.get("starter_choice")

    # Set the subject and body of the email
    subject = 'Check out the shiny encounter!'
    body = f"""Currently shiny hunting {starter_choice}! Finally encountered a shiny at {count} resets!"""

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())

def _press(ser: serial.Serial, s: str, duration: float = .1) -> None:
    print(f'{s=} {duration=}')
    ser.write(s.encode())
    time.sleep(duration)
    ser.write(b'0')
    time.sleep(.075)


def _getframe(vid: cv2.VideoCapture) -> numpy.ndarray:
    _, frame = vid.read()
    cv2.imshow('game', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        raise SystemExit(0)
    # will show RGB and X and Y coords for troubleshooting
    def mouse_pos_BGR(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN: # Left mouse click
            
            B = frame[y,x,0]
            G = frame[y,x,1]
            R = frame[y,x,2]
        
            print("Blue: ", B)
            print("Green: ", G)
            print("Red: ", R)        

            print("Coords x: ", x," y: ", y)
    cv2.namedWindow('game')
    cv2.setMouseCallback('game',mouse_pos_BGR)
    return frame


def _wait_and_render(vid: cv2.VideoCapture, t: float) -> None:
    end = time.time() + t
    while time.time() < end:
        _getframe(vid)


def _alarm(ser: serial.Serial, vid: cv2.VideoCapture) -> None:
    while True:
        ser.write(b'!')
        _wait_and_render(vid, .5)
        ser.write(b'.')
        _wait_and_render(vid, .5)


def _await_pixel(
        ser: serial.Serial,
        vid: cv2.VideoCapture,
        *,
        x: int,
        y: int,
        pixel: tuple[int, int, int],
        timeout: float = 90,
) -> None:
    end = time.time() + timeout
    frame = _getframe(vid)
    while not numpy.array_equal(frame[y][x], pixel):
        frame = _getframe(vid)
        if time.time() > end:
            _alarm(ser, vid)


def _await_not_pixel(
        ser: serial.Serial,
        vid: cv2.VideoCapture,
        *,
        x: int,
        y: int,
        pixel: tuple[int, int, int],
        timeout: float = 90,
) -> None:
    end = time.time() + timeout
    frame = _getframe(vid)
    while numpy.array_equal(frame[y][x], pixel):
        frame = _getframe(vid)
        if time.time() > end:
            _alarm(ser, vid)


def _color_near(pixel: numpy.ndarray, expected: tuple[int, int, int]) -> bool:
    total = 0
    for c1, c2 in zip(pixel, expected):
        total += (c2 - c1) * (c2 - c1)
        
    return total < 76


@contextlib.contextmanager
def _shh(ser: serial.Serial) -> Generator[None, None, None]:
    try:
        yield
    finally:
        ser.write(b'.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    vid = cv2.VideoCapture(0)
    vid.set(cv2.CAP_PROP_FRAME_WIDTH, 768)
    vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    i = 2039
     # running number for the count of resets
    # Variable for starter CHOICE!
    starterChoice = os.environ.get("starter_choice")
    print(' starter Choice ', starterChoice)

    with serial.Serial(args.serial, 9600) as ser, _shh(ser):
        while True:
            i = i + 1
            print(' total count: ', i)
            _press(ser, 'H')
            _wait_and_render(vid, 1)
            _press(ser, 'X')
            _wait_and_render(vid, 1)
            _press(ser, 'A')
            _wait_and_render(vid, 3.5)
            _press(ser, 'A')
            _wait_and_render(vid, 1)
            _press(ser, 'A')
            print('Loading screen!')
            frame = _getframe(vid)
            while not _color_near(frame[57][659], (248, 248, 248)): #bgr?  checks for dirt spot on ground, may break during day night or player positioning

            # while not _color_near(frame[627][1074], (91, 151, 189)): #bgr?  checks for dirt spot on ground, may break during day night or player positioning
                _wait_and_render(vid, .15)
                _press(ser, 'A')
                frame = _getframe(vid)

            print('game loaded!')

            _press(ser, 'w', duration=.5)
            # bashes A through dialogue 
            # while not _color_near(frame[213][911], (38, 42, 85)): #bgr? checks for the bag background
            # while not _color_near(frame[155][574], (25, 39, 106)): #sunset
            while not _color_near(frame[423][1003], (243, 243, 243)): # turtwig background (at sunset)

                _wait_and_render(vid, .15)
                _press(ser, 'A')
                frame = _getframe(vid)
            # _press(ser, 'A')

            # Variable for starter CHOICE!
            # _wait_and_render(vid, 2)
            # _press(ser, 'A')

            if (starterChoice == 'turtwig'): # clean up efficiency
                # _wait_and_render(vid, 1.75)
                # _press(ser, 'A')
                _wait_and_render(vid, 1.0)
                _press(ser, 'w')
                _wait_and_render(vid, 1.0)
                _press(ser, 'A')


                # _wait_and_render(vid, 1.75)
                # _press(ser, 'A')
                # _wait_and_render(vid, 1.75)
                # _press(ser, 'w')
                # _wait_and_render(vid, 1.75)
                # _press(ser, 'A')

            if (starterChoice == 'chimchar'):
                _wait_and_render(vid, 1)
                _press(ser, 'd') 
                _wait_and_render(vid, 1)
                _press(ser, 'A')
                _wait_and_render(vid, 1)
                _press(ser, 'w')
                _wait_and_render(vid, 1)
                _press(ser, 'A')

            if (starterChoice == 'piplup'):
                _wait_and_render(vid, 1)
                _press(ser, 'a')
                _wait_and_render(vid, 1)
                _press(ser, 'A')
                _wait_and_render(vid, 1)
                _press(ser, 'w')
                _wait_and_render(vid, 1)
                _press(ser, 'A')

            print('started battle!')

            _wait_and_render(vid, 1)

            _await_pixel(ser, vid, x=900, y=900, pixel=(254, 254, 254))
            print('dialog started')
            _await_not_pixel(ser, vid, x=900, y=900, pixel=(254, 254, 254))

            print('dialog ended')

            t0 = time.time()

            _await_pixel(ser, vid, x=900, y=900, pixel=(254, 254, 254))
            print('2nd dialog started')
            # _await_not_pixel(ser, vid, x=900, y=900, pixel=(254, 254, 254)) #need?

            t1 = time.time()
            print(f'dialog delay: {t1 - t0:.3f}s')

            if (t1 - t0) > 1:
                print('SHINY!!!')
                # shiny uncatchable bird
                sendEmail(i) # TODO: Customize alerts or ignore shiny bird completely
                _alarm(ser, vid)

            _await_pixel(ser, vid, x=268, y=915, pixel=(248, 248, 248))
            t2 = time.time()
            print('2nd dialog ended')

            print(f'2nd dialog delay: {t2 - t1:.3f}s')
            if (t2 - t1) > 5: # 7.5 to filter out strange errors... or at least 7.1... Idk what real shiny would be
                # shiny starter
                print('SHINY!!!')
                sendEmail(i) 
                _alarm(ser, vid)


                
# reael shiny
#                 started battle!
# dialog started
# dialog ended
# 2nd dialog started
# dialog delay: 0.536s
# 2nd dialog ended
# 2nd dialog delay: 7.533s
# SHINY!!!

    vid.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())