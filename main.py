import utime
import machine
try:
    import usocket as socket
except ImportError:
    import socket
try:
    import ustruct as struct
except ImportError:
    import struct


ADDR      = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
# (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
NTP_DELTA = 3155673600 + 7200
host      = "pool.ntp.org"
LED       = machine.Pin(2, machine.Pin.OUT)


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
def set_time():
    t = time_delta()
    tm = utime.localtime(t)
    tm = tm[0:3] + (0,) + tm[3:6] + (0,)
    machine.RTC().datetime(tm)


def init_web(ip):
    s = socket.socket()
    s.bind(ADDR)
    s.listen(1)
    print('listening on', ip, ":", ADDR[1])
    return s


def web_server(s, pins):
    LED.on()
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

    cl, ADDR = s.accept()
    print('client connected from', ADDR)
    cl_file = cl.makefile('rwb', 0)
    while True:
        line = cl_file.readline()
        if not line or line == b'\r\n':
            break
    rows = ['<tr><td>%s</td><td>%d</td></tr>' % (str(p), p.value()) for p in pins]
    response = html % '\n'.join(rows)
    cl.send(response)
    cl.close()
    LED.off()


def do_connect():
    import network

    LED.on()
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('Fuxbau', 'JuV30062013')
        while not sta_if.isconnected():
            print(".", end="")
            utime.sleep_ms(300)
    ips = sta_if.ifconfig()
    print('network config:', ips)
    LED.off()
    return ips[0]


def set_device_time(new_time):
    rtc = machine.RTC()
    rtc.datetime(new_time)
    print("Current persistent time: {}".format(rtc.datetime()))


def manage_time():
    set_time()
    print("New device time: {}".format(utime.localtime()))
    set_device_time(utime.localtime())


def main():
    ip = do_connect()
    manage_time()
    s    = init_web(ip)
    pins = [machine.Pin(i, machine.Pin.IN) for i in (0, 2, 4, 5, 12, 13, 14, 15)]
    while True:
        print(utime.localtime(utime.time()))
        web_server(s, pins)
        utime.sleep_ms(100)


if __name__ == '__main__':
    main()

# EndOfLol
