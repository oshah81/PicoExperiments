# License: MIT
# Credit: https://github.com/oshah81/

import machine
from time import sleep_ms
import urequests
import network
import socket
import rp2
import errno
import json


#layers
LAYER = [9,8,7,6]

#columns
GRID_3D = [[17, 16, 0, 1], 
           [19, 18, 2, 3],
           [21, 20, 4, 5],
           [26, 22, 28, 27]]

# Main program
def program(WIFI_SSID, WIFI_PASSWORD, COLOUR) -> None:

    try:
        while True:
            # Main program
            wifi = connect_to_wifi(WIFI_SSID, WIFI_PASSWORD)

            led_pattern = get_led_pattern(COLOUR)

            init_layers()

            clear_leds()
            sckt = tcpip_port(wifi)
            prog_loop(led_pattern, sckt)

            sckt.close()
            wifi.active(False)
            print("End of program. Restarting")
    except Exception as e:
        onboard = machine.Pin("LED", machine.Pin.OUT)
        onboard.on()
        raise e


def prog_loop(led_pattern: str, sckt: socket.socket) -> None:
    time_delta = 10
    current_time = 0
    led_time = 0

    while current_time < 3_600_000:
        for frame in led_pattern:
            # time will mostly be spend here
            restartFlag = read_socket(sckt)
            # Always restart after an hour

            if restartFlag:
                return
            sleep_ms(time_delta)
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

# Connect to the Wi-Fi network
def connect_to_wifi(ssid: str, pwd: str) -> network.WLAN:
    retries = 10
    wifi = network.WLAN(network.STA_IF)
    rp2.country('GB')
    wifi.active(True)

    isConnected = False
    wifi.connect(ssid, pwd)
    while True:
        print("wifi connecting")
        retries -= 1
        isConnected = wifi.isconnected()
        if isConnected:
            return wifi
        if retries <= 0:
            break
        sleep_ms(500)

    raise ConnectionError("wifi not connected")

def tcpip_port(wifi: network.WLAN) -> socket.socket:
    connection = socket.socket()
    connection.setblocking(False)
    addr = socket.getaddrinfo("0.0.0.0", 2028)[0][-1]
    connection.bind(addr)
    connection.listen(1)

    return connection

def read_socket(sckt: socket.socket) -> bool:
    try:
        retBytes = sckt.recv(1024)
        retStr = retBytes.decode()
        if retStr.startswith("1"):
            try:
                # send an ack packet
                sckt.send(b'c')
            except Exception as e1:
                print("socket terminated before could send ack frame")
            return True

    # Backcompat hack for handling timeouts in micropython
    except OSError as e:
        if e.errno in [errno.ETIMEDOUT, errno.EAGAIN]:
            return False
        raise e

    # # This is the proper way for handling timeouts:
    # 
    # except TimeoutError as e:
    #    return False

    # rogue data. Return false
    return False

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
    pattern_str = """1010 1010 1010 1010  1010 1010 1010 1010  1010 1010 1010 1010  1010 1010 1010 1010
0101 0101 0101 0101  0101 0101 0101 0101  0101 0101 0101 0101  0101 0101 0101 0101  """

    try:
        # raise ConnectionError("Unable to connect.")
        response = urequests.get(f"https://raw.githubusercontent.com/oshah81/PicoExperiments/main/ledpattern{colour}.txt")
        pattern_str = response.text
        print(f"pattern {colour} obtained.")
    except Exception as e:
        print(e)
        print("pattern not obtained. using fallback pattern")
        pass

    pattern = process_pattern_txt(pattern_str)
    print(f"pattern is {json.dumps(pattern)}")
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



