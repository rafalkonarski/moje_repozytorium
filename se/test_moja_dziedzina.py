import json
import sys
from pathlib import Path

# Umożliwia import z katalogu se/ niezależnie od miejsca uruchomienia skryptu
KATALOG_SE = Path(__file__).resolve().parent
if str(KATALOG_SE) not in sys.path:
    sys.path.insert(0, str(KATALOG_SE))

from silnik import wnioskuj_w_przod, wnioskuj_wstecz

PLIK_BAZY = KATALOG_SE.parent / "wiedza" / "moja_dziedzina.json"


def uruchom_testy():
    baza = json.loads(PLIK_BAZY.read_text(encoding="utf-8"))
    cel = baza["cel"]

    przypadki = [
        (
            "T1 (typowy: studia, budżetowy, wysoka mobilność)",
            {"budzet": 2800, "zastosowanie": "biuro_studia", "mobilnosc": "wysoka", "system_os": "Windows"},
            "ACER_SWIFT_3",
        ),
        (
            "T2 (typowy: programowanie, premium, Linux)",
            {"budzet": 8500, "zastosowanie": "programowanie", "mobilnosc": "wysoka", "system_os": "Linux"},
            "THINKPAD_P14S",
        ),
        (
            "T3 (granica przedziału: budżet dokładnie na progu 3500)",
            {"budzet": 3500, "zastosowanie": "biuro_studia", "mobilnosc": "wysoka", "system_os": "Windows"},
            "ASUS_ZENBOOK_14",
        ),
        (
            "T4 (brak wyniku: programowanie, budżet < 3500, macOS)",
            {"budzet": 3000, "zastosowanie": "programowanie", "mobilnosc": "wysoka", "system_os": "macOS"},
            None,
        ),
        (
            "T5 (konflikt R0 vs R16: grafika 3D, premium, macOS)",
            {"budzet": 9000, "zastosowanie": "grafika_3d", "mobilnosc": "wysoka", "system_os": "macOS"},
            "APPLE_MACBOOK_PRO_14",
        ),
    ]

    zaliczone = 0
    for nazwa, dane, oczekiwany in przypadki:
        # 1. Wnioskowanie w przód
        fakty_przod, slad_przod = wnioskuj_w_przod(baza, dane)
        wynik_przod = fakty_przod.get(cel)

        # 2. Wnioskowanie wstecz (symulacja odpowiedzi użytkownika ze słownika dane)
        slad_wstecz = []
        wynik_wstecz = wnioskuj_wstecz(
            baza,
            cel,
            {},
            lambda atrybut, powod=None: dane.get(atrybut),
            slad_wstecz,
            None,
        )

        ok = (wynik_przod == oczekiwany) and (wynik_wstecz == oczekiwany)
        status = "OK" if ok else "BŁĄD"
        if ok:
            zaliczone += 1

        print(f"[{status}] {nazwa}")
        print(f"      Oczekiwany: {oczekiwany} | W przód: {wynik_przod} ({' -> '.join(slad_przod)}) | Wstecz: {wynik_wstecz}")

    print(f"\nZaliczone przypadki: {zaliczone}/{len(przypadki)}")
    if zaliczone != len(przypadki):
        sys.exit(1)


if __name__ == "__main__":
    uruchom_testy() 