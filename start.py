import utime
import network

CONNECT_TIME_MS = 10000 

sta = network.WLAN(network.STA_IF)
print("Checking WIFI...")
deadline = utime.ticks_add(utime.ticks_ms(), CONNECT_TIME_MS)
while utime.ticks_diff(deadline, utime.ticks_ms()) > 0 and not sta.isconnected():
    pass
if sta.isconnected():
    print("Connected!")
    print("Starting LEDs...")
    import ledcontroller
else:
    print("No WiFi connection")
    print("Activating Access Point")
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    print("Starting Web Server")
    import wifi_connect