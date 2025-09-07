# License: MIT
# Credit: https://github.com/oshah81/
# version 20230602

import machine
from time import sleep_ms
import requests
import json

# Requires Python 3.12
# type LEDArray = list[list[list[bool]]]

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
    init_layers()
    clear_leds()

    led_pattern = get_led_pattern(COLOUR)
    if not is_night_time(COLOUR):
        prog_loop(led_pattern, endFlagger)
        clear_leds()
    else:
        night_wait(2000, 1_800_000, endFlagger)
    return

def night_wait(poll_time, timeout, endFlagger):
    nchecks = timeout // poll_time
    while (nchecks > 0):
        sleep_ms(poll_time)
        if (endFlagger()):
            return
        nchecks -= 1


def prog_loop(led_pattern: list[list[list[list[bool]]]], endFlagger) -> None:
    time_delta = 10
    current_time = 0
    led_time = 0

    while current_time < 3600000:
        for frame in led_pattern:
            # Always restart after an hour
            sleep_ms(time_delta)
            if endFlagger():
                return
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

def is_night_time(colour) -> bool:
    status : int
    datestr : str
    response = requests.get(f"https://pi.hole/tpbulb/timestr.flask")
    response_txt = response.text
    print(f"timestr returned {response_txt}")
    json_struct = json.loads(response_txt)
    status = int(json_struct["status"])

    if status != 0:
        print(f"datetime api returned error")
        return False

    datestr = json_struct["datestr"]
    # cur_hour = datetime.fromisoformat(date).hour
    cur_hour = get_timezone_corrected_hour(datestr)

    # blue turns off one hour earlier
    is_night = \
        (cur_hour < 8 or cur_hour > 21) \
        if colour == "C3" else \
        (cur_hour < 7 or cur_hour > 22)

    print(f"current hour of {cur_hour}, means {'night' if is_night else 'day'}")
    if is_night:
        print("Night mode. Sleeping for half an hour")
    return is_night

# Turns a plain text string into a pattern string suitable for light_up_leds
def process_pattern_txt(pattern: str) -> list[list[list[list[bool]]]]:
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
def get_led_pattern(colour : str) -> list[list[list[list[bool]]]]:
    pattern_str = """1111 1111 1111 1111  1111 1111 1111 1111  1111 1111 1111 1111
1111 1111 1111 1111  1111 1111 1111 1111  1111 1111 1111 1111  """

    try:
        # raise OSError("Unable to connect.")
        response = requests.get(f"https://raw.githubusercontent.com/oshah81/PicoExperiments/main/ledpattern{colour}.txt")
        pattern_str = response.text
        print(f"pattern {colour} obtained.")
    except Exception as e:
        print(e)
        print("pattern not obtained. using fallback pattern")

    pattern = process_pattern_txt(pattern_str)
    parsed_pattern = json.dumps(pattern).replace("]", "]\n")
    print(f"pattern is {parsed_pattern}")
    return pattern

# Function to light up LEDs based on the pattern
def light_up_leds(pattern: list[list[list[bool]]]) -> None:

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




# datetime reimplementation:
#
# All because Micropython doesn't have datetime.fromisoformat().
#
# Fine I'll vibe code it myself.
#
# prompt from Claude AI:
# I need to parse a ISO 8601 datetime that was sent from a python web server using datetime.toisoformat(). And in the client,
# I need to parse out that datetime to extract the (timezone corrected) hour from it. However, the client is using Micropython,
# where datetime.fromisoformat() is not available. That means you need to rebuild datetime.fromisoformat() from scratch - but you
# can take shortcuts in validation because I can guarantee that the only datetime you need to read is one generated from a full
# python datetime.toisoformat()
# further commands dealt with standardising comments, removing the re import and not using ljust (also unavailable in micropython).

def parse_isoformat(iso_string):
    # Parse ISO 8601 datetime string generated by Python's datetime.isoformat()
    # Returns a tuple: (year, month, day, hour, minute, second, microsecond, tz_offset_seconds)
    
    # Remove 'T' separator and split date/time parts
    if 'T' in iso_string:
        date_part, time_part = iso_string.split('T')
    else:
        # Handle space separator (alternative format)
        date_part, time_part = iso_string.split(' ')
    
    # Parse date part: YYYY-MM-DD
    year, month, day = map(int, date_part.split('-'))
    
    # Handle timezone offset
    tz_offset_seconds = 0
    if '+' in time_part:
        time_part, tz_part = time_part.rsplit('+', 1)
        tz_offset_seconds = parse_timezone_offset('+' + tz_part)
    elif time_part.count('-') > 0 and time_part.rfind('-') > 2:  # Avoid date separator
        time_part, tz_part = time_part.rsplit('-', 1)
        tz_offset_seconds = parse_timezone_offset('-' + tz_part)
    elif time_part.endswith('Z'):
        time_part = time_part[:-1]
        tz_offset_seconds = 0
    
    # Parse time part: HH:MM:SS[.ffffff]
    time_components = time_part.split(':')
    hour = int(time_components[0])
    minute = int(time_components[1])
    
    # Handle seconds and microseconds
    second = 0
    microsecond = 0
    if len(time_components) > 2:
        sec_part = time_components[2]
        if '.' in sec_part:
            sec_str, microsec_str = sec_part.split('.')
            second = int(sec_str)
            # Pad or truncate to 6 digits
            while len(microsec_str) < 6:
                microsec_str += '0'
            microsec_str = microsec_str[:6]
            microsecond = int(microsec_str)
        else:
            second = int(sec_part)
    
    return (year, month, day, hour, minute, second, microsecond, tz_offset_seconds)

def parse_timezone_offset(tz_str):
    # Parse timezone offset string like +05:30 or -08:00
    # Returns offset in seconds
    
    if tz_str in ('Z', '+00:00', '-00:00'):
        return 0
    
    sign = 1 if tz_str[0] == '+' else -1
    tz_str = tz_str[1:]  # Remove sign
    
    if ':' in tz_str:
        hours, minutes = map(int, tz_str.split(':'))
    else:
        # Handle formats like +0530 or +05
        if len(tz_str) == 4:
            hours = int(tz_str[:2])
            minutes = int(tz_str[2:])
        elif len(tz_str) == 2:
            hours = int(tz_str)
            minutes = 0
        else:
            hours = int(tz_str)
            minutes = 0
    
    return sign * (hours * 3600 + minutes * 60)

def get_timezone_corrected_hour(iso_string):
    # Extract the timezone-corrected hour from an ISO 8601 datetime string
    # Returns the hour (0-23) adjusted for the timezone
    
    year, month, day, hour, minute, second, microsecond, tz_offset_seconds = parse_isoformat(iso_string)
    
    # Convert to total minutes for easier calculation
    total_minutes = hour * 60 + minute
    
    # Adjust for timezone (convert offset to minutes)
    tz_offset_minutes = tz_offset_seconds // 60
    total_minutes += tz_offset_minutes
    
    # Handle day rollover
    total_minutes = total_minutes % (24 * 60)
    if total_minutes < 0:
        total_minutes += 24 * 60
    
    # Extract the corrected hour
    corrected_hour = total_minutes // 60
    
    return corrected_hour

