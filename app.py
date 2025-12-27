import pandas as pd
import folium
from folium.plugins import HeatMap
import webbrowser
import os
import json
import datetime

# ==========================================
# 1. CONFIGURATION & DONNÉES MÉTIER
# ==========================================
TAUX_HORAIRE = 65 
DATE_JOUR = datetime.datetime.now().strftime("%d/%m/%Y")
HEURE_JOUR = datetime.datetime.now().strftime("%H:%M")
ID_MISSION = f"MSN-{datetime.datetime.now().strftime('%Y%m%d')}-042"

# Base de données Matériaux (Recettes)
MATERIAL_DB = {
    "Pothole": {
        "CRITIQUE": {"Asphalte à chaud (kg)": 150, "Émulsion (L)": 10, "Gravier (kg)": 50},
        "MOYENNE":  {"Asphalte à froid (kg)": 40,  "Émulsion (L)": 2},
        "FAIBLE":   {"Scellant bitumineux (L)": 5}
    },
    "Garbage": {
        "CRITIQUE": {"Sacs 100L (u)": 10, "Pelle": 1, "Désinfectant (L)": 2},
        "MOYENNE":  {"Sacs 50L (u)": 5, "Pince": 1},
        "FAIBLE":   {"Sacs 30L (u)": 2}
    },
    "Defaut": {
        "CRITIQUE": {"Ciment prompt (kg)": 20, "Barrières Sécu": 2},
        "MOYENNE":  {"Kit Nettoyage": 1},
        "FAIBLE":   {"Spray Marquage": 1}
    }
}

COST_MODEL = {
    "CRITIQUE": {"h": 4, "p": 3, "mat_budget": 1200}, 
    "MOYENNE":  {"h": 2, "p": 2, "mat_budget": 400}, 
    "FAIBLE":   {"h": 0.5, "p": 1, "mat_budget": 50}   
}

# ==========================================
# 2. TRAITEMENT DES DONNÉES
# ==========================================
try:
    df = pd.read_csv("rapport_anomalies.csv")
except FileNotFoundError:
    print("❌ Erreur : Lancez 'detect.py' d'abord.")
    exit()

# Arrondis
df['confiance_display'] = df['confiance'].round(2)
df['lat_display'] = df['latitude'].round(4)
df['lon_display'] = df['longitude'].round(4)

def categoriser_urgence(confiance):
    if confiance >= 0.75: return "CRITIQUE"
    elif confiance >= 0.50: return "MOYENNE"
    return "FAIBLE"

df['urgence'] = df['confiance'].apply(categoriser_urgence)

# Calcul des matériaux
total_materials_needed = {}

def update_material_list(type_anomalie, urgence):
    recette = MATERIAL_DB.get(type_anomalie, MATERIAL_DB["Defaut"]).get(urgence, {})
    for mat, qte in recette.items():
        if mat in total_materials_needed:
            total_materials_needed[mat] += qte
        else:
            total_materials_needed[mat] = qte
    return recette

df['materiaux_requis'] = df.apply(lambda row: update_material_list(row['type'], row['urgence']), axis=1)

# Calculs RH et Financiers
total_budget = 0
total_heures = 0
total_staff = 0
stats = df['urgence'].value_counts()
details_mission = []

for cat in ["CRITIQUE", "MOYENNE", "FAIBLE"]:
    count = stats.get(cat, 0)
    model = COST_MODEL[cat]
    subtotal = count * ((model["h"] * model["p"] * TAUX_HORAIRE) + model["mat_budget"])
    heures_cat = count * (model["h"] * model["p"])
    
    total_budget += subtotal
    total_heures += heures_cat
    
    if count > 0:
        details_mission.append({
            "urgence": cat,
            "count": int(count), # Convertir numpy.int64 en int pour JSON
            "heures": float(heures_cat),
            "staff_unit": model["p"]
        })

# Préparation des données pour le JavaScript (JSON)
bon_data = {
    "id": ID_MISSION,
    "date": DATE_JOUR,
    "heure": HEURE_JOUR,
    "materials": total_materials_needed,
    "stats": details_mission,
    "total_budget": f"{total_budget:,.2f}",
    "total_heures": total_heures,
    "zones": len(df)
}
json_bon_data = json.dumps(bon_data)

# ==========================================
# 3. GÉNÉRATION DU DASHBOARD + SCRIPT D'IMPRESSION
# ==========================================
center_lat = df['latitude'].mean() if len(df) > 0 else 34.0208
center_lon = df['longitude'].mean() if len(df) > 0 else -6.8416
m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles='CartoDB dark_matter')

# --- JAVASCRIPT POUR L'IMPRESSION (Le Cœur du "Massive Details") ---
script_print = f"""
<script>
var bonData = {json_bon_data};

function printBon() {{
    var printWindow = window.open('', '', 'height=800,width=900');
    var d = new Date();
    
    var matRows = "";
    for (var key in bonData.materials) {{
        matRows += '<tr><td style="border:1px solid #ddd; padding:8px;">' + key + '</td><td style="border:1px solid #ddd; padding:8px; font-weight:bold; text-align:right;">' + bonData.materials[key] + '</td><td style="border:1px solid #ddd; padding:8px; text-align:center;"><input type="checkbox"></td></tr>';
    }}

    var docContent = `
    <html><head><title>Bon de Sortie - ${{bonData.id}}</title>
    <style>
        body {{ font-family: 'Courier New', Courier, monospace; padding: 40px; color: #333; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .logo {{ font-size: 30px; font-weight: bold; letter-spacing: 5px; }}
        .meta {{ display: flex; justify-content: space-between; margin-bottom: 20px; font-size: 14px; }}
        .section-title {{ background: #eee; padding: 5px; font-weight: bold; margin-top: 20px; border-left: 5px solid #333; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
        th {{ background: #333; color: white; padding: 8px; text-align: left; }}
        .box {{ border: 1px solid #333; padding: 15px; margin-top: 20px; }}
        .signatures {{ display: flex; justify-content: space-between; margin-top: 50px; height: 100px; }}
        .sign-box {{ width: 40%; border-top: 1px solid #333; padding-top: 10px; text-align: center; }}
        .qr {{ text-align: center; margin-top: 30px; opacity: 0.5; }}
    </style>
    </head><body>
        
        <div class="header">
            <div class="logo">CLEANCITY AI</div>
            <div>DÉPARTEMENT LOGISTIQUE & VOIRIE</div>
            <br>
            <div style="font-size: 20px; font-weight: bold; border: 2px solid #333; display: inline-block; padding: 10px;">
                BON DE SORTIE #INTERNE
            </div>
        </div>

        <div class="meta">
            <div>
                <b>RÉF MISSION:</b> ${{bonData.id}}<br>
                <b>DATE:</b> ${{bonData.date}}<br>
                <b>HEURE:</b> ${{bonData.heure}}
            </div>
            <div style="text-align:right;">
                <b>VÉHICULE CIBLE:</b> CAMION-BENNE-04<br>
                <b>ZONE:</b> SECTEUR NORD<br>
                <b>PRIORITÉ:</b> HAUTE
            </div>
        </div>

        <div class="section-title">1. ORDRE DE MISSION</div>
        <table>
            <thead><tr><th>URGENCE</th><th>INTERVENTIONS</th><th>HEURES ESTIMÉES</th><th>PERSONNEL REQUIS</th></tr></thead>
            <tbody>
                ${{bonData.stats.map(s => `<tr><td style="border:1px solid #ddd; padding:8px;">${{s.urgence}}</td><td style="border:1px solid #ddd; padding:8px;">${{s.count}}</td><td style="border:1px solid #ddd; padding:8px;">${{s.heures}} h</td><td style="border:1px solid #ddd; padding:8px;">${{s.staff_unit}} / site</td></tr>`).join('')}}
            </tbody>
        </table>

        <div class="section-title">2. LISTE DE COLISAGE (STOCK)</div>
        <p><i>Veuillez préparer les éléments suivants sur le quai de chargement B.</i></p>
        <table>
            <thead><tr><th>DESIGNATION MATÉRIEL</th><th>QUANTITÉ REQUISE</th><th>CHECK (MAGASIN)</th></tr></thead>
            <tbody>
                ${{matRows}}
            </tbody>
        </table>

        <div class="box">
            <b>NOTE AU CHAUFFEUR:</b><br>
            Attention, présence de nids-de-poule critiques signalés sur l'Avenue Mohammed V. 
            Chargement prioritaire des sacs d'asphalte à froid.
        </div>

        <div class="signatures">
            <div class="sign-box">
                <b>VISA CHEF D'ÉQUIPE</b><br><br><small>(Signature)</small>
            </div>
            <div class="sign-box">
                <b>VISA MAGASINIER</b><br><br><small>(Signature & Tampon)</small>
            </div>
        </div>

        <div class="qr">
            ||| || ||| || |||| ||| || |||||| ||| || ||<br>
            ${{bonData.id}}-SECURE-HASH-256
        </div>

    </body></html>
    `;

    printWindow.document.write(docContent);
    printWindow.document.close();
    printWindow.print();
}}
</script>
"""
m.get_root().html.add_child(folium.Element(script_print))

# --- WIDGET FLOTTANT (Avec Bouton JS) ---
materials_html_short = ""
count = 0
for mat, qte in total_materials_needed.items():
    if count < 4: # On affiche juste les 4 premiers dans le widget pour pas surcharger
        materials_html_short += f"<tr><td style='border-bottom:1px solid #eee;'>{mat}</td><td style='text-align:right; border-bottom:1px solid #eee;'><b>{qte}</b></td></tr>"
    count += 1
if len(total_materials_needed) > 4:
    materials_html_short += "<tr><td colspan='2' style='text-align:center; color:grey;'>... (Voir Bon complet) ...</td></tr>"

html_panel = f"""
<div style="position: fixed; top: 10px; right: 10px; z-index:9000; font-family: 'Segoe UI', sans-serif;
            background-color: white; padding: 15px; border-radius: 8px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.3); width: 300px; border-top: 5px solid #27ae60;">
    
    <h3 style="margin:0 0 10px 0; color:#2c3e50;">🚛 Logistique & Stock</h3>
    
    <div style="background-color:#f9f9f9; padding:10px; border-radius:4px; font-size:12px; margin-bottom:10px;">
        <b>Charge Travail:</b> {total_heures} Heures<br>
        <b>Budget Matériel:</b> {total_budget:,.0f} MAD
    </div>

    <table style="width:100%; font-size:11px; border-collapse: collapse; margin-bottom:15px;">
        {materials_html_short}
    </table>
    
    <div style="text-align:center;">
        <button onclick="printBon()" style="background-color:#27ae60; color:white; border:none; padding:10px 20px; border-radius:4px; cursor:pointer; font-weight:bold; font-size:14px; width:100%; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
            🖨️ IMPRIMER BON DE SORTIE
        </button>
    </div>
</div>
"""
m.get_root().html.add_child(folium.Element(html_panel))

# Couches Carte
heat_data = [[row['latitude'], row['longitude']] for index, row in df.iterrows()]
HeatMap(heat_data, radius=15, blur=10).add_to(m)

for index, row in df.iterrows():
    color = 'green'
    if row['urgence'] == 'CRITIQUE': color = 'red'
    elif row['urgence'] == 'MOYENNE': color = 'orange'
    
    mat_list_str = "<br>".join([f"- {k}: {v}" for k,v in row['materiaux_requis'].items()])
    popup_html = f"""
    <div style="font-family: sans-serif; width: 220px;">
        <b style="color:{color};">{row['type'].upper()} ({row['urgence']})</b>
        <hr style="margin:5px 0;">
        <div style="font-size:11px;">
            <b>Matériel requis :</b><br>
            <i style="color:#555;">{mat_list_str}</i>
        </div>
    </div>
    """
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=6, color=color, fill=True, fill_color=color, fill_opacity=0.8,
        popup=folium.Popup(popup_html, max_width=250)
    ).add_to(m)

output_file = "dashboard_logistique_final.html"
m.save(output_file)
print(f"✅ Dashboard ULTIME généré : {output_file}")
webbrowser.open('file://' + os.path.realpath(output_file))