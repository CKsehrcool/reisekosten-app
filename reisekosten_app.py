import pandas as pd
import streamlit as st
from datetime import datetime

AUSLANDS_DIETEN = {
    "Deutschland": 40.0,
    "Schweiz": 58.0,
    "Italien": 45.0,
    "USA": 66.0
}

INLAND_PAUSCHALE_PRO_STUNDE = 2.20
INLAND_MAX_TAGEGELD = 26.40
NAECHTIGUNG_PAUSCHALE = 15.00
KILOMETERGELD = 0.42
MITFAHRER_ZUSCHLAG = 0.05

def berechne_tagesgeld_inland(stunden, frei_mahlzeiten=0):
    pauschale = min(INLAND_MAX_TAGEGELD, stunden * INLAND_PAUSCHALE_PRO_STUNDE)
    abzug = pauschale * (frei_mahlzeiten * 0.35)
    return max(0, pauschale - abzug)

def berechne_tagesgeld_ausland(land, stunden, frei_mahlzeiten=0):
    tagessatz = AUSLANDS_DIETEN.get(land, 0)
    if stunden >= 12:
        anteil = 1.0
    elif stunden >= 8:
        anteil = 0.5
    elif stunden >= 6:
        anteil = 1/3
    else:
        anteil = 0
    pauschale = tagessatz * anteil
    abzug = pauschale * (frei_mahlzeiten * 0.35)
    return max(0, pauschale - abzug)

def berechne_kilometergeld(km, mitfahrer=0):
    zuschlag = min(mitfahrer, 4) * MITFAHRER_ZUSCHLAG
    return km * (KILOMETERGELD + zuschlag)

st.title("🇦🇹 Österreich Reisekostenrechner")

zielort = st.selectbox("Reiseziel", ["Inland"] + list(AUSLANDS_DIETEN.keys()))

# Korrigierte Eingabe: Datum + Uhrzeit getrennt
start_datum = st.date_input("Startdatum", value=datetime.now().date())
start_zeit = st.time_input("Startzeit", value=datetime.now().time())
start = datetime.combine(start_datum, start_zeit)

ende_datum = st.date_input("Enddatum", value=datetime.now().date())
ende_zeit = st.time_input("Endzeit", value=datetime.now().time())
ende = datetime.combine(ende_datum, ende_zeit)

km = st.number_input("Gefahrene Kilometer (eigener PKW)", min_value=0.0)
mitfahrer = st.slider("Anzahl Mitfahrer", 0, 4)
naechte = st.number_input("Nächtigungen (ohne Beleg)", min_value=0, step=1)
mahlzeiten = st.slider("Anzahl kostenloser Mahlzeiten (Mittag/Abend)", 0, 2)

dauer = (ende - start).total_seconds() / 3600

if zielort == "Inland":
    tagesgeld = berechne_tagesgeld_inland(dauer, mahlzeiten)
else:
    tagesgeld = berechne_tagesgeld_ausland(zielort, dauer, mahlzeiten)

km_geld = berechne_kilometergeld(km, mitfahrer)
naechtigung = naechte * NAECHTIGUNG_PAUSCHALE
gesamt = round(tagesgeld + km_geld + naechtigung, 2)

st.subheader("🧾 Abrechnungsergebnis")
st.write(f"**Tagesgeld:** {tagesgeld:.2f} €")
st.write(f"**Kilometergeld:** {km_geld:.2f} €")
st.write(f"**Nächtigungsgeld:** {naechtigung:.2f} €")
st.write(f"**Gesamt:** {gesamt:.2f} €")

abrechnung = pd.DataFrame([{
    "Reiseziel": zielort,
    "Start": start,
    "Ende": ende,
    "Dauer (h)": round(dauer, 2),
    "Tagesgeld (€)": round(tagesgeld, 2),
    "Kilometergeld (€)": round(km_geld, 2),
    "Nächtigungsgeld (€)": round(naechtigung, 2),
    "Gesamt (€)": gesamt
}])

excel_data = abrechnung.to_excel(index=False, engine='openpyxl')

st.download_button(
    label="📥 Excel Export herunterladen",
    data=excel_data,
    file_name="reisekosten_abrechnung.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
