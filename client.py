import asyncio
import websockets
import json

async def main():
    uri = "ws://localhost:8765"

    async with websockets.connect(uri, ping_interval=None) as websocket:
        print("Connected to server!")

        while True:
            food_label = input("Enter detected food label: ")

            if food_label.lower() == "quit":
                print("Closing client...")
                break

            await websocket.send(food_label)
            print(f"Sent: {food_label}")

            reply = await websocket.recv()
            reply = await websocket.recv()
            data = json.loads(reply)

            if "error" in data:
                print(f"{data['food']} → {data['error']}")
            else:
                print(f"\nFood: {data['food']}")
                print(f"Calories: {data['calories']} kcal")
                print(f"Protein: {data['protein']} g")
                print(f"Carbs: {data['carbs']} g\n")
                print("Reply from server:", reply)

asyncio.run(main())