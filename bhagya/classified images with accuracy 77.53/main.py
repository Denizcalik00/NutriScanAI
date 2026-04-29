import sensor
import image
import time
import json
import network
import uwebsockets.client as ws

# ─── Config ───────────────────────────────────────────────────────────────────
WIFI_SSID    = "Bhagya S's iPhoneD"
WIFI_PASS    = "terathilla"
SERVER_IP    = "172.20.10.2"
SERVER_PORT  = 8765
CONFIDENCE_THRESHOLD = 0.70
CAPTURE_INTERVAL_MS  = 2500

# ─── Camera init ──────────────────────────────────────────────────────────────
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_hmirror(False)
sensor.skip_frames(time=2000)

# ─── Load model ───────────────────────────────────────────────────────────────
import tf

model = tf.load("/model.tflite", load_to_fb=True)

# Read labels from SD card — order matches Edge Impulse training
with open("/labels.txt") as f:
    labels = [line.strip() for line in f.readlines()]

print("Labels:", labels)

# ─── WiFi connect ─────────────────────────────────────────────────────────────
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASS)

print("Connecting to WiFi", end="")
for _ in range(20):
    if wlan.isconnected():
        break
    time.sleep_ms(500)
    print(".", end="")
print()

if not wlan.isconnected():
    raise RuntimeError("WiFi connection failed — check SSID/password")

print("WiFi connected. IP:", wlan.ifconfig()[0])

# ─── Display helper ───────────────────────────────────────────────────────────
try:
    import display
    lcd = display.SPIDisplay(width=320, height=240)
    HAS_LCD = True
except ImportError:
    HAS_LCD = False
    print("[WARN] No display — output to serial only")


def draw_results(frame, label, confidence, payload):
    nut = payload.get("nutrition_per_100g", {})
    print(f"\n=== {label.upper()} ({confidence*100:.1f}%) ===")
    print(f"  Calories : {nut.get('calories', '?')} kcal / 100g")
    print(f"  Protein  : {nut.get('protein_g', '?')} g")
    print(f"  Carbs    : {nut.get('carbs_g', '?')} g")
    print(f"  Fat      : {nut.get('fat_g', '?')} g")
    print(f"  Fibre    : {nut.get('fiber_g', '?')} g")
    if payload.get("show_ingredients") and payload.get("ingredients"):
        print(f"  Ingredients: {', '.join(payload['ingredients'][:5])}")
    if payload.get("allergens"):
        print(f"  Allergens  : {', '.join(payload['allergens'])}")

    if not HAS_LCD:
        return

    frame.draw_rectangle(0, 0, 320, 240, color=0, fill=True)
    frame.draw_rectangle(0, 0, 320, 28, color=(30, 80, 200), fill=True)
    frame.draw_string(6, 7, f"{label.upper()}  {confidence*100:.0f}%",
                      color=(255, 255, 255), scale=2)

    y = 36
    line_h = 22

    def row(key, val):
        nonlocal y
        frame.draw_string(6,   y, key, color=(160, 200, 255), scale=1)
        frame.draw_string(130, y, str(val), color=(220, 220, 220), scale=1)
        y += line_h

    row("Calories", f"{nut.get('calories','?')} kcal")
    row("Protein",  f"{nut.get('protein_g','?')} g")
    row("Carbs",    f"{nut.get('carbs_g','?')} g")
    row("Fat",      f"{nut.get('fat_g','?')} g")
    row("Fibre",    f"{nut.get('fiber_g','?')} g")

    if payload.get("show_ingredients") and payload.get("ingredients"):
        y += 4
        frame.draw_string(6, y, "Ingredients:", color=(255, 200, 80), scale=1)
        y += line_h
        frame.draw_string(6, y, ", ".join(payload["ingredients"][:4]),
                          color=(220, 220, 220), scale=1)
        y += line_h

    if payload.get("allergens"):
        y += 4
        frame.draw_string(6, y, "Allergens:", color=(255, 100, 80), scale=1)
        y += line_h
        frame.draw_string(6, y, ", ".join(payload["allergens"][:3]),
                          color=(255, 160, 100), scale=1)

    lcd.write(frame)


# ─── WebSocket helper ─────────────────────────────────────────────────────────
def make_ws_connection():
    uri = f"ws://{SERVER_IP}:{SERVER_PORT}"
    print(f"Connecting to WebSocket {uri}")
    conn = ws.connect(uri)
    print("WebSocket connected")
    return conn


socket_conn = None
last_label  = None
last_sent   = 0

# ─── Main loop ────────────────────────────────────────────────────────────────
while True:
    frame = sensor.snapshot()

    # FIX 1: classify without sliding-window params (those are for detection not classification)
    objs = model.classify(frame)

    if not objs:
        time.sleep_ms(CAPTURE_INTERVAL_MS)
        continue

    scores    = objs[0].output()
    best_idx  = scores.index(max(scores))
    best_conf = max(scores)
    best_label = labels[best_idx] if best_idx < len(labels) else "unknown"

    print(f"Detected: {best_label}  ({best_conf:.2f})")

    if best_conf < CONFIDENCE_THRESHOLD:
        time.sleep_ms(CAPTURE_INTERVAL_MS)
        continue

    now = time.ticks_ms()
    if best_label == last_label and time.ticks_diff(now, last_sent) < 5000:
        time.sleep_ms(CAPTURE_INTERVAL_MS)
        continue

    try:
        if socket_conn is None:
            socket_conn = make_ws_connection()

        # FIX 2: send label as lowercase so server nutrition lookup works
        # (labels.txt has "Pizza" but server dict uses "pizza")
        msg = json.dumps({"label": best_label.lower(), "confidence": best_conf})
        socket_conn.send(msg)
        raw = socket_conn.recv()
        payload = json.loads(raw)

        draw_results(frame, best_label, best_conf, payload)
        last_label = best_label
        last_sent  = now

    except Exception as e:
        print("WebSocket error:", e)
        socket_conn = None

    time.sleep_ms(CAPTURE_INTERVAL_MS)