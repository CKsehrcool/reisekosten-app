# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
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
    start_dt = datetime.combine(reise['startdatum'], reise['startzeit'])
    end_dt = datetime.combine(reise['enddatum'], reise['endzeit'])
    dauer_stunden = (end_dt - start_dt).total_seconds() / 3600
    tage_gesamt = (reise['enddatum'] - reise['startdatum']).days + 1

    if reise['reiseart'] == 'Inland':
        pauschale_pro_tag = INLAND_PAUSCHALE
        abzug = 0
        if reise.get('fruehstück'):
            abzug += 4.50
        if reise.get('mittagessen'):
            abzug += 7.50
        gesamt = tage_gesamt * (pauschale_pro_tag - abzug)
        return max(0, round(gesamt, 2))

    # Ausland
    land = reise.get('land', 'Andere')
    vollsatz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN['Andere'])['voll']
    teilsatz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN['Andere'])['teil']

    if tage_gesamt == 1:
        return max(0, round(teilsatz, 2))
    elif tage_gesamt == 2:
        return max(0, round(2 * teilsatz, 2))
    else:
        volltage = tage_gesamt - 2
        gesamt = volltage * vollsatz + 2 * teilsatz
        return max(0, round(gesamt, 2))
        if reise.get('fruehstück'):
            abzug += 4.50
        if reise.get('mittagessen'):
            abzug += 7.50
        gesamt = tage_gesamt * (pauschale_pro_tag - abzug)
        return max(0, round(gesamt, 2))

    # Ausland
    land = reise.get('land', 'Andere')
    vollsatz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN['Andere'])['voll']
    teilsatz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN['Andere'])['teil']

    if tage_gesamt == 1:
        return max(0, round(teilsatz, 2))
    elif tage_gesamt == 2:
        return max(0, round(2 * teilsatz, 2))
    else:
        volltage = tage_gesamt - 2
        gesamt = volltage * vollsatz + 2 * teilsatz
        return max(0, round(gesamt, 2))
        if reise.get('fruehstück'):
            abzug += 4.50
        if reise.get('mittagessen'):
            abzug += 7.50
        gesamt = tage_gesamt * (pauschale_pro_tag - abzug)
        return max(0, round(gesamt, 2))

    else:  # Ausland
        land = reise.get('land', 'Andere')
        vollsatz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN['Andere'])['voll']
        teilsatz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN['Andere'])['teil']

        if tage_gesamt == 1:
            # Nur 1 Tag
            return max(0, round(teilsatz, 2))
        elif tage_gesamt == 2:
            # 1 Anreise + 1 Abreise
            return max(0, round(2 * teilsatz, 2))
        else:
            # Volle Tage dazwischen + An-/Abreise
            volltage = tage_gesamt - 2
            gesamt = volltage * vollsatz + 2 * teilsatz
            return max(0, round(gesamt, 2))
    
    else:  # Ausland
        land = reise['land']
        vollsatz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN['Andere'])['voll']
        teilsatz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN['Andere'])['teil']
        
        # Tage und Stunden berechnen
        start_dt = datetime.combine(reise['startdatum'], reise['startzeit'])
        end_dt = datetime.combine(reise['enddatum'], reise['endzeit'])
        
        # Gesamtdauer in Stunden
        stunden_gesamt = (end_dt - start_dt).total_seconds() / 3600
        
        # Tageberechnung für Ausland
        tage = (reise['enddatum'] - reise['startdatum']).days + 1
        tage_voll = tage - 1  # Volle Tage ohne An-/Abreisetag
        if stunden_gesamt > 24:
            tage_voll = max(0, tage - 2)  # Anreisetag und Abreisetag abziehen
            
        # Teiltagpauschale nur wenn mindestens 8 Stunden
        tage_teil = 1 if stunden_gesamt >= 8 else 0
        
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
        
        st.session_state.current_reise.update({
            'tage': tage,
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
        
        if reiseart == 'Ausland':
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.session_state.current_reise['startzeit'] = st.time_input("Startzeit*", time(8,0))
            with col_t2:
                st.session_state.current_reise['endzeit'] = st.time_input("Endzeit*", time(17,0))
        
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
            
            # Zusätzliche Infos für Auslandsreisen
            if reise['reiseart'] == 'Ausland':
                start_dt = datetime.combine(reise['startdatum'], reise.get('startzeit', time(0,0)))
                end_dt = datetime.combine(reise['enddatum'], reise.get('endzeit', time(0,0)))
                stunden = (end_dt - start_dt).total_seconds() / 3600
                row['Stunden'] = f"{stunden:.1f}h"
                row['Land'] = reise.get('land', '')
            
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
                    
                    if reise['reiseart'] == 'Ausland':
                        detail['Land'] = reise.get('land', '')
                        detail['Startzeit'] = reise.get('startzeit', '').strftime('%H:%M') if 'startzeit' in reise else ''
                        detail['Endzeit'] = reise.get('endzeit', '').strftime('%H:%M') if 'endzeit' in reise else ''
                    
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
    st.markdown("**Berechnungslogik**")
    st.markdown("- >24h: Volle Tagespauschale")
    st.markdown("- 8-24h: Teilsatzpauschale")
    st.markdown("- <8h: Keine Verpflegungspauschale")

st.caption("Quellen: WKO-Verordnung 2025, Bundesministerium für Finanzen Österreich, USP-Guidelines 2025")