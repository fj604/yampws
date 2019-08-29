import network
import webserver
import machine
import ubinascii
import utime

import urldecode       

CONNECTION_TIME_MS = 10000

def read_file(file_name):
    with open(file_name) as file:
        content = file.read()
        file.close()
    return content


def scan(method, path, query, body):
    template_file = "scan.phtml"
    
    authmode = {
        0: "Open",
        1: "WEP",
        2: "WPA-PSK",
        3: "WPA2-PSK",
        4: "WPA/WPA2-PSK"
    }

    template = read_file(template_file)

    sta = network.WLAN(network.STA_IF)
    networks = sta.scan()
    print("Networks:", networks)
    table = ""
    for net in networks:
        ssid = net[0].decode()
        channel = net[2]
        rssi = net[3]
        auth = authmode[net[4]]
        if net[4]:
            password = """
<input type="password" name="pwd" minlength="8" maxlength="63" required>
"""
        else:
            password = ""
        table += """
<form action="connect" method="POST">
<tr>
<td>{}</td>
<td>{}</td>
<td>{}</td>
<td>{}</td>
<td><input type="hidden" name="SSID" value="{}">{}</td>
<td><input type="Submit" value="Connect"></td>
</tr></form>""".format(ssid, channel, rssi, auth, ssid, password)
    return (200, {"Content-Type" : "text/html"}, template.format(table))


def connect(method, path, query, body):
    print("Connect handling Method:", method)
    if method == "POST":
        print("Connecting...")
        body_items = body.split("&")
        print("Request body items:", body_items)
        items = {}
        for item in body_items:
            values = item.split("=")
            if len(values) > 1:
                key = urldecode.decode(values.pop(0))
                value = "=".join(values)
                items[key.lower()] = urldecode.decode(value)
        print("Request parameters:",items)
        if "ssid" in items:
            ssid = items["ssid"]
            if "pwd" in items:
                pwd = items["pwd"]
            else:
                pwd = None
            print("Connecting to", ssid)
            sta = network.WLAN(network.STA_IF)
            sta.active(True)
            sta.connect(ssid, pwd)
            deadline = utime.ticks_add(utime.ticks_ms(), CONNECTION_TIME_MS)
            while utime.ticks_diff(deadline, utime.ticks_ms()) > 0 and not sta.isconnected():
                pass
            status = "Successfully connected" if sta.isconnected() else "Error connecting"
            status += " to " + ssid
            print(status)
        else:
            print("Bad request parameters")
            return (400, None, None)
        template_file = "connect.phtml"
        template = read_file(template_file)
        return (200, {"Content-Type" : "text/html"}, template.format(status))
    else:
        return (405, None, None)


def restart(method, path, query, body):
    if method == "POST":
        machine.reset()
    else:
        return (405, None, None)


handlers = {
    "/scan":scan,
    "/connect":connect,
    "/restart":restart
}


webserver.start(handlers=handlers)
