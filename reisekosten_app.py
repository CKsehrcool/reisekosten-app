# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import os
from io import BytesIO

# Konfiguration
st.set_page_config(page_title="Reisekostenabrechnung AT 2025", layout="wide")

# Regelsätze 2025
AUSLAND_PAUSCHALEN = {
    "Deutschland": {"voll": 58.00, "teil": 34.00},
    "Schweiz": {"voll": 81.00, "teil": 48.00},
    "Liechtenstein": {"voll": 81.00, "teil": 48.00},
    "Italien": {"voll": 58.00, "teil": 34.00},
    "Tschechien": {"voll": 49.00, "teil": 30.00},
    "Slowakei": {"voll": 49.00, "teil": 30.00},
    "Frankreich": {"voll": 58.00, "teil": 34.00},
    "Andere": {"voll": 50.00, "teil": 33.00}
}

INLAND_PAUSCHALE = 30.00
UEBERNACHTUNG_INLAND = 17.00
KILOMETERGELD = 0.50

# Session State initialisieren
if 'reisen' not in st.session_state:
    st.session_state.reisen = []
if 'current_reise' not in st.session_state:
    st.session_state.current_reise = {}

# Hilfsfunktionen
def calculate_verpflegung(reise):
    if reise['reiseart'] == 'Inland':
        pauschale = INLAND_PAUSCHALE
        if reise.get('fruehstück'):
            pauschale -= 4.50
        if reise.get('mittagessen'):
            pauschale -= 7.50
        return pauschale * reise['tage']
    
    else:  # Ausland
        land = reise['land']
        vollsatz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN['Andere'])['voll']
        teilsatz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN['Andere'])['teil']
        
        # Tage berechnen
        tage_voll = reise['tage']
        tage_teil = 1 if reise['stunden'] > 8 else 0
        
        gesamt = (tage_voll * vollsatz) + (tage_teil * teilsatz)
        
        # Mahlzeiten abziehen
        if reise.get('fruehstück'):
            gesamt -= vollsatz * 0.20
        if reise.get('mittagessen'):
            gesamt -= vollsatz * 0.40
            
        return gesamt

def berechne_reisekosten(reise):
    kosten = {
        'verpflegung': calculate_verpflegung(reise),
        'kilometergeld': reise['kilometer'] * KILOMETERGELD,
        'parken': reise.get('parken', 0),
        'oepnv': reise.get('oepnv', 0),
        'hotel': reise.get('hotel', 0),
        'maut': reise.get('maut', 0),
        'sonstiges': reise.get('sonstiges', 0)
    }
    
    if reise['reiseart'] == 'Inland':
        kosten['uebernachtung'] = reise.get('uebernachtungen', 0) * UEBERNACHTUNG_INLAND
    
    kosten['gesamt'] = sum(kosten.values())
    return kosten

def save_reise():
    if st.session_state.current_reise:
        # Tage berechnen
        start = st.session_state.current_reise['startdatum']
        ende = st.session_state.current_reise['enddatum']
        tage = (ende - start).days + 1
        
        # Stunden berechnen (für Ausland)
        stunden = (ende - start).total_seconds() / 3600
        
        st.session_state.current_reise.update({
            'tage': tage,
            'stunden': stunden,
            'kosten': berechne_reisekosten(st.session_state.current_reise)
        })
        
        st.session_state.reisen.append(st.session_state.current_reise.copy())
        st.session_state.current_reise = {}
        st.success("Reise erfolgreich gespeichert!")

# UI
st.title("🇦🇹 Reisekostenabrechnung Österreich 2025")
st.caption("Gemäß WKO-Verordnung 2025 und Bundesministerium für Finanzen")

# Eingabeformular
with st.expander("Neue Reise erfassen", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.current_reise['mitarbeiter'] = st.text_input("Mitarbeitername*")
        st.session_state.current_reise['projekt'] = st.text_input("Projekt*")
        
        reiseart = st.radio("Reiseart*", ['Inland', 'Ausland'], horizontal=True)
        st.session_state.current_reise['reiseart'] = reiseart
        
        if reiseart == 'Ausland':
            st.session_state.current_reise['land'] = st.selectbox(
                "Zielland*", 
                list(AUSLAND_PAUSCHALEN.keys())
            )
            st.info(f"Verpflegungspauschale: {AUSLAND_PAUSCHALEN[st.session_state.current_reise['land']]['voll']}€ (>24h) / {AUSLAND_PAUSCHALEN[st.session_state.current_reise['land']]['teil']}€ (8-24h)")
        else:
            st.info(f"Verpflegungspauschale Inland: {INLAND_PAUSCHALE}€ pro Tag")
        
        start_datum = st.date_input("Startdatum*", datetime.today())
        end_datum = st.date_input("Enddatum*", datetime.today())
        st.session_state.current_reise['startdatum'] = start_datum
        st.session_state.current_reise['enddatum'] = end_datum
        
    with col2:
        st.session_state.current_reise['von'] = st.text_input("Startort*")
        st.session_state.current_reise['nach'] = st.text_input("Zielort*")
        st.session_state.current_reise['zwischenstopps'] = st.text_input("Zwischenstopps (durch Komma getrennt)")
        
        st.subheader("Mahlzeiten inkludiert")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.session_state.current_reise['fruehstück'] = st.checkbox("Frühstück")
        with col_m2:
            st.session_state.current_reise['mittagessen'] = st.checkbox("Mittagessen")
        
        st.subheader("Kosten")
        st.session_state.current_reise['kilometer'] = st.number_input("Kilometer (PKW)", min_value=0.0, step=0.5)
        
        if reiseart == 'Inland':
            st.session_state.current_reise['uebernachtungen'] = st.number_input("Übernachtungen", min_value=0, step=1)
        
        col_k1, col_k2 = st.columns(2)
        with col_k1:
            st.session_state.current_reise['parken'] = st.number_input("Parken (€)", min_value=0.0, step=0.5)
            st.session_state.current_reise['oepnv'] = st.number_input("Öffentlicher Verkehr (€)", min_value=0.0, step=0.5)
        with col_k2:
            st.session_state.current_reise['maut'] = st.number_input("Mautgebühren (€)", min_value=0.0, step=0.5)
            st.session_state.current_reise['sonstiges'] = st.number_input("Sonstige Kosten (€)", min_value=0.0, step=0.5)
    
    st.button("Reise speichern", on_click=save_reise, type="primary")

# Belegmanagement
st.subheader("Belege hochladen")
uploaded_files = st.file_uploader("Belege für diese Reise (PDF, JPG, PNG)", 
                                 type=["pdf", "jpg", "png", "jpeg"],
                                 accept_multiple_files=True)

if uploaded_files:
    st.session_state.current_reise['belege'] = [file.name for file in uploaded_files]

# Reiseübersicht
st.divider()
st.subheader("Gespeicherte Reisen")

if not st.session_state.reisen:
    st.info("Noch keine Reisen erfasst")
else:
    # Monatsfilter
    current_year = datetime.now().year
    monat = st.selectbox("Monat auswählen", 
                         list(calendar.month_name[1:]), 
                         index=datetime.now().month-1)
    
    # Daten für Tabelle vorbereiten
    reisen_data = []
    for reise in st.session_state.reisen:
        if reise['startdatum'].strftime("%B") == monat:
            row = {
                'Mitarbeiter': reise['mitarbeiter'],
                'Projekt': reise['projekt'],
                'Reiseart': reise['reiseart'],
                'Von': reise['von'],
                'Nach': reise['nach'],
                'Datum': f"{reise['startdatum'].strftime('%d.%m.%Y')} - {reise['enddatum'].strftime('%d.%m.%Y')}",
                'Tage': reise['tage'],
                'Verpflegung': f"{reise['kosten']['verpflegung']:.2f}€",
                'Fahrtkosten': f"{reise['kosten']['kilometergeld']:.2f}€",
                'Gesamt': f"{reise['kosten']['gesamt']:.2f}€"
            }
            reisen_data.append(row)
    
    if reisen_data:
        df = pd.DataFrame(reisen_data)
        st.dataframe(df, use_container_width=True)
        
        # Excel Export
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reiseübersicht')
            
            # Detaillierte Kosten
            details = []
            for reise in st.session_state.reisen:
                if reise['startdatum'].strftime("%B") == monat:
                    detail = {
                        'Mitarbeiter': reise['mitarbeiter'],
                        'Projekt': reise['projekt'],
                        'Verpflegung': reise['kosten']['verpflegung'],
                        'Kilometergeld': reise['kosten']['kilometergeld'],
                        'Parken': reise.get('parken', 0),
                        'ÖPNV': reise.get('oepnv', 0),
                        'Hotel': reise.get('hotel', 0),
                        'Maut': reise.get('maut', 0),
                        'Sonstiges': reise.get('sonstiges', 0),
                        'Gesamt': reise['kosten']['gesamt']
                    }
                    details.append(detail)
            
            details_df = pd.DataFrame(details)
            details_df.to_excel(writer, index=False, sheet_name='Kostendetails')
            
            # Belegübersicht
            belege = []
            for reise in st.session_state.reisen:
                if reise['startdatum'].strftime("%B") == monat and 'belege' in reise:
                    for beleg in reise['belege']:
                        belege.append({
                            'Mitarbeiter': reise['mitarbeiter'],
                            'Projekt': reise['projekt'],
                            'Belegname': beleg,
                            'Betrag': 'siehe Kostendetails'
                        })
            
            if belege:
                belege_df = pd.DataFrame(belege)
                belege_df.to_excel(writer, index=False, sheet_name='Belegübersicht')
        
        excel_buffer.seek(0)
        st.download_button(
            label="Excel Export herunterladen",
            data=excel_buffer,
            file_name=f"Reisekosten_{monat}_{current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning(f"Keine Reisen für {monat} {current_year} gefunden")

# Regelsätze anzeigen
st.divider()
st.subheader("Aktuelle Regelsätze 2025")

col_r1, col_r2 = st.columns(2)
with col_r1:
    st.markdown("**Inland**")
    st.markdown(f"- Verpflegungspauschale: {INLAND_PAUSCHALE}€/Tag")
    st.markdown(f"- Kürzung Frühstück: 4.50€")
    st.markdown(f"- Kürzung Mittagessen: 7.50€")
    st.markdown(f"- Nächtigungspauschale: {UEBERNACHTUNG_INLAND}€/Nacht")
    st.markdown(f"- Kilometergeld: {KILOMETERGELD}€/km")

with col_r2:
    st.markdown("**Ausland (Beispiele)**")
    for land, saetze in AUSLAND_PAUSCHALEN.items():
        if land != "Andere":
            st.markdown(f"- {land}: {saetze['voll']}€ (>24h), {saetze['teil']}€ (8-24h)")
    
    st.markdown("**Kürzungen Ausland**")
    st.markdown("- Frühstück: 20% Abzug")
    st.markdown("- Mittagessen: 40% Abzug")

st.caption("Quellen: WKO-Verordnung 2025, Bundesministerium für Finanzen Österreich, USP-Guidelines 2025")