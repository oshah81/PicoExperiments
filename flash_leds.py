# License: MIT
# Credit: https://github.com/oshah81/
# version 20230602

import machine
from time import sleep_ms
import urequests
import json


#layers
LAYER = [9,8,7,6]

#columns
GRID_3D = [[17, 16, 0, 1], 
           [19, 18, 2, 3],
           [21, 20, 4, 5],
           [26, 22, 28, 27]]

# Main program
def innerprogram(COLOUR :str, endFlagger) -> None:

    # Main program
    led_pattern = get_led_pattern(COLOUR)

    init_layers()

    clear_leds()
    prog_loop(led_pattern, endFlagger)


def prog_loop(led_pattern: str, endFlagger) -> None:
    time_delta = 10
    current_time = 0
    led_time = 0

    while current_time < 3600000:
        for frame in led_pattern:
            # Always restart after an hour
            sleep_ms(time_delta)
            if endFlagger():
                break
            current_time += time_delta
            if (current_time - led_time > 250):
                # Update LEDs
                led_time += 250
                light_up_leds(frame)


def init_layers() -> None:
    onboard = machine.Pin("LED", machine.Pin.OUT)
    onboard.off()

    for pin in LAYER:
        machine.Pin(pin, machine.Pin.OUT)

    for x in range(4):
        for z in range(4):
            machine.Pin(GRID_3D[x][z], machine.Pin.OUT)


def enable_layer(layer: int) -> None:
    a = machine.Pin(LAYER[layer])
    a.on()

def disable_layer(layer: int) -> None:
    a = machine.Pin(LAYER[layer])
    a.off()

def light_on(y: int, x: int, z: int) -> None:
    enable_layer(y)
    a = machine.Pin(GRID_3D[x][z])
    a.on()
    
def light_off(y: int, x: int, z: int) -> None:
    enable_layer(y)
    a = machine.Pin(GRID_3D[x][z])
    a.off()

def clear_leds() -> None:
    
    for x in range(4):
        for z in range(4):
            a = machine.Pin(GRID_3D[x][z])
            a.off()
            sleep_ms(0)

# Turns a plain text string into a pattern string suitable for light_up_leds
def process_pattern_txt(pattern: str) -> list[bool]:
    flag = False
    frame = []
    row = []
    depth = []
    col = []
    for c in pattern:
        if c == " ":
            if not flag:
                flag = True
                depth.append(col)
                col = []
            else:
                flag = False
                row.append(depth)
                depth = []
                col = []
                continue
        else:
            flag = False
            
        if c == "0":
            col.append(False)
            continue
        if c == "1":
            col.append(True)
            continue
        if c == "\r":
            continue
        if c == "\n":
            if len(col) > 0:
                depth.append(col)
            if len(depth) > 0:
                row.append(depth)

            frame.append(row)
            row = []
            depth = []
            col = []
            continue
 
    if len(col) > 0:
        depth.append(col)
    if len(depth) > 0:
        row.append(depth)

    frame.append(row)
    return frame

# Function to retrieve the LED pattern from a web server
def get_led_pattern(colour : str) -> list[bool]:
    pattern_str = """1111 1111 1111 1111  1111 1111 1111 1111  1111 1111 1111 1111
1111 1111 1111 1111  1111 1111 1111 1111  1111 1111 1111 1111  """

    try:
        # raise OSError("Unable to connect.")
        response = urequests.get(f"https://raw.githubusercontent.com/oshah81/PicoExperiments/main/ledpattern{colour}.txt")
        pattern_str = response.text
        print(f"pattern {colour} obtained.")
    except Exception as e:
        print(e)
        print("pattern not obtained. using fallback pattern")
        pass

    pattern = process_pattern_txt(pattern_str)
    parsed_pattern = json.dumps(pattern).replace("]", "]\n")
    print(f"pattern is {parsed_pattern}")
    return pattern

# Function to light up LEDs based on the pattern
def light_up_leds(pattern: list[bool]) -> None:

    for x in range(4):
        for y in range(4):
            for z in range(4):
                # print(f"({x}, {y}, {z}) is {pattern[x][y]}")
                switched = pattern[x][y][z]
                if not switched:
                    light_off(x, y, z)
                else:
                    light_on(x, y, z)

    # Update the LEDs
    return

