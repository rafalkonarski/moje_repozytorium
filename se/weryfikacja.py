"""Weryfikacja bazy wiedzy (odpowiednik programu Cake z pakietu SPHINX)."""
import sys
from pathlib import Path

from silnik import OPERATORY, wczytaj_baze


def weryfikuj(baza):
    """Zwraca listę (poziom, komunikat); poziom to 'BŁĄD' albo 'UWAGA'."""
    raport = []
    atrybuty = baza["atrybuty"]
    reguly = baza["reguly"]

    # Test 1: powtórzone identyfikatory reguł
    ids = [r["id"] for r in reguly]
    for id_ in sorted({i for i in ids if ids.count(i) > 1}):
        raport.append(("BŁĄD", f"Powtórzony identyfikator reguły {id_}"))

    # Test 2: niezadeklarowane atrybuty i nieznane operatory
    for r in reguly:
        for atr, op, wart in r["jesli"]:
            if atr not in atrybuty:
                raport.append(("BŁĄD", f"{r['id']}: niezadeklarowany atrybut '{atr}'"))
            if op not in OPERATORY:
                raport.append(("BŁĄD", f"{r['id']}: nieznany operator '{op}'"))

    # TODO 3: wartości spoza dziedziny
    for r in reguly:
        for atr, op, wart in r["jesli"]:
            if atr in atrybuty and "wartosci" in atrybuty[atr] and op in ("==", "!="):
                if wart not in atrybuty[atr]["wartosci"]:
                    raport.append(("BŁĄD", f"{r['id']}: wartość '{wart}' spoza dziedziny '{atr}'"))

    # TODO 4: nieużywane atrybuty wejściowe i nieużywane wartości atrybutów typu "wybor"
    uzyte_atrybuty = {atr for r in reguly for atr, _, _ in r["jesli"]}
    uzyte_wartosci = {(atr, wart) for r in reguly for atr, _, wart in r["jesli"]}
    for atr, opis in atrybuty.items():
        if opis["typ"] != "wniosek" and atr not in uzyte_atrybuty:
            raport.append(("UWAGA", f"Atrybut '{atr}' nie jest używany w żadnej regule"))
        elif opis["typ"] == "wybor":
            for wart in opis.get("wartosci", []):
                if (atr, wart) not in uzyte_wartosci:
                    raport.append(("UWAGA", f"Wartość '{wart}' atrybutu '{atr}' nieużywana"))

    # TODO 5: warunek niemożliwy do spełnienia
    wytwarzane = {tuple(r["to"]) for r in reguly}
    for r in reguly:
        for atr, op, wart in r["jesli"]:
            if op == "==" and atrybuty.get(atr, {}).get("typ") == "wniosek" and (atr, wart) not in wytwarzane:
                raport.append(("BŁĄD", f"{r['id']}: warunek {atr} == '{wart}' nigdy niespełniony"))

    # TODO 6: pary reguł — duplikat, sprzeczność, pochłanianie
    for i, a in enumerate(reguly):
        for b in reguly[i + 1:]:
            wa = {tuple(w) for w in a["jesli"]}
            wb = {tuple(w) for w in b["jesli"]}
            if wa == wb:
                if a["to"] == b["to"]:
                    raport.append(("UWAGA", f"{a['id']} i {b['id']} są identyczne (duplikat)"))
                elif a["to"][0] == b["to"][0]:
                    raport.append(("BŁĄD", f"{a['id']} i {b['id']} są sprzeczne: te same warunki, różne wnioski"))
            elif a["to"] == b["to"]:
                if wa < wb:
                    raport.append(("UWAGA", f"{b['id']} jest pochłaniana przez {a['id']} (zbędna)"))
                elif wb < wa:
                    raport.append(("UWAGA", f"{a['id']} jest pochłaniana przez {b['id']} (zbędna)"))

    # TODO 7: cel musi być wnioskiem co najmniej jednej reguły
    if not any(r["to"][0] == baza["cel"] for r in reguly):
        raport.append(("BŁĄD", f"Cel '{baza['cel']}' nie jest wnioskiem żadnej reguły (cel nieosiągalny)"))

    return raport


if __name__ == "__main__":
    plik = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent.parent / "wiedza" / "kawa.json"
    wyniki = weryfikuj(wczytaj_baze(plik))
    if not wyniki:
        print("Baza wiedzy nie zawiera wykrytych problemów.")
    for poziom, komunikat in wyniki:
        print(f"[{poziom}] {komunikat}")
    print(f"\nZnaleziono: {len(wyniki)} (w kawa_z_bledami.json jest 10 problemów do wykrycia)")