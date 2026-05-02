# Edge Impulse - OpenMV Image Classification Example
#
# This work is licensed under the MIT license.
# Copyright (c) 2013-2024 OpenMV LLC. All rights reserved.
# https://github.com/openmv/openmv/blob/master/LICENSE

import sensor, time, ml, uos, gc   # camera + time + model + file + memory
import ujson                       # send JSON data
import network, socket            # WiFi + HTTP server

sensor.reset()                    # initialize camera
sensor.set_pixformat(sensor.GRAYSCALE)   # use grayscale (matches your model)
sensor.set_framesize(sensor.QQVGA)       # small resolution for speed
sensor.set_windowing((240, 240))         # crop image center
sensor.skip_frames(time=2000)            # wait for camera to stabilize

net = None                        # placeholder for model
labels = None                     # placeholder for labels
CONFIDENCE_THRESHOLD = 0.75       # minimum confidence to accept prediction

SSID = "Denizhot"                # WiFi name
KEY  = "deniz333"                # WiFi password

wlan = network.WLAN(network.STA_IF)  # create WiFi object
wlan.active(True)                   # turn WiFi ON
wlan.connect(SSID, KEY)             # connect to network

while not wlan.isconnected():       # wait until connected
    time.sleep(1)

ip = wlan.ifconfig()[0]             # get device IP address
print("IP:", ip)

# ----------- CREATE HTTP SERVER -----------
addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]  # listen on port 8080
s = socket.socket()                               # create socket
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allow restart reuse
s.bind(addr)                                      # bind to address
s.listen(1)                                       # allow 1 client
s.setblocking(False)                              # non-blocking mode

print("Stream: http://%s:8080/stream" % ip)

# ----------- LOAD MODEL -----------
try:
    net = ml.Model("trained.tflite",
        load_to_fb=uos.stat('trained.tflite')[6] > (gc.mem_free() - (64*1024)))  # load model
except Exception as e:
    raise Exception('Failed to load model: ' + str(e))

# ----------- LOAD LABELS -----------
try:
    labels = [line.rstrip('\n') for line in open("labels.txt")]  # read labels file
except Exception as e:
    raise Exception('Failed to load labels: ' + str(e))

clock = time.clock()           # FPS timer
last_prediction_time = 0       # track last prediction time
client = None                 # store connected browser

# ----------- MAIN LOOP -----------
while True:
    img = sensor.snapshot()   # capture image

    # ----------- HANDLE NEW CLIENT -----------
    if client is None:
        try:
            client, cli_addr = s.accept()   # accept browser connection

            client.setblocking(True)        # use blocking mode for communication
            client.settimeout(2.0)          # timeout for request

            try:
                req = client.recv(1024)     # read browser request
            except OSError:
                req = b""                  # empty if failed

            if b"/stream" in req:          # check if stream requested
                client.sendall(            # send HTTP headers for MJPEG
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
                    b"Cache-Control: no-cache\r\n"
                    b"\r\n"
                )
                client.settimeout(5.0)     # longer timeout for streaming
            else:
                client.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")  # reject unknown request
                client.close()
                client = None

        except OSError:
            pass  # no client yet

    # ----------- STREAM IMAGE FRAME -----------
    if client:
        try:
            jpg = img.compress(quality=15)  # compress image to JPEG

            try:
                img_bytes = jpg.bytearray()  # convert to bytes
            except AttributeError:
                img_bytes = bytes(jpg)       # fallback conversion

            frame_header = (
                "--frame\r\n"
                "Content-Type: image/jpeg\r\n"
                "Content-Length: %d\r\n"
                "\r\n"
            ) % len(img_bytes)

            client.sendall(frame_header.encode())  # send frame header
            client.sendall(img_bytes)              # send image
            client.sendall(b"\r\n")                # frame end

        except OSError:
            try:
                client.close()  # close broken connection
            except:
                pass
            client = None      # reset client

    # ----------- RUN PREDICTION EVERY 2s -----------
    now = time.ticks_ms()
    if time.ticks_diff(now, last_prediction_time) > 2000:
        last_prediction_time = now

        predictions = net.predict([img])[0].flatten().tolist()  # run model

        scores = {}            # store all class scores
        best_label = None      # best class
        best_score = 0         # highest confidence

        for i in range(len(labels)):
            label = labels[i]
            score = predictions[i]

            scores[label] = score  # save score

            if score > best_score:  # find best prediction
                best_score = score
                best_label = label

        predicted = best_label if best_score >= CONFIDENCE_THRESHOLD else "No confident prediction"

        message = {
            "scores": scores,
            "predicted": predicted,
            "confidence": best_score
        }

        print(ujson.dumps(message))  # send result to PC
