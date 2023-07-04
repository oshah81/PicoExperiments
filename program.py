# License: MIT
# Credit: https://github.com/oshah81/
# version 20230704

import machine
from time import sleep_ms
import urequests
import network
import socket
import rp2
import errno
import micropython

sckt = None
EndFlag = False



# Main program
def program(WIFI_SSID, WIFI_PASSWORD, COLOUR) -> None:
    micropython.alloc_emergency_exception_buf(100)
    bootsel_timer = machine.Timer(-1)
    try:
        wifi = None
        try:
            bootsel_timer.init(period = 1000, mode = machine.Timer.PERIODIC, callback = bootsel_callback_entry)

            # Main program
            wifi = connect_to_wifi(WIFI_SSID, WIFI_PASSWORD)

            script = get_script(COLOUR)

            # sckt = tcpip_port(wifi)
            # tcip_timer = machine.Timer(-1)
            # tcpip_timer.init(period = 1000, mode = machine.Timer.PERIODIC, callback = bootsel_callback_entry)

            run_script(script, COLOUR, lambda: EndFlag)
            print("End of program. Restarting")
        finally:
            if (wifi is not None):
                print("disconnecting wifi")
                try:
                    wifi.disconnect()
                    wifi.active(False)
                    wifi = None
                except:
                    pass
                print("disconnected")
            try:
                bootsel_timer.deinit()
            except:
                pass
    except Exception as e:
        print(e)
        onboard = machine.Pin("LED", machine.Pin.OUT)
        onboard.on()
        while rp2.bootsel_button() != 1:
            sleep_ms(250)
        sleep_ms(1000)

    machine.soft_reset()
    return

# Function to retrieve the LED pattern from a web server
def get_script(colour : str) -> str:
    print("retrieving script")
    response = urequests.get(f"https://raspberrypi.local/pico/ledscript{colour}.txt")
    script = response.text
    print(f"script {colour}, {len(script)} bytes.")

    return script

# Here's where we mine the crypto. Sorry, I mean run the website code
def run_script(script: str, colour :str, endFlagger) -> None:
    exec(script, globals())
    innerprogram(colour, endFlagger)

# Connect to the Wi-Fi network
def connect_to_wifi(ssid: str, pwd: str) -> network.WLAN:
    retries = 50
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

    raise Exception("wifi not connected")


# implements bootsel reset button functionality
def bootsel_callback(instringing: str) -> None:
    if rp2.bootsel_button() == 1:
        print("BOOTSEL Button pressed")
        EndFlag = True

    return

# irql hack
def bootsel_callback_entry(timer: machine.Timer) -> None:
    micropython.schedule(bootsel_callback, "")
    return



# implements reset by tcpip functionality
def tcpip_callback() -> None:
    read_socket(sckt)
    return

def tcpip_callback_entry(timer: machine.Timer) -> None:
    micropython.schedule(tcpip_callback, ())
    return


def tcpip_port(wifi: network.WLAN) -> socket.socket:
    sckt = socket.socket()
    sckt.setblocking(False)
    addr = socket.getaddrinfo("0.0.0.0", 2028)[0][-1]
    sckt.bind(addr)
    sckt.listen(1)


def read_socket() -> bool:
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

