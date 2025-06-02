
import streamlit as st
from datetime import datetime, timedelta, time

st.title("Reisekosten Österreich 2025")

# Session State für Uhrzeiten initialisieren
if "start_time" not in st.session_state:
    st.session_state["start_time"] = time(8, 0)
if "end_time" not in st.session_state:
    st.session_state["end_time"] = time(17, 0)

datum = st.date_input("Reisedatum", datetime.now().date())
startzeit = st.time_input("Startzeit", value=st.session_state["start_time"])
endzeit = st.time_input("Endzeit", value=st.session_state["end_time"])

# Speichere Eingaben
st.session_state["start_time"] = startzeit
st.session_state["end_time"] = endzeit

# Kombiniere Datum mit Uhrzeit für vollständige Datetime-Objekte
start_datetime = datetime.combine(datum, startzeit)
end_datetime = datetime.combine(datum, endzeit)

# Berechne Dauer
if end_datetime < start_datetime:
    end_datetime += timedelta(days=1)
dauer = (end_datetime - start_datetime).total_seconds() / 3600

st.write(f"Dauer der Reise: {dauer:.2f} Stunden")

# --- Inlandspauschale berechnen laut Regelwerk (gültig ab 2025) ---
verpflegungspauschale = 0.0
frühstück = 4.50
mittag = 7.50
abend = 7.50

if dauer >= 24:
    verpflegungspauschale = 30.00
elif dauer >= 8:
    verpflegungspauschale = 30.00
else:
    verpflegungspauschale = 0.00

# Kürzungen abfragen
kuerzung_fr = st.checkbox("Frühstück gestellt (−4,50 €)", value=False)
kuerzung_mi = st.checkbox("Mittagessen gestellt (−7,50 €)", value=False)
kuerzung_ab = st.checkbox("Abendessen gestellt (−7,50 €)", value=False)

kuerzung_summe = 0.0
if kuerzung_fr:
    kuerzung_summe += frühstück
if kuerzung_mi:
    kuerzung_summe += mittag
if kuerzung_ab:
    kuerzung_summe += abend

betrag_nach_kuerzung = max(0, verpflegungspauschale - kuerzung_summe)

# Ergebnis anzeigen
st.subheader("Berechnetes Taggeld (Inland, brutto)")
st.write(f"Anspruch vor Kürzungen: **{verpflegungspauschale:.2f} €**")
st.write(f"Kürzungen: **−{kuerzung_summe:.2f} €**")
st.success(f"➡️ Erstattungsbetrag: **{betrag_nach_kuerzung:.2f} €**")
