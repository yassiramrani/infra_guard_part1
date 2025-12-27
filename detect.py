import cv2
from ultralytics import YOLO
import pandas as pd
import time
import requests # Pour envoyer à Firebase
import json

# --- CONFIGURATION ---
model_path = 'best.pt'
video_path = 'salah.mp4'

# VOTRE LIEN FIREBASE (J'ajoute 'anomalies.json' pour créer une collection propre)
FIREBASE_URL = "https://smartcity-b4b77-default-rtdb.firebaseio.com/anomalies.json"

# ---------------------

print("Chargement du modèle YOLO...")
try:
    model = YOLO(model_path)
except:
    print("ERREUR: Le fichier best.pt est introuvable.")
    exit()

cap = cv2.VideoCapture(video_path)
detections_log = []

# Coordonnées de départ (Rabat)
lat, lon = 34.020882, -6.841650

print(f"🚀 Lancement de l'analyse & Synchronisation Cloud...")
print(f"📡 Cible: {FIREBASE_URL}")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Simulation GPS (Le camion avance)
    lat += 0.00005
    lon += 0.00002

    # Inférence
    results = model(frame, conf=0.4, verbose=False)
    annotated_frame = results[0].plot()
    
    # HUD (Affichage tête haute)
    cv2.putText(annotated_frame, f"GPS: {lat:.4f}, {lon:.4f}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    if len(results[0].boxes) > 0:
        for box in results[0].boxes:
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            class_name = model.names[cls_id]
            
            # --- 1. EDGE COMPUTING (Calcul local) ---
            # On détermine l'urgence ICI pour soulager le serveur
            urgence = "FAIBLE"
            if conf >= 0.75: urgence = "CRITIQUE"
            elif conf >= 0.50: urgence = "MOYENNE"

            # --- 2. PRÉPARATION DE LA DONNÉE ---
            timestamp = time.time()
            data_payload = {
                "timestamp": timestamp,
                "date_heure": time.strftime("%Y-%m-%d %H:%M:%S"),
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "type": class_name,
                "confiance": round(conf, 2),
                "urgence": urgence,
                "statut": "NON_TRAITE" # Pour le dashboard de gestion
            }

            # --- 3. ENVOI CLOUD (FIREBASE) ---
            try:
                # On utilise POST pour ajouter une nouvelle entrée
                response = requests.post(FIREBASE_URL, json=data_payload)
                if response.status_code == 200:
                    status_icon = "☁️ OK"
                else:
                    status_icon = "⚠️ Cloud Err"
            except Exception as e:
                status_icon = "❌ No Net"
            
            # Affichage sur la vidéo
            cv2.putText(annotated_frame, f"ALERTE: {class_name}", (50, 100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            cv2.putText(annotated_frame, f"Uploading... {status_icon}", (50, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Sauvegarde locale (Backup CSV)
            detections_log.append(data_payload)
            
            # Petit délai pour ne pas spammer Firebase (optionnel)
            # time.sleep(0.1) 

    cv2.imshow("CleanCity AI - Cloud Connected", annotated_frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Sauvegarde CSV finale
if detections_log:
    df = pd.DataFrame(detections_log)
    df.to_csv("rapport_anomalies.csv", index=False)
    print(f"✅ Terminé ! {len(df)} anomalies envoyées au Cloud et sauvegardées en CSV.")
else:
    print("Terminé. Rien à signaler.")