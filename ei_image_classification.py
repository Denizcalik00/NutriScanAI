# Edge Impulse - OpenMV Image Classification Example
#
# This work is licensed under the MIT license.
# Copyright (c) 2013-2024 OpenMV LLC. All rights reserved.
# https://github.com/openmv/openmv/blob/master/LICENSE

import sensor, time, ml, uos, gc


sensor.reset()                         # Reset and initialize the sensor.
sensor.set_pixformat(sensor.RGB565)    # Set pixel format to RGB565 color mode.
sensor.set_framesize(sensor.QVGA)      # Set frame size to QVGA (320x240).
sensor.set_windowing((240, 240))       # Use only a 240x240 window from the camera image.
sensor.skip_frames(time=2000)          # Wait 2 seconds so camera can adjust brightness/exposure.

# <<< : Nutrition information for each food class.
# These labels must match labels.txt names.
nutrition = {
    "Fries": ["312 kcal", "3.4g protein", "41g carbs"],
    "Burger": ["295 kcal", "17g protein", "30g carbs"],
    "Pizza": ["266 kcal", "11g protein", "33g carbs"],
    "Banana": ["89 kcal", "1.1g protein", "23g carbs"],
    "Broccoli": ["55 kcal", "3.7g protein", "11g carbs"]
}

net = None                             # Placeholder for the trained AI model.
labels = None                          # Placeholder for the class labels.

try:
    # Load the trained TensorFlow Lite model from the OpenMV storage.
    # load_to_fb helps manage memory depending on available free memory.
    net = ml.Model("trained.tflite", load_to_fb=uos.stat('trained.tflite')[6] > (gc.mem_free() - (64*1024)))
except Exception as e:
    print(e)
    raise Exception('Failed to load "trained.tflite", did you copy the .tflite and labels.txt file onto the mass-storage device? (' + str(e) + ')')

try:
    # Load class names from labels.txt.
    # Example: Fries, Burger, Pizza, Banana, Broccoli.
    labels = [line.rstrip('\n') for line in open("labels.txt")]
except Exception as e:
    raise Exception('Failed to load "labels.txt", did you copy the .tflite and labels.txt file onto the mass-storage device? (' + str(e) + ')')  # <<< CHANGED: error message now says labels.txt

clock = time.clock()                   # Create clock object to measure FPS.

while(True):                           # Main loop runs forever.
    clock.tick()                       # Start timing this frame.

    img = sensor.snapshot()            # Capture one image from the camera.

    # Run the AI model on the image.
    # net.predict([img]) returns prediction scores.
    # zip(labels, scores) pairs each label with its score.
    predictions_list = list(zip(labels, net.predict([img])[0].flatten().tolist()))

    # <<< : Find the label with the highest prediction score.
    best_label, best_score = max(predictions_list, key=lambda x: x[1])

    # <<< : Print only the best prediction instead of all class scores.
    # Set confidence threshold (tune this value)
    THRESHOLD = 0.80   # Only accept predictions above 80% confidence

    print("---- Predictions ----")
    for label, score in predictions_list:
        print("%s = %.4f" % (label, score))
    # Decide what to display
    if best_score > THRESHOLD:
        print("Detected:", best_label, best_score)          # High confidence  show prediction
    else:
        print("Unknown")       # Low confidence  reject prediction


    # <<< : Draw detected food name on the live camera image.
    img.draw_string(10, 10, best_label, color=(255, 0, 0), scale=4)

    # <<< : Draw nutrition info on the live camera image.
    if best_label in nutrition:
        lines = nutrition[best_label]  # Get nutrition list for detected food.
        y = 50                         # Starting y-position for nutrition text.

        for line in lines:             # Draw each nutrition line separately.
            img.draw_string(10, y, line, color=(0, 255, 0), scale=2)
            y += 25                    # Move next line lower.

    print(clock.fps(), "fps")          # Print current frames per second.
