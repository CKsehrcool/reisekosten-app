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

def berechne_brutto_tagesgeld(stunden, ziel):
    if ziel == "Inland":
        return min(INLAND_MAX_TAGEGELD, stunden * INLAND_PAUSCHALE_PRO_STUNDE)
    else:
        tagessatz = AUSLANDS_DIETEN.get(ziel, 0)
        if stunden >= 12:
            return tagessatz
        elif stunden >= 8:
            return tagessatz * 0.5
        elif stunden >= 6:
            return tagessatz * (1/3)
        else:
            return 0

def berechne_kilometergeld(km, mitfahrer=0):
    return km * (KILOMETERGELD + min(mitfahrer, 4) * MITFAHRER_ZUSCHLAG)

if "abrechnungen" not in st.session_state:
    st.session_state.abrechnungen = []

st.title("🇦🇹 Reisekostenabrechnung Österreich (klar dargestellt)")

with st.expander("🔹 Angaben zur Person und Reise"):
    name = st.text_input("👤 Name des Mitarbeiters")
    projekt = st.text_input("📁 Projektbezeichnung")
    abfahrt = st.text_input("🧭 Abfahrtsort / Startstation")
    zielort_text = st.text_input("🏁 Zielort")
    zwischenstopps = st.text_area("🛑 Zwischenstopps (Komma-getrennt)")

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
fruehstueck = st.checkbox("🥐 Kostenloses Frühstück erhalten?")
mahlzeiten = st.slider("Kostenlose Mittag-/Abendessen", 0, 2)

with st.expander("🧾 Zusätzliche Belege"):
    parken = st.number_input("Parkticket (€)", min_value=0.0)
    hotel = st.number_input("Hotelübernachtung (Beleg) (€)", min_value=0.0)
    einladungen = st.number_input("Einladungen / Bewirtung (€)", min_value=0.0)
    sonstiges = st.number_input("Sonstige Belege (€)", min_value=0.0)
    bahn = st.number_input("Bahn-/Öffitickets (€)", min_value=0.0)

if st.button("➕ Abrechnung speichern"):
    brutto_tg = berechne_brutto_tagesgeld(dauer, ziel)
    if ziel == "Inland":
        kuerzung_frueh = FRUEHSTUECK_INLAND if fruehstueck else 0
        kuerzung_mahl = mahlzeiten * 11.55
    else:
        kuerzung_frueh = brutto_tg * 0.15 if fruehstueck else 0
        kuerzung_mahl = brutto_tg * 0.35 * mahlzeiten

    netto_tg = max(0, brutto_tg - kuerzung_frueh - kuerzung_mahl)
    km_geld = berechne_kilometergeld(km, mitfahrer)
    naechtigung = naechte * NAECHTIGUNG_PAUSCHALE
    beleg_summe = parken + hotel + einladungen + sonstiges + bahn
    gesamt = round(netto_tg + km_geld + naechtigung + beleg_summe, 2)

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
        "Brutto-Tagesgeld (€)": round(brutto_tg, 2),
        "Kürzung Frühstück (€)": round(kuerzung_frueh, 2),
        "Kürzung Mahlzeiten (€)": round(kuerzung_mahl, 2),
        "Netto-Tagesgeld (€)": round(netto_tg, 2),
        "Kilometergeld (€)": round(km_geld, 2),
        "Nächtigung (€)": round(naechtigung, 2),
        "Belege (Summe) (€)": round(beleg_summe, 2),
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
                       file_name="abrechnung_klartext.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
