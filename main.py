# Edge Impulse - OpenMV Image Classification Example
#
# This work is licensed under the MIT license.
# Copyright (c) 2013-2024 OpenMV LLC. All rights reserved.
# https://github.com/openmv/openmv/blob/master/LICENSE

import sensor, time, ml, uos, gc
import ujson  # >>> ADDED: needed to send clean JSON to WebSocket bridge
import network, socket   # >>> 

sensor.reset()                         # Reset and initialize the sensor.
sensor.set_pixformat(sensor.RGB565)    # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.QQVGA)      # Set frame size to QQVGA (320x240)
sensor.set_windowing((240, 240))       # Set 240x240 window.
sensor.skip_frames(time=2000)          # Let the camera adjust.

net = None
labels = None

CONFIDENCE_THRESHOLD = 0.75  # >>> ADDED: only count prediction if 75% or higher
# >>> ADDED: WiFi setup (CHANGE THESE)
SSID = "Denizhot"
KEY  = "deniz333"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, KEY)
while not wlan.isconnected():
    time.sleep(1)

ip = wlan.ifconfig()[0]
print("IP:", ip)

# Server socket — non-blocking so it doesn't stall the main loop
addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse on restart
s.bind(addr)
s.listen(1)
s.setblocking(False)
print("Stream: http://%s:8080/stream" % ip)

try:
    net = ml.Model("trained.tflite", load_to_fb=uos.stat('trained.tflite')[6] > (gc.mem_free() - (64*1024)))
except Exception as e:
    raise Exception('Failed to load model: ' + str(e))

try:
    labels = [line.rstrip('\n') for line in open("labels.txt")]
except Exception as e:
    raise Exception('Failed to load labels: ' + str(e))

clock = time.clock()
last_prediction_time = 0
client = None

while True:
    img = sensor.snapshot()

    # ----------- HANDLE NEW CLIENT CONNECTION -----------
    if client is None:
        try:
            client, cli_addr = s.accept()

            # FIX 1: Set client to BLOCKING so recv/send work reliably
            client.setblocking(True)
            client.settimeout(2.0)  # 2s timeout to read the HTTP request

            try:
                req = client.recv(1024)
            except OSError:
                req = b""

            if b"/stream" in req:
                # FIX 2: Use sendall() for guaranteed delivery
                # FIX 3: Removed "Connection: close" — breaks streaming
                client.sendall(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
                    b"Cache-Control: no-cache\r\n"
                    b"\r\n"
                )
                client.settimeout(5.0)  # Looser timeout for ongoing stream
            else:
                # Unknown request — send 404 and drop
                client.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
                client.close()
                client = None

        except OSError:
            # No client waiting — perfectly normal in non-blocking mode
            pass

    # ----------- STREAM FRAME TO CONNECTED CLIENT -----------
    if client:
        try:
            jpg = img.compress(quality=25)

            # Robust: try bytearray() first, fall back to bytes()
            try:
                img_bytes = jpg.bytearray()
            except AttributeError:
                img_bytes = bytes(jpg)

            frame_header = (
                "--frame\r\n"
                "Content-Type: image/jpeg\r\n"
                "Content-Length: %d\r\n"
                "\r\n"
            ) % len(img_bytes)

            client.sendall(frame_header.encode())
            client.sendall(img_bytes)
            client.sendall(b"\r\n")

        except OSError:
            # Client disconnected — clean up so we can accept a new one
            try:
                client.close()
            except:
                pass
            client = None

    # ----------- PREDICTION (EVERY 2s) -----------
    now = time.ticks_ms()
    if time.ticks_diff(now, last_prediction_time) > 2000:
        last_prediction_time = now

        predictions = net.predict([img])[0].flatten().tolist()
        scores = {}
        best_label = None
        best_score = 0

        for i in range(len(labels)):
            label = labels[i]
            score = predictions[i]
            scores[label] = score
            if score > best_score:
                best_score = score
                best_label = label

        predicted = best_label if best_score >= CONFIDENCE_THRESHOLD else "No confident prediction"

        message = {
            "scores": scores,
            "predicted": predicted,
            "confidence": best_score
        }
        print(ujson.dumps(message))
