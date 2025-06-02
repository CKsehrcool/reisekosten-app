import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from io import BytesIO

st.set_page_config(page_title="Reisekostenabrechnung Österreich", layout="wide")

st.title("🇦🇹 Reisekostenabrechnung nach österreichischem Finanzrecht")
st.markdown(
    "Diese App erfasst alle relevanten Angaben für die steuerliche Reisekostenabrechnung in Österreich, "
    "inkl. Beleg-Upload, Einzelbeträge, Taggeld-, Nächtigungsgeld- und Kilometergeld-Berechnung. "
    "Für mehrere Reisen je Mitarbeiter. Excel-Export am Ende."
)

mitarbeiter_liste = ["Max Mustermann", "Maria Beispiel", "Hans Huber", "Frei wählbar..."]
belegarten = [
    ("Hotel", "Tatsächliche Hotelrechnung (optional, sonst Pauschale)"),
    ("Mietwagen", "Mietwagenkosten"),
    ("Öffis", "Öffentliche Verkehrsmittel"),
    ("Maut", "Mautgebühren"),
    ("Bewirtung", "Bewirtungskosten"),
    ("Parken", "Parkgebühren"),
    ("Sonstiges", "Sonstige Ausgaben")
]

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

        pauschale_naechtigung = st.checkbox("Nur Pauschale für Nächtigung (15€/Nacht)?", value=True, key=f"pauschale_naechtigung_{index}")

        beleg_uploads = {}
        beleg_betraege = {}
        with st.expander("Belege und Einzelbeträge erfassen"):
            for belegart, beschreibung in belegarten:
                col_upload, col_betrag = st.columns([2,1])
                beleg_uploads[belegart] = col_upload.file_uploader(
                    f"{belegart}-Beleg (PDF/JPG) – {beschreibung}", 
                    type=["pdf", "jpg", "jpeg", "png"], 
                    key=f"beleg_{belegart}_{index}"
                )
                # Für Hotelbetrag: Wenn Pauschale gewählt, Betragfeld deaktivieren
                if belegart == "Hotel":
                    if pauschale_naechtigung:
                        beleg_betraege[belegart] = 15
                        col_betrag.number_input(
                            "Hotelkosten (€) [nur bei tatsächlicher Rechnung editierbar]", 
                            min_value=0.0, step=1.0, value=15.0, disabled=True, key=f"betrag_{belegart}_{index}")
                    else:
                        beleg_betraege[belegart] = col_betrag.number_input(
                            "Hotelkosten (€)", min_value=0.0, step=1.0, key=f"betrag_{belegart}_{index}")
                else:
                    beleg_betraege[belegart] = col_betrag.number_input(
                        f"{belegart} (€)", min_value=0.0, step=1.0, key=f"betrag_{belegart}_{index}")

        bemerkung = st.text_area("Bemerkungen (optional)", key=f"bemerk_{index}")
        submit = st.form_submit_button("Reise speichern")
        if submit:
            st.success("Reise gespeichert.")
            # Einzelposten in Exportspalten
            export_data = {
                "Mitarbeiter": mitarbeiter,
                "Projekt": projekt,
                "Reiseart": reiseart,
                "Startort": startort,
                "Zielort": zielort,
                "Zwischenstopps": stops,
                "Abfahrt": abfahrt_dt,
                "Rückkehr": rueckkehr_dt,
                "Transportmittel": ", ".join(transportmittel),
                "Kilometer": km_anzahl,
                "Taggeld": taggeld_berechnen(abfahrt_dt, rueckkehr_dt, mahlzeiten, reiseart == "Ausland"),
                "Kilometergeld": km_geld(km_anzahl),
                "Bemerkung": bemerkung,
            }
            # Einzelbeträge und Belege als separate Spalten
            summe_belege = 0
            for belegart, _ in belegarten:
                export_data[f"{belegart}_Betrag"] = beleg_betraege[belegart]
                export_data[f"{belegart}_Beleg"] = beleg_uploads[belegart].name if beleg_uploads[belegart] else None
                summe_belege += beleg_betraege[belegart]
            # Gesamtkosten
            export_data["Gesamtkosten"] = export_data["Taggeld"] + export_data["Kilometergeld"] + summe_belege
            return export_data
    return None

st.header("Neue Reise erfassen")
reise = reisekosten_formular()
if reise:
    st.session_state["reisen"].append(reise)

st.header("Reiseübersicht")
if st.session_state["reisen"]:
    df = pd.DataFrame(st.session_state["reisen"])
    # Sichtbare Übersicht: die wichtigsten Spalten + alle Einzelbeträge
    uebersicht_cols = [
        "Mitarbeiter", "Projekt", "Reiseart", "Startort", "Zielort", "Abfahrt", "Rückkehr",
        "Taggeld", "Kilometergeld"
    ] + [f"{b[0]}_Betrag" for b in belegarten] + ["Gesamtkosten"]
    st.dataframe(df[uebersicht_cols])
    st.markdown(f"**Anzahl Reisen:** {len(df)}")
    st.markdown(f"**Gesamtkosten (alle Reisen):** € {round(df['Gesamtkosten'].sum(), 2)}")
else:
    st.info("Noch keine Reisen erfasst.")

if st.session_state["reisen"]:
    if st.button("Alle Reisen als Excel exportieren"):
        excel_buffer = BytesIO()
        df_export = pd.DataFrame(st.session_state["reisen"])
        df_export.to_excel(excel_buffer, index=False, sheet_name="Reisen")
        st.download_button("Download Excel-Datei", data=excel_buffer.getvalue(),
                           file_name="Reisekostenabrechnung_Oesterreich.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("---")
st.caption("Hinweis: Diese Anwendung orientiert sich an den aktuellen steuerlichen Vorgaben für Reisekosten in Österreich (Stand 2024). Für verbindliche Auskünfte bitte immer die offiziellen WKO/BMF-Richtlinien konsultieren.")

