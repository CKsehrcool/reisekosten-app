
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
