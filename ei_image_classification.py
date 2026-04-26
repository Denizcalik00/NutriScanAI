# Edge Impulse - OpenMV Image Classification Example
#
# This work is licensed under the MIT license.
# Copyright (c) 2013-2024 OpenMV LLC. All rights reserved.
# https://github.com/openmv/openmv/blob/master/LICENSE

import sensor, time, ml, uos, gc

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((240, 240))
sensor.skip_frames(time=2000)

net = ml.Model("trained.tflite",
               load_to_fb=uos.stat('trained.tflite')[6] > (gc.mem_free() - (64*1024)))

labels = [line.rstrip('\n') for line in open("labels.txt")]

clock = time.clock()

CONFIDENCE_THRESHOLD = 0.70

while True:
    clock.tick()

    img = sensor.snapshot()

    outputs = net.predict([img])[0].flatten().tolist()
    predictions = list(zip(labels, outputs))

    best_label = max(predictions, key=lambda x: x[1])

    if best_label[1] > CONFIDENCE_THRESHOLD:
        text = "%s %.2f" % (best_label[0], best_label[1])
    else:
        text = "No confident result"

    print(text)

    img.draw_string(10, 10, text, color=(255, 0, 0), scale=2)

    print("FPS:", clock.fps())
