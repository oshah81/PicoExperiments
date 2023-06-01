# License: MIT
# Credit: https://github.com/oshah81/

# import machine
from time import sleep
import math
# import urequests
# import network

#layers
LAYER = [9,8,7,6]

#columns
GRID_3D = [[17, 16, 0, 1], 
           [19, 18, 2, 3],
           [21, 20, 4, 5],
           [26, 22, 28, 27]]

# Main program
def program():

    # Main program
    led_pattern = []
    # connect_to_wifi()
    led_pattern = get_led_pattern()

    while True:
        for frame in led_pattern:
            light_up_leds(frame)
            sleep(0.5)  # Wait for 0.5 second

def light_off(x, y, z):
    print(f"off ({x}, {y}, {z})")

def light_on(x, y, z):
    print(f"on ({x}, {y}, {z})")

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
            if len(depth) > 0:
                row.append(depth)

            frame.append(row)
            row = []
            depth = []
            col = []
            continue
 
    if len(depth) > 0:
        row.append(depth)

    frame.append(row)
    return frame

# Function to retrieve the LED pattern from a web server
def get_led_pattern() -> list[bool]:
    pattern_str = """0000 0000 0000 0000  0000 0000 0000 0000  0000 0000 0000 0000  0000 0000 0000 0000
1111 1111 1111 1111  1111 1111 1111 1111  1111 1111 1111 1111  1111 1111 1111 1111  1111 1111 1111 1111
1010 1010 1010 1010  1010 1010 1010 1010  1010 1010 1010 1010  1010 1010 1010 1010  1010 1010 1010 1010
0101 0101 0101 0101  0101 0101 0101 0101  0101 0101 0101 0101  0101 0101 0101 0101  0101 0101 0101 0101"""



    try:
        raise ConnectionError("Unable to connect.")
        with urequests.get("https://zoostorm.local/led_pattern.json") as response:
            pattern_str = response.text
    except:
        pass

    pattern = process_pattern_txt(pattern_str)
    return pattern

# Function to light up LEDs based on the pattern
def light_up_leds(pattern: list[bool]) -> None:

    for x in range(len(pattern)):
        row = pattern[x]
        for y in range(len(row)):
            col = row[y]
            for z in range(len(col)):
                switched = col[z]
                # print(f"({x}, {j}, {z}) is {switched}")
                if not switched:
                    light_off(x, y, z)
                else:
                    light_on(x, y, z)


    # Update the LEDs
    return


# Start the program
main()


