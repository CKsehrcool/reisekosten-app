
import streamlit as st
from datetime import datetime, date, time
import pandas as pd
import io

# Page config
st.set_page_config(page_title="Reisekostenabrechnung Österreich 2025", layout="wide")

# Regelsätze
INLAND_PAUSCHALE = 30.0
INLAND_NACHT = 17.0
KILOMETERGELD = 0.5
KÜRZUNG_INLAND = {"frühstück": 4.5, "mittagessen": 7.5}

AUSLAND_PAUSCHALEN = {
    "Deutschland": {"voll": 58.0, "teil": 34.0},
    "Schweiz": {"voll": 81.0, "teil": 48.0},
    "Liechtenstein": {"voll": 81.0, "teil": 48.0},
    "Italien": {"voll": 58.0, "teil": 34.0},
    "Tschechien": {"voll": 49.0, "teil": 30.0},
    "Slowakei": {"voll": 49.0, "teil": 30.0},
    "Frankreich": {"voll": 58.0, "teil": 34.0},
    "Andere": {"voll": 50.0, "teil": 33.0}
}
AUSLAND_KÜRZUNG = {"frühstück": 0.2, "mittagessen": 0.4}

if "reisen" not in st.session_state:
    st.session_state.reisen = []

def berechne_verpflegung(art, land, startdatum, startzeit, enddatum, endzeit, frueh, mittag):
    start_dt = datetime.combine(startdatum, startzeit)
    end_dt = datetime.combine(enddatum, endzeit)
    dauer = (end_dt - start_dt).total_seconds() / 3600
    tage = (enddatum - startdatum).days + 1

    if art == "Inland":
        betrag = tage * INLAND_PAUSCHALE
        if frueh:
            betrag -= KÜRZUNG_INLAND["frühstück"]
        if mittag:
            betrag -= KÜRZUNG_INLAND["mittagessen"]
        return max(0, round(betrag, 2))

    satz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN["Andere"])
    voll, teil = satz["voll"], satz["teil"]
    if dauer < 8:
        return 0
    elif dauer < 24:
        betrag = teil
    else:
        betrag = 2 * teil + (tage - 2) * voll if tage > 2 else 2 * teil

    if frueh:
        betrag -= teil * AUSLAND_KÜRZUNG["frühstück"]
    if mittag:
        betrag -= teil * AUSLAND_KÜRZUNG["mittagessen"]
    return max(0, round(betrag, 2))

# Layout
st.markdown("## 🇦🇹 Reisekostenabrechnung Österreich 2025")
with st.expander("Neue Reise erfassen", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        mitarbeiter = st.text_input("Mitarbeitername*")
        projekt = st.text_input("Projekt*")
        reiseart = st.radio("Reiseart*", ["Inland", "Ausland"])
        if reiseart == "Inland":
            st.info(f"Verpflegungspauschale Inland: {INLAND_PAUSCHALE:.2f}€ pro Tag")
        startdatum = st.date_input("Startdatum*", value=date.today())
        enddatum = st.date_input("Enddatum*", value=date.today())
    with col2:
        startort = st.text_input("Startort*")
        zielort = st.text_input("Zielort*")
        stops = st.text_input("Zwischenstopps (durch Komma getrennt)")
        land = st.selectbox("Zielland*", list(AUSLAND_PAUSCHALEN.keys())) if reiseart == "Ausland" else "Österreich"
        startzeit = st.time_input("Startzeit", time(8, 0))
        endzeit = st.time_input("Endzeit", time(17, 0))

    st.markdown("### Mahlzeiten inkludiert")
    colm1, colm2 = st.columns(2)
    with colm1:
        frueh = st.checkbox("Frühstück")
    with colm2:
        mittag = st.checkbox("Mittagessen")

    st.markdown("### Kosten")
    km = st.number_input("Kilometer (PKW)", min_value=0, step=1)
    uebernachtungen = st.number_input("Übernachtungen", min_value=0, step=1)
    maut = st.number_input("Mautgebühren (€)", min_value=0.0, step=1.0)
    parken = st.number_input("Parken (€)", min_value=0.0, step=1.0)
    sonstiges = st.number_input("Sonstige Kosten (€)", min_value=0.0, step=1.0)

    if st.button("Reise speichern"):
        verpflegung = berechne_verpflegung(reiseart, land, startdatum, startzeit, enddatum, endzeit, frueh, mittag)
        fahrtkosten = km * KILOMETERGELD
        uebernachtungskosten = uebernachtungen * INLAND_NACHT if reiseart == "Inland" else 0
        gesamt = verpflegung + fahrtkosten + maut + parken + sonstiges + uebernachtungskosten

        st.session_state.reisen.append({
            "Monat": startdatum.strftime("%B"),
            "Mitarbeiter": mitarbeiter,
            "Projekt": projekt,
            "Reiseart": reiseart,
            "Von": startort,
            "Nach": zielort,
            "Datum": f"{startdatum.strftime('%d.%m.%Y')} - {enddatum.strftime('%d.%m.%Y')}",
            "Tage": (enddatum - startdatum).days + 1,
            "Verpflegung": verpflegung,
            "Fahrtkosten": fahrtkosten,
            "Gesamt": gesamt,
            "Land": land
        })
        st.success("Reise gespeichert.")

# Anzeige gespeicherter Reisen + Export
st.subheader("Gespeicherte Reisen")
df = pd.DataFrame(st.session_state.reisen)
if not df.empty:
    monat = st.selectbox("Monat auswählen", sorted(df["Monat"].unique()))
    df_monat = df[df["Monat"] == monat]
    st.dataframe(df_monat, use_container_width=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_monat.to_excel(writer, index=False, sheet_name="Reisen")
    st.download_button("Excel Export herunterladen", data=buffer.getvalue(), file_name=f"Reisen_{monat}.xlsx")
else:
    st.info("Noch keine Reisen erfasst.")

# Legende
st.subheader("Aktuelle Regelsätze 2025")
colL, colR = st.columns(2)
with colL:
    st.markdown("- Verpflegungspauschale: 30.0€/Tag")
    st.markdown("- Kürzung Frühstück: 4.50€")
    st.markdown("- Kürzung Mittagessen: 7.50€")
    st.markdown("- Nächtigungspauschale: 17.0€/Nacht")
    st.markdown("- Kilometergeld: 0.5€/km")
with colR:
    st.markdown("**Ausland (Beispiele)**")
    for k, v in AUSLAND_PAUSCHALEN.items():
        st.markdown(f"- {k}: {v['voll']}€ (>24h), {v['teil']}€ (8–24h)")
    st.markdown("**Kürzungen Ausland**")
    st.markdown("- Frühstück: 20% Abzug")
    st.markdown("- Mittagessen: 40% Abzug")
    st.markdown("**Berechnungslogik**")
    st.markdown("- 24h: Volle Tagespauschale")
    st.markdown("- 8–24h: Teilsatzpauschale")
    st.markdown("- <8h: Keine Verpflegungspauschale")
