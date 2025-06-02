import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from io import BytesIO

st.set_page_config(page_title="Reisekostenabrechnung Österreich", layout="wide")

st.title("🇦🇹 Reisekostenabrechnung nach österreichischem Finanzrecht")
st.markdown(
    "Diese App erfasst alle relevanten Angaben für die steuerliche Reisekostenabrechnung in Österreich, "
    "inkl. Beleg-Upload, Taggeld-, Nächtigungsgeld- und Kilometergeld-Berechnung. "
    "Für mehrere Reisen je Mitarbeiter. Excel-Export am Ende."
)

mitarbeiter_liste = ["Max Mustermann", "Maria Beispiel", "Hans Huber", "Frei wählbar..."]

if "reisen" not in st.session_state:
    st.session_state["reisen"] = []

def taggeld_berechnen(abreise, rueckkehr, mahlzeiten=None, ausland=False):
    diff = rueckkehr - abreise
    stunden = diff.total_seconds() / 3600
    taggeld_voll = 40 if ausland else 26.4
    taggeld = 0
    if stunden >= 24:
        tage = int(stunden // 24)
        rest = stunden % 24
        taggeld = tage * taggeld_voll
        taggeld += round((rest // 1) * (taggeld_voll / 12), 2)
    elif stunden >= 3:
        taggeld = round((stunden // 1) * (taggeld_voll / 12), 2)
    # Kürzung bei kostenlosen Mahlzeiten
    if mahlzeiten:
        if mahlzeiten.get("Mittag", False):
            taggeld *= 2/3
        if mahlzeiten.get("Abend", False):
            taggeld *= 2/3
    return round(taggeld, 2)

def km_geld(km):
    return round(km * 0.5, 2)

def reisekosten_formular(index=None):
    form_key = f"reise_{index if index is not None else 'neu'}"
    with st.form(key=form_key):
        cols = st.columns(3)
        mitarbeiter = cols[0].selectbox("Mitarbeiter", mitarbeiter_liste, key=f"mitarbeiter_{index}")
        projekt = cols[1].text_input("Projekt / Kostenstelle", key=f"projekt_{index}")
        reiseart = cols[2].selectbox("Reiseart", ["Inland", "Ausland"], key=f"reiseart_{index}")
        startort = st.text_input("Startort", key=f"startort_{index}")
        zielort = st.text_input("Zielort", key=f"zielort_{index}")
        stops = st.text_area("Zwischenstopps (optional, jeweils neue Zeile)", key=f"stops_{index}")

        col1, col2 = st.columns(2)
        abfahrt_datum = col1.date_input("Abfahrt (Datum)", value=date.today(), key=f"abfahrt_datum_{index}")
        abfahrt_zeit = col1.time_input("Abfahrt (Uhrzeit)", value=time(8, 0), key=f"abfahrt_zeit_{index}")
        rueckkehr_datum = col2.date_input("Rückkehr (Datum)", value=date.today(), key=f"rueckkehr_datum_{index}")
        rueckkehr_zeit = col2.time_input("Rückkehr (Uhrzeit)", value=time(17, 0), key=f"rueckkehr_zeit_{index}")

        abfahrt_dt = datetime.combine(abfahrt_datum, abfahrt_zeit)
        rueckkehr_dt = datetime.combine(rueckkehr_datum, rueckkehr_zeit)

        transportmittel = st.multiselect(
            "Transportmittel", ["PKW (privat)", "Bahn", "Flug", "Mietwagen", "Öffis", "Taxi", "Fahrrad"], key=f"tm_{index}"
        )
        km_anzahl = st.number_input("Gefahrene Kilometer (nur für PKW privat, sonst 0)", min_value=0, max_value=2000, value=0, key=f"km_{index}")

        with st.expander("Mahlzeiten während der Reise (für Kürzung Taggeld):"):
            mahlzeiten = {
                "Mittag": st.checkbox("Kostenloses Mittagessen erhalten?", key=f"mittag_{index}"),
                "Abend": st.checkbox("Kostenloses Abendessen erhalten?", key=f"abend_{index}"),
            }

        nae_pa = st.radio("Nächtigungsgeld", ["Pauschale (15€/Nacht)", "Tatsächliche Hotelrechnung"], key=f"naechti_{index}")
        hotel_betrag, hotel_beleg = 0, None
        if nae_pa == "Tatsächliche Hotelrechnung":
            hotel_betrag = st.number_input("Hotelkosten (€)", min_value=0.0, step=1.0, key=f"hotel_{index}")
            hotel_beleg = st.file_uploader("Beleg für Hotel (PDF/JPG)", type=["pdf", "jpg", "jpeg", "png"], key=f"beleg_hotel_{index}")
        else:
            hotel_betrag = 15

        with st.expander("Weitere Belege hochladen"):
            belege = {}
            for kategorie in ["Mietwagen", "Öffis", "Maut", "Bewirtung", "Parken", "Sonstiges"]:
                belege[kategorie] = st.file_uploader(f"{kategorie}-Beleg (PDF/JPG)", type=["pdf", "jpg", "jpeg", "png"], key=f"beleg_{kategorie}_{index}")

        bemerkung = st.text_area("Bemerkungen (optional)", key=f"bemerk_{index}")
        submit = st.form_submit_button("Reise speichern")
        if submit:
            st.success("Reise gespeichert.")
            return {
                "Mitarbeiter": mitarbeiter,
                "Projekt": projekt,
                "Reiseart": reiseart,
                "Startort": startort,
                "Zielort": zielort,
                "Zwischenstopps": stops,
                "Abfahrt": abfahrt_dt,
                "Rückkehr": rueckkehr_dt,
                "Transportmittel": transportmittel,
                "Kilometer": km_anzahl,
                "Mahlzeiten": mahlzeiten,
                "Nächtigungsgeld": nae_pa,
                "Hotelbetrag": hotel_betrag,
                "Hotelbeleg": hotel_beleg.name if hotel_beleg else None,
                "Belege": {k: (v.name if v else None) for k, v in belege.items()},
                "Bemerkung": bemerkung,
                "Taggeld": taggeld_berechnen(abfahrt_dt, rueckkehr_dt, mahlzeiten, reiseart == "Ausland"),
                "Kilometergeld": km_geld(km_anzahl),
                "Gesamtkosten": taggeld_berechnen(abfahrt_dt, rueckkehr_dt, mahlzeiten, reiseart == "Ausland") +
                    (hotel_betrag if hotel_betrag else 0) + km_geld(km_anzahl)
            }
    return None

st.header("Neue Reise erfassen")
reise = reisekosten_formular()
if reise:
    st.session_state["reisen"].append(reise)

st.header("Reiseübersicht")
if st.session_state["reisen"]:
    df = pd.DataFrame(st.session_state["reisen"])
    st.dataframe(df[["Mitarbeiter", "Projekt", "Reiseart", "Startort", "Zielort", "Abfahrt", "Rückkehr",
                     "Taggeld", "Hotelbetrag", "Kilometergeld", "Gesamtkosten"]])
    st.markdown(f"**Anzahl Reisen:** {len(df)}")
    st.markdown(f"**Gesamtkosten (alle Reisen):** € {round(df['Gesamtkosten'].sum(), 2)}")
else:
    st.info("Noch keine Reisen erfasst.")

if st.session_state["reisen"]:
    if st.button("Alle Reisen als Excel exportieren"):
        excel_buffer = BytesIO()
        df_export = pd.DataFrame(st.session_state["reisen"])
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Reisen")
        st.download_button("Download Excel-Datei", data=excel_buffer.getvalue(),
                           file_name="Reisekostenabrechnung_Oesterreich.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("---")
st.caption("Hinweis: Diese Anwendung orientiert sich an den aktuellen steuerlichen Vorgaben für Reisekosten in Österreich (Stand 2024). Für verbindliche Auskünfte bitte immer die offiziellen WKO/BMF-Richtlinien konsultieren.")
