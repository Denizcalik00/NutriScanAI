import asyncio
import websockets
import json

connected_clients = set()

nutrition_data = {
    "apple": {"calories": 52, "protein": 0.3, "carbs": 14},
    "banana": {"calories": 89, "protein": 1.1, "carbs": 23},
    "broccoli": {"calories": 34, "protein": 2.8, "carbs": 7},
    "burger": {"calories": 295, "protein": 17, "carbs": 30},
    "donut": {"calories": 452, "protein": 4.9, "carbs": 51},
    "egg": {"calories": 155, "protein": 13, "carbs": 1.1},
    "fries": {"calories": 312, "protein": 3.4, "carbs": 41},
    "pizza": {"calories": 266, "protein": 11, "carbs": 33}
}

async def broadcast(message):
    if connected_clients:
        await asyncio.gather(
            *(client.send(message) for client in connected_clients),
            return_exceptions=True
        )

def build_response_from_prediction(message):
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return {
            "error": "Invalid JSON from OpenMV",
            "raw": message
        }

    predicted = data.get("predicted", "No confident prediction")
    confidence = data.get("confidence", 0)
    scores = data.get("scores", {})

    response = {
        "predicted": predicted,
        "confidence": confidence,
        "scores": scores
    }

    food_key = predicted.lower()

    if food_key in nutrition_data:
        nutrition = nutrition_data[food_key]

        response["nutrition"] = {
            "calories": nutrition["calories"],
            "protein": nutrition["protein"],
            "carbs": nutrition["carbs"]
        }
    else:
        response["nutrition"] = None

    return response

async def handler(websocket):
    connected_clients.add(websocket)
    print("Client connected!", flush=True)

    try:
        async for message in websocket:
            print("Received:", message, flush=True)

            response = build_response_from_prediction(message)
            json_response = json.dumps(response)

            await broadcast(json_response)

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected", flush=True)

    finally:
        connected_clients.remove(websocket)

async def main():
    print("Starting server...", flush=True)

    async with websockets.serve(
        handler,
        "localhost",
        8765,
        ping_interval=None
    ):
        print("Server running on ws://localhost:8765", flush=True)
        await asyncio.Future()

asyncio.run(main())