# License: MIT
# Credit: https://github.com/oshah81/
# version 20240703

import machine
from time import sleep_ms
import ntptime
import requests
import network
import rp2
import micropython
import socket
import struct
import sys

EndFlag = False

# Main program
def program(WIFI_SSID, WIFI_PASSWORD, COLOUR) -> None:
    global EndFlag
    EndFlag = False
    micropython.alloc_emergency_exception_buf(100)
    bootsel_timer = machine.Timer(-1)
    onboard = machine.Pin("LED", machine.Pin.OUT)

    try:
        wifi = None
        try:
            bootsel_timer.init(period = 1000, mode = machine.Timer.PERIODIC, callback = bootsel_callback_entry)
            onboard.off()

            # Main program
            wifi = connect_to_wifi(WIFI_SSID, WIFI_PASSWORD)
            gatewayip = debugnetwork(wifi)

            script = get_script(COLOUR, gatewayip)

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

    except Exception as e:
        print(f"{type(e)} occurred, {e}.")
        sys.print_exception(e)
        onboard.on()
        wait_until(2000, 1_800_000)
        sleep_ms(1000)

    try:
        print("deiniting bootsel timer")
        bootsel_timer.deinit()
    except:
        pass
    print("resetting machine")
    machine.soft_reset()
    return


def wait_until(poll_time: int, timeout: int) -> None:
    global EndFlag
    nchecks = timeout // poll_time
    while (nchecks > 0):
        sleep_ms(poll_time)
        if (EndFlag):
            return
        nchecks -= 1

# Function to retrieve the LED pattern from a web server
def get_script(colour : str, gatewayip : str) -> str:
    print("retrieving script")
    response = requests.get(f"https://pi.hole/pico/ledscript{colour}.txt")
    script = response.text
    print(f"gateway {gatewayip}, script {colour}, {len(script)} bytes.")

    return script

# Here's where we mine the crypto. Sorry, I mean run the website code
def run_script(script: str, colour: str, endFlagger) -> None:
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
            print("wifi connected")
            wifi.config(pm=network.WLAN.PM_POWERSAVE)
            print("wifi successfully configured")
            return wifi
        if retries <= 0:
            break
        sleep_ms(500)

    raise Exception("wifi not connected")

def debugnetwork(wifi)-> str:
    ipaddr: str
    subnet : str
    gateway : str
    dns : str
    ipaddr, subnet, gateway, dns = wifi.ifconfig()
    print(f"Network info {ipaddr}, {subnet}, {gateway}, {dns}")
    return gateway

# implements bootsel reset button functionality
def bootsel_callback(instringing: str) -> None:
    global EndFlag
    if rp2.bootsel_button() == 1:
        print("BOOTSEL Button pressed")
        EndFlag = True

    return

# irql hack
def bootsel_callback_entry(timer: machine.Timer) -> None:
    micropython.schedule(bootsel_callback, "")
    return


