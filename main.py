import utime
import machine
try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct


addr      = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
# (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
NTP_DELTA = 3155673600
host      = "pool.ntp.org"
led       = machine.Pin(2, machine.Pin.OUT)


def get_time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1b
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1)
    res = s.sendto(NTP_QUERY, addr)
    msg = s.recv(48)
    s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    return val


def time_delta():
    return get_time() - NTP_DELTA


# There's currently no timezone support in MicroPython, so
# utime.localtime() will return UTC time (as if it was .gmtime())
def settime():
    t = time_delta()
    import machine
    import utime
    tm = utime.localtime(t)
    tm = tm[0:3] + (0,) + tm[3:6] + (0,)
    machine.RTC().datetime(tm)


def init_web():
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('listening on', addr)
    return s


def web_server(s):
    led.on()
    pins = [machine.Pin(i, machine.Pin.IN) for i in (0, 2, 4, 5, 12, 13, 14, 15)]
    html = """
    <!DOCTYPE html>
    <html>
        <head><title>ESP8266</title></head>
        <body> 
        <h1>ESP8266 Pins</h1>
        <h2>Time: {}</h2>
            <table border="1"> <tr><th>Pin</th><th>Value</th></tr> %s </table>
        </body>
    </html>
     """.format(utime.localtime())

    cl, addr = s.accept()
    print('client connected from', addr)
    cl_file = cl.makefile('rwb', 0)
    while True:
        line = cl_file.readline()
        if not line or line == b'\r\n':
            break
    rows = ['<tr><td>%s</td><td>%d</td></tr>' % (str(p), p.value()) for p in pins]
    response = html % '\n'.join(rows)
    cl.send(response)
    cl.close()
    led.off()


def do_connect():
    import network
    import time
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('Fuxbau', 'JuV30062013')
        while not sta_if.isconnected():
            print(".", end="")
            time.sleep(.25)
    print('network config:', sta_if.ifconfig())


def set_device_time(new_time):
    rtc = machine.RTC()
    rtc.datetime(new_time)
    print("Current persistent time: {}".format(rtc.datetime()))


def manage_time():
    settime()
    print("New device time: {}".format(utime.localtime()))
    set_device_time(utime.localtime())


def main():
    do_connect()
    manage_time()
    s   = init_web()
    now = utime.time()
    while True:
        if utime.time() > now + 5000:
            now = utime.time()
        rtc = machine.RTC()
        print(rtc.datetime())
        web_server(s)


if __name__ == '__main__':
    main()
