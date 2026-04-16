# NutriScanAI
## Team:
### Bhagya
### Deniz
### Hamza
### Ritika
### Venu

# 🍎 Food Detection & Nutrition Display (OpenMV TinyML Project)

## 📌 Overview

This project aims to build a real-time food detection system using the OpenMV Cam RT1062 and TinyML. The system detects different types of food using an on-device AI model and displays related nutritional information.

## 🧠 How It Works

* The OpenMV camera captures live images.
* A TinyML model (trained with Edge Impulse) runs on the device to classify 6–7 food categories (e.g., bread, fruit, fast food).
* The detected food label is sent to an external system (via serial or WebSocket).
* A display interface receives this label and shows estimated nutrition values (calories, protein, carbohydrates) using a predefined lookup table.

## ⚙️ Technologies

* OpenMV Cam RT1062
* Edge Impulse (TinyML)
* Python (for communication & display)
* WebSocket / Serial communication

## 🎯 Goal

To demonstrate an embedded AI system that performs real-time image classification and connects it with meaningful user feedback through a live display.

## ⚠️ Note

Nutritional values shown are approximate and based on general category data, not exact measurements of the detected food.

