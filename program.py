# License: MIT
# Credit: https://github.com/oshah81/
# version 20230704

import machine
from time import sleep_ms, localtime
import ntptime
import urequests
import network
import rp2
import micropython

sckt = None
EndFlag = False



# Main program
def program(WIFI_SSID, WIFI_PASSWORD, COLOUR) -> None:
    global EndFlag
    EndFlag = False
    NightTime = False
    micropython.alloc_emergency_exception_buf(100)
    bootsel_timer = machine.Timer(-1)
    try:
        wifi = None
        try:
            bootsel_timer.init(period = 1000, mode = machine.Timer.PERIODIC, callback = bootsel_callback_entry)

            # Main program
            wifi = connect_to_wifi(WIFI_SSID, WIFI_PASSWORD)

            synctime()

            NightTime = is_night_time(localtime()[3], COLOUR)
            if not NightTime:
                script = get_script(COLOUR)

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

            if NightTime:
                print("Night mode. Sleeping for half an hour")
                wait_until(1000, 1_800_000)

            try:
                print("deiniting bootsel timer")
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

    print("resetting machine")
    machine.soft_reset()
    return

def synctime() -> None:
    print("Attempting to sync time")
    ntptime.host = "raspberrypi.local"
    ntptime.timeout = 1
    ntptime.settime()

def wait_until(poll_time: int, timeout: int) -> None:
    # todo, poll EndFlag 
    sleep_ms(timeout)

def is_night_time(utc_hour: int, colour: str) -> bool:
    if (colour == "C3"):
        return (utc_hour >= 21 or utc_hour <= 8)
    else:
        return (utc_hour >= 22 or utc_hour <= 7)


# Function to retrieve the LED pattern from a web server
def get_script(colour : str) -> str:
    print("retrieving script")
    response = urequests.get(f"https://raspberrypi.local/pico/ledscript{colour}.txt")
    script = response.text
    print(f"script {colour}, {len(script)} bytes.")

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
            print("wifi successfully connected")
            return wifi
        if retries <= 0:
            break
        sleep_ms(500)

    raise Exception("wifi not connected")


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


