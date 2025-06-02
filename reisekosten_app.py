import streamlit as st
from datetime import datetime, timedelta, time

st.title("Reisekosten Österreich")

datum = st.date_input("Datum", datetime.today())

# Zeitangaben mit Session State
if "startzeit" not in st.session_state:
    st.session_state["startzeit"] = time(8, 0)
if "endzeit" not in st.session_state:
    st.session_state["endzeit"] = time(17, 0)

startzeit = st.time_input("Startzeit", value=st.session_state["startzeit"])
endzeit = st.time_input("Endzeit", value=st.session_state["endzeit"])

st.session_state["startzeit"] = startzeit
st.session_state["endzeit"] = endzeit

start = datetime.combine(datum, startzeit)
ende = datetime.combine(datum, endzeit)
if ende < start:
    ende += timedelta(days=1)

dauer = (ende - start).total_seconds() / 3600
st.write(f"Reisedauer: {dauer:.2f} Stunden")
