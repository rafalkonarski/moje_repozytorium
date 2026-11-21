"""Interfejs systemu ekspertowego. Uruchom: python3 -m streamlit run app.py"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "se"))
from silnik import coto, wczytaj_baze, wnioskuj_w_przod, wyjasnij_jak  # noqa: E402
from weryfikacja import weryfikuj  # noqa: E402

PLIK_BAZY = Path(__file__).parent / "wiedza" / "moja_dziedzina.json"
baza = wczytaj_baze(PLIK_BAZY)

st.set_page_config(page_title=baza["nazwa"])
st.title(baza["nazwa"])

with st.sidebar:
    st.header("Weryfikacja bazy wiedzy")
    raport = weryfikuj(baza)
    if not raport:
        st.success("Nie wykryto problemów.")
    for poziom, komunikat in raport:
        (st.error if poziom == "BŁĄD" else st.warning)(komunikat)

with st.form("konsultacja"):
    fakty = {}
    for nazwa, opis in baza["atrybuty"].items():
        if opis["typ"] == "liczba":
            lo, hi = opis.get("zakres", [-100, 100])
            fakty[nazwa] = st.slider(opis["pytanie"], lo, hi, (lo + hi) // 2)
        elif opis["typ"] == "wybor":
            fakty[nazwa] = st.radio(opis["pytanie"], opis["wartosci"], horizontal=True)
    wyslano = st.form_submit_button("Doradź")

if wyslano:
    wynik, slad = wnioskuj_w_przod(baza, fakty)
    cel = wynik.get(baza["cel"])
    if cel is None:
        st.error("Brak rekomendacji: żadna reguła w bazie nie obejmuje tych danych.")
    else:
        st.success(f"Polecam: {cel}")
        opis = coto(baza, slad)
        if opis:
            st.info(f"Co to jest? {opis}")
    with st.expander("Jak do tego doszedłem?"):
        for krok in wyjasnij_jak(baza, slad):
            st.text(krok)

    # raport do pobrania: dane, wynik, wyjaśnienie „jak?” i weryfikacja bazy
    tekst = [
        f"Raport konsultacji — {baza['nazwa']}",
        "",
        "Dane wejściowe:",
        *[f"  {nazwa}: {wartosc}" for nazwa, wartosc in fakty.items()],
        "",
        f"Wynik: {cel if cel is not None else 'brak rekomendacji'}",
        f"Co to jest? {coto(baza, slad) or '-'}",
        "",
        "Jak do tego doszedłem?",
        *wyjasnij_jak(baza, slad),
        "",
        "Weryfikacja bazy wiedzy:",
        *([f"  [{poziom}] {komunikat}" for poziom, komunikat in raport] or ["  Nie wykryto problemów."]),
    ]
    st.download_button("Pobierz raport", "\n".join(tekst), file_name="raport.txt")
