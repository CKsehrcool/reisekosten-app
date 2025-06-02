import pandas as pd
import streamlit as st
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Reisekosten Österreich", layout="centered")

AUSLANDS_DIETEN = {
    "Deutschland": 40.0,
    "Schweiz": 58.0,
    "Italien": 45.0,
    "USA": 66.0
}

INLAND_MAX_TAGEGELD = 26.40
INLAND_PAUSCHALE_PRO_STUNDE = 2.20
FRUEHSTUECK_INLAND = 5.85
NAECHTIGUNG_PAUSCHALE = 15.00
KILOMETERGELD = 0.42
MITFAHRER_ZUSCHLAG = 0.05

def berechne_tagesgeld_inland(stunden, mahlzeiten, fruehstueck):
    pauschale = min(INLAND_MAX_TAGEGELD, stunden * INLAND_PAUSCHALE_PRO_STUNDE)
    abzug = mahlzeiten * 11.55  # Mittag/Abend
    if fruehstueck:
        abzug += FRUEHSTUECK_INLAND
    return max(0, pauschale - abzug)

def berechne_tagesgeld_ausland(land, stunden, mahlzeiten, fruehstueck):
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
    abzug = mahlzeiten * 0.35 * pauschale
    if fruehstueck:
        abzug += 0.15 * pauschale
    return max(0, pauschale - abzug)

def berechne_kilometergeld(km, mitfahrer=0):
    return km * (KILOMETERGELD + min(mitfahrer, 4) * MITFAHRER_ZUSCHLAG)

if "abrechnungen" not in st.session_state:
    st.session_state.abrechnungen = []

st.title("🇦🇹 Reisekostenabrechnung – Österreich")

# Meta-Daten
name = st.text_input("Name des Mitarbeiters")
projekt = st.text_input("Projekt")
abfahrt = st.text_input("Abfahrtsort")
zielort_text = st.text_input("Zielort")
zwischenstopps = st.text_area("Zwischenstopps (optional, Komma getrennt)")

# Reisedetails
ziel = st.selectbox("Reiseziel (Inland oder Ausland)", ["Inland"] + list(AUSLANDS_DIETEN.keys()))
start_datum = st.date_input("Startdatum", value=datetime.now().date())
start_zeit = st.time_input("Startzeit", value=datetime.now().time())
start = datetime.combine(start_datum, start_zeit)

ende_datum = st.date_input("Enddatum", value=datetime.now().date())
ende_zeit = st.time_input("Endzeit", value=datetime.now().time())
ende = datetime.combine(ende_datum, ende_zeit)

dauer = (ende - start).total_seconds() / 3600
km = st.number_input("Gefahrene Kilometer (eigener PKW)", min_value=0.0)
mitfahrer = st.slider("Anzahl Mitfahrer", 0, 4)
naechte = st.number_input("Nächtigungen ohne Beleg", min_value=0)
fruehstueck = st.checkbox("Frühstück enthalten")
mahlzeiten = st.slider("Kostenlose Mittag-/Abendessen", 0, 2)

# Belege
st.subheader("🧾 Belege")
parken = st.number_input("Parkticket (€)", min_value=0.0)
hotel = st.number_input("Hotelübernachtung (Beleg) (€)", min_value=0.0)
essen = st.number_input("Einladungen / Bewirtung (€)", min_value=0.0)
sonstiges = st.number_input("Sonstiges (€)", min_value=0.0)
bahn = st.number_input("Bahn-/Öffitickets (€)", min_value=0.0)

if st.button("➕ Abrechnung speichern"):
    if ziel == "Inland":
        tg = berechne_tagesgeld_inland(dauer, mahlzeiten, fruehstueck)
    else:
        tg = berechne_tagesgeld_ausland(ziel, dauer, mahlzeiten, fruehstueck)

    km_geld = berechne_kilometergeld(km, mitfahrer)
    naechtigung = naechte * NAECHTIGUNG_PAUSCHALE
    beleg_summe = parken + hotel + essen + sonstiges + bahn
    gesamt = round(tg + km_geld + naechtigung + beleg_summe, 2)

    eintrag = {
        "Name": name,
        "Projekt": projekt,
        "Von": abfahrt,
        "Nach": zielort_text,
        "Stopps": zwischenstopps,
        "Ziel": ziel,
        "Start": start,
        "Ende": ende,
        "Dauer (h)": round(dauer, 2),
        "Tagesgeld (€)": round(tg, 2),
        "Kilometergeld (€)": round(km_geld, 2),
        "Nächtigungspauschale (€)": round(naechtigung, 2),
        "Parken (€)": parken,
        "Hotel (€)": hotel,
        "Einladungen (€)": essen,
        "Sonstiges (€)": sonstiges,
        "Bahn (€)": bahn,
        "Gesamt (€)": gesamt
    }

    st.session_state.abrechnungen.append(eintrag)
    st.success("✔ Abrechnung gespeichert")

if st.session_state.abrechnungen:
    df = pd.DataFrame(st.session_state.abrechnungen)
    st.subheader("📊 Übersicht")
    st.dataframe(df, use_container_width=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    st.download_button("📥 Gesamtabrechnung als Excel", data=output.getvalue(),
                       file_name="abrechnung_at.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
