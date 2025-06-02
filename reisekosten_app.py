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

def brutto_tagesgeld(stunden, ziel):
    if ziel == "Inland":
        return min(INLAND_MAX_TAGEGELD, stunden * INLAND_PAUSCHALE_PRO_STUNDE)
    else:
        tg = AUSLANDS_DIETEN.get(ziel, 0)
        if stunden >= 12:
            return tg
        elif stunden >= 8:
            return tg * 0.5
        elif stunden >= 6:
            return tg * (1/3)
        else:
            return 0

def km_geld_berechnen(km, mitfahrer):
    return km * (KILOMETERGELD + min(mitfahrer, 4) * MITFAHRER_ZUSCHLAG)

if "abrechnungen" not in st.session_state:
    st.session_state.abrechnungen = []

st.title("🇦🇹 Reisekostenabrechnung – Österreich (mit Geschäftsessen)")

# Eingaben
with st.expander("🔹 Reisedaten"):
    name = st.text_input("👤 Name")
    projekt = st.text_input("📁 Projekt")
    abfahrt = st.text_input("🧭 Abfahrtsort")
    zielort_text = st.text_input("🏁 Zielort")
    zwischenstopps = st.text_area("🛑 Zwischenstopps")

ziel = st.selectbox("Reiseziel", ["Inland"] + list(AUSLANDS_DIETEN.keys()))
with st.form("reise_formular"):
    start_datum = st.date_input("Startdatum", value=datetime.now().date())
    start_zeit = st.time_input("Startzeit", value=datetime.now().time())
    ende_datum = st.date_input("Enddatum", value=datetime.now().date())
    ende_zeit = st.time_input("Endzeit", value=datetime.now().time())

    submitted = st.form_submit_button("Berechnung starten")

if submitted:
    start = datetime.combine(start_datum, start_zeit)
    ende = datetime.combine(ende_datum, ende_zeit)

km = st.number_input("Gefahrene Kilometer", min_value=0.0)
mitfahrer = st.slider("Mitfahreranzahl", 0, 4)
naechte = st.number_input("Nächtigungen ohne Beleg", min_value=0)

fruehstueck = st.checkbox("🥐 Frühstück enthalten?")
mahlzeiten = st.slider("Kostenlose Mittag-/Abendessen", 0, 2)
geschaeftsessen = st.checkbox("🍽 Geschäftsessen (nur Ausland)?")

# Belege
with st.expander("🧾 Belege"):
    parken = st.number_input("Parken (€)", min_value=0.0)
    hotel = st.number_input("Hotel (€)", min_value=0.0)
    einladungen = st.number_input("Einladungen (€)", min_value=0.0)
    sonstiges = st.number_input("Sonstiges (€)", min_value=0.0)
    bahn = st.number_input("Bahn/Öffis (€)", min_value=0.0)

if st.button("➕ Abrechnung speichern"):
    brutto = brutto_tagesgeld(dauer, ziel)
    if ziel == "Inland":
        kuerzung_fr = FRUEHSTUECK_INLAND if fruehstueck else 0
        kuerzung_m = mahlzeiten * 11.55
    else:
        if geschaeftsessen:
            kuerzung_fr = 0
            kuerzung_m = brutto * (1/3)
        else:
            kuerzung_fr = brutto * 0.15 if fruehstueck else 0
            kuerzung_m = mahlzeiten * 0.35 * brutto

    netto = max(0, brutto - kuerzung_fr - kuerzung_m)
    km_geld = km_geld_berechnen(km, mitfahrer)
    naechtig = naechte * NAECHTIGUNG_PAUSCHALE
    beleg_summe = parken + hotel + einladungen + sonstiges + bahn
    gesamt = round(netto + km_geld + naechtig + beleg_summe, 2)

    eintrag = {
        "Name": name, "Projekt": projekt, "Von": abfahrt, "Nach": zielort_text, "Stopps": zwischenstopps,
        "Ziel": ziel, "Start": start, "Ende": ende, "Dauer (h)": round(dauer, 2),
        "Brutto-Tagesgeld (€)": round(brutto, 2),
        "Kürzung Frühstück (€)": round(kuerzung_fr, 2),
        "Kürzung Mahlzeiten/Geschäftsessen (€)": round(kuerzung_m, 2),
        "Netto-Tagesgeld (€)": round(netto, 2),
        "Kilometergeld (€)": round(km_geld, 2),
        "Nächtigung (€)": round(naechtig, 2),
        "Belege (€)": round(beleg_summe, 2),
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
                       file_name="abrechnung_geschaeftsessen.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")