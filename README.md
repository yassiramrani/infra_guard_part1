# 🏙️ INFRAGUARD AI - Urban Anomaly Detection & Logistics System

INFRAGUARD AI is an intelligent system designed to automate the detection of urban anomalies (such as potholes, garbage, and infrastructure defects) and optimize the logistics for their resolution.

## 🚀 Project Overview

The system operates in two main phases:
1.  **Detection & Data Collection (`detect.py`)**: Uses a computer vision model (YOLOv8) on video feeds to identify broken infrastructure. It simulates GPS tracking, logs events to a local CSV file, and syncs data to Firebase in real-time.
2.  **Logistics & Analytics (`app.py`)**: Processes the collected data to calculate repair costs, material requirements, and workforce needs. It generates an interactive map dashboard for resource planning and mission orders.

## 📂 Project Structure

- **`detect.py`**: The "Edge Computing" script. detecting anomalies, determining urgency, and simulating a patrol vehicle's route.
- **`app.py`**: The "Backend/Analytics" script. Generates the logistics dashboard (`dashboard_logistique_final.html`).
- **`best.pt`**: Custom trained YOLOv8 model weights for urban anomalies.
- **`salah.mp4`**: Sample video footage used for simulation.
- **`rapport_anomalies.csv`**: generated report containing detected anomalies with geolocation and urgency levels.
- **`dashboard_logistique_final.html`**: The final interactive output map.

## 🛠️ Prerequisites

Ensure you have Python 3.8+ installed. You will need the following libraries:

```bash
pip install opencv-python ultralytics pandas folium requests
```

> **Note:** The project uses `best.pt` which requires the `ultralytics` package.

## ⏯️ Execution Tutorial

Follow these steps to run the full simulation:

### Step 1: Run the Detection System
This script processes the video feed, detecting anomalies and uploading data.

```bash
python detect.py
```
*   **What happens?**
    *   A window opens showing the video feed with bounding boxes around detected objects.
    *   "Edge Computing" logic runs to assess urgency (Low/Medium/Critical).
    *   Data is saved to `rapport_anomalies.csv`.
    *   Press `q` to stop the simulation early.

### Step 2: Generate the Logistics Dashboard
Once detection is complete (or you have generated enough data), run the analytics engine.

```bash
python app.py
```
*   **What happens?**
    *   The script reads `rapport_anomalies.csv`.
    *   It calculates the budget (MAD), materials (e.g., Asphalt, Cement), and staff hours required.
    *   It generates `dashboard_logistique_final.html`.
    *   The dashboard should automatically open in your default web browser.

### Step 3: Interact with the Dashboard
*   **Map Interface**: View anomalies as a heatmap or individual markers color-coded by urgency.
*   **Logistics Panel**: A floating widget shows the total budget and material summary.
*   **Print Mission Order**: Click the "🖨️ IMPRIMER BON DE SORTIE" button to generate a formal PDF-ready mission order for the maintenance crew.

## 🧩 Configuration

- **Firebase**: The URL is configured in `detect.py` (`FIREBASE_URL`).
- **Cost Model**: Pricing and material formatting are defined in `app.py` (`MATERIAL_DB`, `COST_MODEL`).
