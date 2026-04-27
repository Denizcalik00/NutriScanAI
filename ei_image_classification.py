import sensor, time, ml, gc, uos
import socket
import json

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((240, 240))
sensor.skip_frames(time=2000)

# Server config (your laptop IP)
SERVER_IP = "192.168.1.5"
SERVER_PORT = 8000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, SERVER_PORT))

nutrition = {
    "Fries": ["312 kcal", "3.4g protein", "41g carbs"],
    "Burger": ["295 kcal", "17g protein", "30g carbs"],
    "Pizza": ["266 kcal", "11g protein", "33g carbs"],
    "Banana": ["89 kcal", "1.1g protein", "23g carbs"],
    "Broccoli": ["55 kcal", "3.7g protein", "11g carbs"]
}

net = ml.Model("trained.tflite", load_to_fb=uos.stat('trained.tflite')[6] > (gc.mem_free() - (64*1024)))
labels = [line.strip() for line in open("labels.txt")]

clock = time.clock()
THRESHOLD = 0.80

while True:
    clock.tick()
    img = sensor.snapshot()

    scores = net.predict([img])[0].flatten().tolist()
    predictions = list(zip(labels, scores))

    best_label, best_score = max(predictions, key=lambda x: x[1])

    if best_score > THRESHOLD:
        payload = {
            "label": best_label,
            "score": float(best_score),
            "nutrition": nutrition.get(best_label, [])
        }
    else:
        payload = {
            "label": "Unknown",
            "score": float(best_score)
        }

    client.send((json.dumps(payload) + "\n").encode())

    img.draw_string(10, 10, best_label, color=(255, 0, 0), scale=2)
