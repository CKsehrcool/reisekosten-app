
import streamlit as st
from datetime import datetime, timedelta, time

st.set_page_config(page_title="Reisekosten Österreich 2025", layout="centered")

st.title("Reisekosten Österreich 2025")

# Allgemeine Reisedaten
st.header("Allgemeine Angaben")

mitarbeiter = st.text_input("Mitarbeitername")
projekt = st.text_input("Projektbezeichnung")
reise_typ = st.selectbox("Reisetyp", ["Inland", "Ausland"])

abfahrtsort = st.text_input("Abfahrtsort")
zielort = st.text_input("Zielort")
zwischenstationen = st.text_area("Zwischenstation(en)", placeholder="Mehrere Stationen mit Komma oder Zeilenumbruch trennen")

# Erfassung mehrerer Reisen
anzahl_reisen = st.number_input("Anzahl Reisen", min_value=1, max_value=10, value=1, step=1)

gesamt_summe = 0.0

for i in range(anzahl_reisen):
    st.subheader(f"Reise {i+1}")
    datum = st.date_input(f"Reisedatum {i+1}", key=f"datum_{i}")
    startzeit = st.time_input(f"Startzeit {i+1}", value=time(8, 0), key=f"startzeit_{i}")
    endzeit = st.time_input(f"Endzeit {i+1}", value=time(17, 0), key=f"endzeit_{i}")

    start_dt = datetime.combine(datum, startzeit)
    end_dt = datetime.combine(datum, endzeit)
    if end_dt < start_dt:
        end_dt += timedelta(days=1)
    dauer = (end_dt - start_dt).total_seconds() / 3600

    st.write(f"Dauer: {dauer:.2f} Stunden")

    # Pauschalen laut österreichischem Steuerrecht 2025
    if reise_typ == "Inland":
        pauschale = 30.0 if dauer >= 8 else 0.0
        kürzung_fr = 4.50
        kürzung_mi = 7.50
        kürzung_ab = 7.50
    else:
        if dauer >= 24:
            pauschale = 50.0
        elif dauer >= 8:
            pauschale = 33.0
        else:
            pauschale = 0.0
        kürzung_fr = pauschale * 0.20
        kürzung_mi = pauschale * 0.40
        kürzung_ab = pauschale * 0.40

    fr = st.checkbox(f"Frühstück gestellt (–{kürzung_fr:.2f} €)", key=f"fr_{i}")
    mi = st.checkbox(f"Mittagessen gestellt (–{kürzung_mi:.2f} €)", key=f"mi_{i}")
    ab = st.checkbox(f"Abendessen gestellt (–{kürzung_ab:.2f} €)", key=f"ab_{i}")

    kürzungen = 0.0
    if fr:
        kürzungen += kürzung_fr
    if mi:
        kürzungen += kürzung_mi
    if ab:
        kürzungen += kürzung_ab

    erstattungsbetrag = max(0.0, pauschale - kürzungen)
    gesamt_summe += erstattungsbetrag

    st.success(f"Reise {i+1} – Erstattungsbetrag: {erstattungsbetrag:.2f} €")

# Belege Upload
st.header("Belegerfassung")
belege = st.file_uploader("Belege (PDF, JPG, PNG)", type=["pdf", "jpg", "jpeg", "png"], accept_multiple_files=True)
if belege:
    st.write(f"{len(belege)} Beleg(e) hochgeladen.")

# Gesamtsumme
st.header("Gesamtsumme")
st.success(f"➡️ Gesamt Erstattungsbetrag: {gesamt_summe:.2f} €")
