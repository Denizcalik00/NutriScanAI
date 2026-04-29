🍎 NutriScanAI
Real-Time Food Detection & Nutrition Display using OpenMV + TinyML
📌 Overview

NutriScanAI is an embedded AI system that detects food items in real time using an OpenMV Cam RT1062 and displays estimated nutritional information through a live web interface.

The system combines:
Edge AI (TinyML) for on-device image classification
Serial + WebSocket communication for data transfer
Browser UI for visualization
👥 Team
Bhagya
Deniz
Hamza
Ritika
Venu
🧠 How It Works
OpenMV Camera (TinyML)
        ↓ (Serial)
Python Bridge (serial_to_websocket.py)
        ↓ (WebSocket)
Server (server.py)
        ↓
Web UI (index.html)
Step-by-step:
OpenMV captures images in real time
TinyML model classifies food into one of 8 categories
Prediction is sent via serial as JSON
Python bridge forwards data to WebSocket server
Server adds nutrition data
Browser displays:
Detected food
Confidence
Nutrition values
All prediction scores
Live camera feed
🍽️ Supported Food Classes
Apple
Banana
Broccoli
Burger
Donut
Egg
Fries
Pizza
⚙️ Technologies Used
OpenMV Cam RT1062
Edge Impulse (TinyML)
Python (asyncio, websockets, serial)
HTML / CSS / JavaScript
WebSocket communication
🚀 Setup & Installation
1. Flash OpenMV

Upload the following files to OpenMV:

main.py  
trained.tflite  
labels.txt  

Then disconnect OpenMV IDE.

2. Install Python dependencies
pip install websockets pyserial
3. Run backend

Terminal 1:

python server.py

Terminal 2:

python serial_to_websocket.py
4. Open frontend

Open:

index.html

in your browser.

📷 Camera Streaming
✅ Recommended (Stable)
OpenMV serves snapshot images via HTTP
Browser refreshes image periodically
⚠️ MJPEG Streaming
Attempted but unstable under TinyML load
OpenMV resource limitations affect performance
🎯 Features
Real-time food detection (on-device AI)
Confidence-based prediction filtering
Nutrition lookup (calories, protein, carbs)
Live camera visualization
WebSocket-based real-time UI updates
Lightweight embedded system
⚠️ Limitations
Nutrition values are approximate (category-based)
OpenMV cannot reliably handle:
TinyML + MJPEG streaming simultaneously
Frame rate depends on model complexity
🧪 Example Output
{
  "food": "Banana",
  "calories": 89,
  "protein": 1.1,
  "carbs": 23
}
🧠 Key Learning Outcomes
Edge AI deployment on microcontrollers
Real-time embedded system design
Serial → WebSocket communication pipeline
Handling hardware constraints in AI systems
UI integration with embedded devices
🚀 Future Improvements
Improve model accuracy with more training data
Add portion size estimation
Optimize streaming performance
Deploy on Raspberry Pi for HDMI output
Mobile app integration
📄 License

This project builds upon OpenMV examples licensed under MIT.

💡 Final Note

NutriScanAI demonstrates how embedded AI can be connected to meaningful user interfaces, turning raw predictions into useful real-world insights.
