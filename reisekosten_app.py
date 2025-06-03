import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from io import BytesIO
import tempfile
from PIL import Image
import os

st.set_page_config(page_title="Reisekostenabrechnung Österreich", layout="wide")

st.title("🇦🇹 Reisekostenabrechnung nach österreichischem Finanzrecht")
st.markdown(
    "Diese App erfasst alle relevanten Angaben für die steuerliche Reisekostenabrechnung in Österreich, "
    "inkl. Beleg-Upload, Einzelbeträge, Taggeld-, Nächtigungsgeld- und Kilometergeld-Berechnung. "
    "Für mehrere Reisen je Mitarbeiter. Excel-Export am Ende."
)

mitarbeiter_liste = ["Franz Tramberger", "Maria Beispiel", "Hans Huber", "Frei wählbar..."]
belegarten = [
    ("Hotel", "Tatsächliche Hotelrechnung (optional, sonst Pauschale)"),
    ("Mietwagen", "Mietwagenkosten"),
    ("Öffis", "Öffentliche Verkehrsmittel"),
    ("Maut", "Mautgebühren"),
    ("Bewirtung", "Bewirtungskosten"),
    ("Parken", "Parkgebühren"),
    ("Sonstiges", "Sonstige Ausgaben")
]

taggeld_saetze_ausland = {
    "Deutschland": 35.30,
    "Schweiz": 36.80,
    "Frankreich": 32.70,
    "Italien": 35.80,
    "Liechtenstein": 30.70,
    "Tschechien": 31.00,
    "Andere": 30.00
}

if "reisen" not in st.session_state:
    st.session_state["reisen"] = []

def taggeld_berechnen(abreise, rueckkehr, mahlzeiten=None, reiseziel=None, ausland=False, fruehstueck_hotel=False, fruehstueck_ext=False):
    diff = rueckkehr - abreise
    stunden = diff.total_seconds() / 3600
    taggeld_voll = 26.4

    if ausland and reiseziel in taggeld_saetze_ausland:
        taggeld_voll = taggeld_saetze_ausland[reiseziel]
    elif ausland:
        taggeld_voll = taggeld_saetze_ausland["Andere"]

    taggeld = 0.0
    if stunden >= 24:
        tage = int(stunden // 24)
        rest = stunden % 24
        taggeld = tage * taggeld_voll
        taggeld += round((rest // 1) * (taggeld_voll / 12), 2)
    elif stunden >= 3:
        taggeld = round((stunden // 1) * (taggeld_voll / 12), 2)

    if not ausland:
        if mahlzeiten:
            if mahlzeiten.get("Mittag", False):
                taggeld *= 2/3
            if mahlzeiten.get("Abend", False):
                taggeld *= 2/3
        if fruehstueck_ext:
            taggeld *= 2/3

    if ausland:
        if mahlzeiten and mahlzeiten.get("Mittag", False) and mahlzeiten.get("Abend", False):
            taggeld *= 1/3

    return round(taggeld, 2)

def km_geld(km):
    return round(km * 0.5, 2)

def reisekosten_formular(reiseart, reiseziel):
    form_key = f"reise_form_{len(st.session_state['reisen'])}"
    with st.form(key=form_key):
        cols = st.columns(2)
        mitarbeiter = cols[0].selectbox("Mitarbeiter", mitarbeiter_liste, key=f"mitarbeiter_{form_key}")
        projekt = cols[1].text_input("Projekt / Kostenstelle", key=f"projekt_{form_key}")

        startort = st.text_input("Startort", key=f"startort_{form_key}")
        zielort = st.text_input("Zielort", key=f"zielort_{form_key}")
        stops = st.text_area("Zwischenstopps (optional, jeweils neue Zeile)", key=f"stops_{form_key}")

        col1, col2 = st.columns(2)
        abfahrt_datum = col1.date_input("Abfahrt (Datum)", value=date.today(), key=f"abfahrt_datum_{form_key}")
        abfahrt_zeit = col1.time_input("Abfahrt (Uhrzeit)", value=time(8, 0), key=f"abfahrt_zeit_{form_key}")
        rueckkehr_datum = col2.date_input("Rückkehr (Datum)", value=date.today(), key=f"rueckkehr_datum_{form_key}")
        rueckkehr_zeit = col2.time_input("Rückkehr (Uhrzeit)", value=time(17, 0), key=f"rueckkehr_zeit_{form_key}")

        abfahrt_dt = datetime.combine(abfahrt_datum, abfahrt_zeit)
        rueckkehr_dt = datetime.combine(rueckkehr_datum, rueckkehr_zeit)

        transportmittel = st.multiselect("Transportmittel", ["PKW (privat)", "Bahn", "Flug", "Mietwagen", "Öffis", "Taxi", "Fahrrad"], key=f"tm_{form_key}")
        km_anzahl = st.number_input("Gefahrene Kilometer (nur für PKW privat, sonst 0)", min_value=0, max_value=2000, value=0, key=f"km_{form_key}")

        with st.expander("Mahlzeiten (für Kürzung Taggeld)"):
            mahlzeiten = {
                "Mittag": st.checkbox("Kostenloses Mittagessen erhalten?", key=f"mittag_{form_key}"),
                "Abend": st.checkbox("Kostenloses Abendessen erhalten?", key=f"abend_{form_key}")
            }
            fruehstueck_hotel = st.checkbox("Frühstück war im Hotelpreis inkludiert", key=f"fruehstueck_hotel_{form_key}")
            fruehstueck_ext = st.checkbox("Kostenloses Frühstück außerhalb des Hotels erhalten", key=f"fruehstueck_ext_{form_key}")

        pauschale_naechtigung = st.checkbox("Nur Pauschale für Nächtigung (15 €/Nacht)?", value=False, key=f"pauschale_naechtigung_{form_key}")

        beleg_uploads = {}
        beleg_betraege = {}
        with st.expander("Belege & Einzelbeträge erfassen"):
            for belegart, beschreibung in belegarten:
                col_upload, col_betrag = st.columns([2, 1])
                beleg_betraege[belegart] = col_betrag.number_input(f"{belegart} (€)", min_value=0.0, step=1.0, key=f"betrag_{belegart}_{form_key}")

        sammelbelege = st.file_uploader("Sammelupload Belege (JPG/PNG, mehrere möglich)", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"sammelbelege_{form_key}")

        bemerkung = st.text_area("Bemerkungen (optional)", key=f"bemerk_{form_key}")
        submit = st.form_submit_button("Reise speichern")

        if submit:
            st.success("Reise gespeichert.")
            export_data = {
                "Mitarbeiter": mitarbeiter,
                "Projekt": projekt,
                "Reiseart": reiseart,
                "Zielland": reiseziel if reiseart == "Ausland" else "",
                "Startort": startort,
                "Zielort": zielort,
                "Zwischenstopps": stops,
                "Abfahrt": abfahrt_dt,
                "Rückkehr": rueckkehr_dt,
                "Transportmittel": ", ".join(transportmittel),
                "Kilometer": km_anzahl,
                "Taggeld": taggeld_berechnen(abfahrt_dt, rueckkehr_dt, mahlzeiten, reiseziel if reiseart == "Ausland" else None, ausland=(reiseart == "Ausland"), fruehstueck_hotel=fruehstueck_hotel, fruehstueck_ext=fruehstueck_ext),
                "Kilometergeld": km_geld(km_anzahl),
                "Bemerkung": bemerkung,
                "Belege": sammelbelege
            }
            summe_belege = 0.0
            for belegart, _ in belegarten:
                export_data[f"{belegart}_Betrag"] = beleg_betraege[belegart]
                summe_belege += beleg_betraege[belegart]
            export_data["Gesamtkosten"] = export_data["Taggeld"] + export_data["Kilometergeld"] + summe_belege
            return export_data

    return None

st.header("Neue Reise erfassen")
reiseart = st.selectbox("Reiseart", ["Inland", "Ausland"], key="reiseart_auswahl")
ausland = (reiseart == "Ausland")

reiseziel = ""
if ausland:
    reiseziel = st.selectbox("Zielland", list(taggeld_saetze_ausland.keys()), index=0, key="auslandsziel_auswahl")

reise = reisekosten_formular(reiseart, reiseziel)
if reise:
    st.session_state["reisen"].append(reise)

st.header("Reiseübersicht")
if st.session_state["reisen"]:
    df = pd.DataFrame([r for r in st.session_state["reisen"] if isinstance(r, dict)])
    uebersicht_cols = ["Mitarbeiter", "Projekt", "Reiseart", "Zielland", "Startort", "Zielort", "Abfahrt", "Rückkehr", "Taggeld", "Kilometergeld"] + [f"{b[0]}_Betrag" for b in belegarten] + ["Gesamtkosten"]
    st.dataframe(df[uebersicht_cols])
    st.markdown(f"**Anzahl Reisen:** {len(df)}")
    st.markdown(f"**Gesamtkosten (alle Reisen):** € {round(df['Gesamtkosten'].sum(), 2)}")

    if st.button("Alle Reisen als Excel exportieren"):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df[uebersicht_cols].to_excel(writer, index=False, sheet_name="Reisen")
            workbook = writer.book
            worksheet = workbook.add_worksheet("Belege")
            writer.sheets["Belege"] = worksheet
            row = 0
            for i, reise in enumerate(st.session_state["reisen"]):
                worksheet.write(row, 0, f"Reise {i+1}: {reise['Mitarbeiter']} | {reise['Startort']} → {reise['Zielort']}")
                row += 1
                if reise.get("Belege"):
                    for file in reise["Belege"]:
                        if file.type in ["image/jpeg", "image/png"]:
                            image_bytes = file.read()
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                                tmp_file.write(image_bytes)
                                tmp_path = tmp_file.name
                            worksheet.insert_image(row, 1, tmp_path, {'x_scale': 0.5, 'y_scale': 0.5})
                            row += 15
                            os.unlink(tmp_path)
                else:
                    worksheet.write(row, 1, "Keine Bildbelege hochgeladen")
                    row += 2

        st.download_button(
            "Download Excel-Datei",
            data=buffer.getvalue(),
            file_name="Reisekostenabrechnung_Oesterreich.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Noch keine Reisen erfasst.")

st.markdown("---")
st.caption("Hinweis: Diese Anwendung orientiert sich an den aktuellen steuerlichen Vorgaben für Reisekosten in Österreich (Stand 2024, Quelle: WKO/Arbeiterkammer). Für verbindliche Auskünfte bitte immer die offiziellen WKO/BMF-Richtlinien konsultieren.")


