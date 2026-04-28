import asyncio
import serial
import websockets

SERIAL_PORT = "COM11"
BAUD_RATE = 115200
WEBSOCKET_URI = "ws://localhost:8765"

async def main():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

    async with websockets.connect(WEBSOCKET_URI, ping_interval=None) as websocket:
        print("Connected to WebSocket server")
        print("Reading predictions from OpenMV serial...")

        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if line:
                print("OpenMV sent:", line)

                await websocket.send(line)

                reply = await websocket.recv()
                print("Server reply:", reply)

asyncio.run(main())