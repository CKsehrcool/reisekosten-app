
import streamlit as st
from datetime import datetime, time, timedelta

# Konfiguration
st.set_page_config(page_title="Reisekostenabrechnung", layout="wide")

# Pauschalen
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
KILOMETERGELD = 0.50

# Berechnung Verpflegung
def berechne_verpflegung(art, land, startdatum, startzeit, enddatum, endzeit, fruehstück, mittagessen):
    start_dt = datetime.combine(startdatum, startzeit)
    end_dt = datetime.combine(enddatum, endzeit)
    tage = (end_dt.date() - start_dt.date()).days + 1

    if art == "Inland":
        abzug = 0
        if fruehstück:
            abzug += 4.50
        if mittagessen:
            abzug += 7.50
        return max(0, tage * (INLAND_PAUSCHALE - abzug))
    else:
        satz = AUSLAND_PAUSCHALEN.get(land, AUSLAND_PAUSCHALEN["Andere"])
        if tage == 1:
            return satz["teil"]
        elif tage == 2:
            return 2 * satz["teil"]
        else:
            return 2 * satz["teil"] + (tage - 2) * satz["voll"]

# UI
st.title("Reisekostenabrechnung")

col1, col2 = st.columns(2)
with col1:
    reiseart = st.selectbox("Reiseart", ["Inland", "Ausland"])
    startdatum = st.date_input("Startdatum")
    startzeit = st.time_input("Startzeit", value=time(8, 0))
    fruehstück = st.checkbox("Frühstück gestellt")
with col2:
    enddatum = st.date_input("Enddatum")
    endzeit = st.time_input("Endzeit", value=time(18, 0))
    mittagessen = st.checkbox("Mittagessen gestellt")

land = "Deutschland"
if reiseart == "Ausland":
    land = st.selectbox("Zielland", list(AUSLAND_PAUSCHALEN.keys()))

kilometer = st.number_input("Gefahrene Kilometer", min_value=0, value=0, step=1)

hotel = st.number_input("Hotelkosten (€)", min_value=0.0, value=0.0, step=1.0)
parken = st.number_input("Parkgebühren (€)", min_value=0.0, value=0.0, step=1.0)
oepnv = st.number_input("ÖPNV (€)", min_value=0.0, value=0.0, step=1.0)
bewirtung = st.number_input("Bewirtung (€)", min_value=0.0, value=0.0, step=1.0)
sonstiges = st.number_input("Sonstiges (€)", min_value=0.0, value=0.0, step=1.0)

if st.button("Berechnen"):
    verpflegung = berechne_verpflegung(reiseart, land, startdatum, startzeit, enddatum, endzeit, fruehstück, mittagessen)
    kilometergeld = kilometer * KILOMETERGELD
    gesamtkosten = verpflegung + kilometergeld + hotel + parken + oepnv + bewirtung + sonstiges

    st.subheader("Ergebnis")
    st.write(f"**Verpflegungspauschale:** {verpflegung:.2f} €")
    st.write(f"**Kilometergeld:** {kilometergeld:.2f} €")
    st.write(f"**Hotel:** {hotel:.2f} €")
    st.write(f"**Parken:** {parken:.2f} €")
    st.write(f"**ÖPNV:** {oepnv:.2f} €")
    st.write(f"**Bewirtung:** {bewirtung:.2f} €")
    st.write(f"**Sonstiges:** {sonstiges:.2f} €")
    st.markdown("---")
    st.success(f"**Gesamtkosten: {gesamtkosten:.2f} €**")
