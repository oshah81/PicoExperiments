# License: MIT
# Credit: https://github.com/oshah81/

import machine
from time import sleep
import urequests
import network
import socket


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

            led_pattern = get_led_pattern(WIFI_SSID, WIFI_PASSWORD, COLOUR)

            init_layers()

            clear_leds()
            with tcpip_port(wifi) as sckt:
                prog_loop(led_pattern, sckt)


            wifi.active(False)
            print("Reset received. Restarting program")
    except Exception as e:
        onboard = machine.Pin("LED", machine.Pin.OUT)
        onboard.on()
        raise e


def prog_loop(led_pattern: str, sckt: socket.socket) -> None:
    while True:
        for frame in led_pattern:
            light_up_leds(frame)
            restartFlag = read_socket(sckt, 0.02)
            if restartFlag:
                return


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
            sleep(0)

# Connect to the Wi-Fi network
def connect_to_wifi(ssid: str, pwd: str) -> network.WLAN:
    retries = 10
    wifi = network.WLAN(network.STA_IF)
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
        sleep(0.5)

    raise ConnectionError("wifi not connected")

def tcpip_port(wifi: network.WLAN) -> socket.socket:
    ip = wifi.ifconfig()[0]
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.settimeout(0.1)
    connection.bind(ip, 2028)
    connection.listen(1)

    return connection

def read_socket(sckt: socket.socket, timeout: int) -> bool:
    try:
        sckt.settimeout(timeout)
        retBytes = sckt.recv(1024)
        retStr = retBytes.decode()
        if retStr.startswith("1"):
            try:
                # send an ack packet
                sckt.send(b'c')
            except Exception as e1:
                print("socket terminated before could send ack frame")
            return True

    except socket.timeout as e:
        return False

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
    pattern_str = """0000 0000 0000 0000  0000 0000 0000 0000  0000 0000 0000 0000  0000 0000 0000 0000
1111 1111 1111 1111  1111 1111 1111 1111  1111 1111 1111 1111  1111 1111 1111 1111
1010 1010 1010 1010  1010 1010 1010 1010  1010 1010 1010 1010  1010 1010 1010 1010
0101 0101 0101 0101  0101 0101 0101 0101  0101 0101 0101 0101  0101 0101 0101 0101  """

    try:
        # raise ConnectionError("Unable to connect.")
        response = urequests.get(f"https://raw.githubusercontent.com/oshah81/PicoExperiments/main/ledpattern{colour}.txt")
        pattern_str = response.text
        print(f"pattern {colour} obtained. Disconnecting wifi")
    except Exception as e:
        print(e)
        print("pattern not obtained. using fallback pattern")
        pass

    pattern = process_pattern_txt(pattern_str)
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

