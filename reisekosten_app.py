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

    datum_start = st.date_input("Startdatum", value=datetime.now().date())
    uhrzeit_start = st.time_input("Startzeit", value=datetime.now().time().replace(second=0, microsecond=0))
    datum_ende = st.date_input("Enddatum", value=datetime.now().date())
    uhrzeit_ende = st.time_input("Endzeit", value=datetime.now().time().replace(second=0, microsecond=0))

    km = st.number_input("Gefahrene Kilometer (eigener PKW)", min_value=0.0, step=0.1)
    mitfahrer = st.slider("Anzahl Mitfahrer", 0, 4)

    frühstück = st.checkbox("Frühstück gestellt?")
    mittagessen = st.checkbox("Mittagessen gestellt?")
    abendessen = st.checkbox("Abendessen gestellt?")

    submitted = st.form_submit_button("Berechnen")

if submitted:
    start = datetime.combine(datum_start, uhrzeit_start)
    ende = datetime.combine(datum_ende, uhrzeit_ende)

    dauer = ende - start
    stunden = dauer.total_seconds() / 3600

    if stunden < 3:
        tagesgeld = 0.0
    elif 3 <= stunden < 12:
        tagesgeld = round(min(stunden, 11) * 2.5, 2)
    else:
        tagesgeld = 30.0

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


    # Belegverwaltung
    st.subheader("🧾 Zusätzliche Belege erfassen")
    beleg_typ = st.selectbox("Belegtyp", ["Hotel", "Parkticket", "Bahnticket/Öffis", "Essenseinladung", "Sonstiges"])
    beleg_betrag = st.number_input("Betrag in EUR", min_value=0.0, step=0.1, key="beleg")
    beleg_bemerkung = st.text_input("Bemerkung", key="bemerkung")
    if 'belege' not in st.session_state:
        st.session_state.belege = []

    if st.button("➕ Beleg hinzufügen"):
        st.session_state.belege.append({
            "Typ": beleg_typ,
            "Betrag": beleg_betrag,
            "Bemerkung": beleg_bemerkung
        })

    if st.session_state.belege:
        st.subheader("📋 Erfasste Belege")
        beleg_df = pd.DataFrame(st.session_state.belege)
        st.dataframe(beleg_df)

        beleg_summe = sum(b["Betrag"] for b in st.session_state.belege)
        st.write(f"**Summe zusätzliche Belege:** {beleg_summe:.2f} EUR")

        gesamt += beleg_summe

        df["Belegsumme"] = beleg_summe
        df["Gesamt inkl. Belege"] = gesamt

    # Speicherung im Session State für Monatsübersicht
    if 'abrechnungen' not in st.session_state:
        st.session_state.abrechnungen = []

    if st.button("💾 Abrechnung speichern"):
        st.session_state.abrechnungen.append(df.iloc[0].to_dict())
        st.success("Abrechnung gespeichert!")

    if st.session_state.abrechnungen:
        st.subheader("📆 Monatsübersicht")
        monats_df = pd.DataFrame(st.session_state.abrechnungen)
        st.dataframe(monats_df)

        buffer_all = BytesIO()
        with pd.ExcelWriter(buffer_all, engine="openpyxl") as writer:
            monats_df.to_excel(writer, index=False, sheet_name="Monatsübersicht")
        st.download_button("📥 Monatsübersicht als Excel", data=buffer_all.getvalue(), file_name="Monatsabrechnung.xlsx")