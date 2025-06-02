import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="Reisekosten Österreich", layout="wide")

# Eingaben
st.title("🇦🇹 Reisekostenabrechnung (BMF-konform, Stand 2025)")

with st.form("eingabe"):
    name = st.text_input("Mitarbeitername")
    projekt = st.text_input("Projekt")
    abfahrt = st.text_input("Abfahrtsort")
    zwischenstopps = st.text_area("Zwischenstopps (optional)")
    zielort = st.text_input("Zielort")

    start = st.datetime_input("Startzeitpunkt", value=datetime.now() - timedelta(hours=8))
    ende = st.datetime_input("Endzeitpunkt", value=datetime.now())

    km = st.number_input("Gefahrene Kilometer (eigener PKW)", min_value=0.0, step=0.1)
    mitfahrer = st.slider("Anzahl Mitfahrer", 0, 4)

    frühstück = st.checkbox("Frühstück gestellt?")
    mittagessen = st.checkbox("Mittagessen gestellt?")
    abendessen = st.checkbox("Abendessen gestellt?")

    submitted = st.form_submit_button("Berechnen")

if submitted:
    dauer = ende - start
    stunden = dauer.total_seconds() / 3600
    tage = dauer.days + (1 if stunden >= 24 else 0)

    # Inlandspauschalen
    if stunden < 3:
        tagesgeld = 0.0
    elif 3 <= stunden < 12:
        tagesgeld = round(min(stunden, 11) * 2.5, 2)
    else:
        tagesgeld = 30.0

    # Kürzungen
    kürzung = 0.0
    if frühstück:
        kürzung += 4.50
    if mittagessen:
        kürzung += 7.50
    if abendessen:
        kürzung += 7.50

    netto_tagesgeld = max(0.0, tagesgeld - kürzung)

    km_geld = round(km * 0.5 + km * mitfahrer * 0.15, 2)

    gesamt = round(netto_tagesgeld + km_geld, 2)

    df = pd.DataFrame([{
        "Mitarbeiter": name,
        "Projekt": projekt,
        "Abfahrt": abfahrt,
        "Ziel": zielort,
        "Start": start.strftime("%d.%m.%Y %H:%M"),
        "Ende": ende.strftime("%d.%m.%Y %H:%M"),
        "Tagesgeld (brutto)": tagesgeld,
        "Kürzung": kürzung,
        "Tagesgeld (netto)": netto_tagesgeld,
        "Kilometergeld": km_geld,
        "Gesamt": gesamt
    }])

    st.dataframe(df)

    # Excel Export
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    st.download_button("📥 Excel Export", data=buffer.getvalue(), file_name="Reisekostenabrechnung.xlsx")