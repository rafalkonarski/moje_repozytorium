"""Silnik wnioskujący z modułem wyjaśnień (spotkanie 3)."""
import json
import operator
from pathlib import Path

OPERATORY = {
    "==": operator.eq, "!=": operator.ne,
    ">": operator.gt, ">=": operator.ge,
    "<": operator.lt, "<=": operator.le,
}


def wczytaj_baze(sciezka):
    return json.loads(Path(sciezka).read_text(encoding="utf-8"))


def warunek_spelniony(warunek, fakty):
    """warunek to lista [atrybut, operator, wartość], np. ["temperatura", ">", 22]."""
    atrybut, op, wartosc = warunek
    return atrybut in fakty and fakty[atrybut] is not None and OPERATORY[op](fakty[atrybut], wartosc)


def regula_spelniona(regula, fakty):
    return all(warunek_spelniony(w, fakty) for w in regula["jesli"])


def wnioskuj_w_przod(baza, fakty):
    """Zwraca (fakty po wnioskowaniu, lista id odpalonych reguł)."""
    fakty = dict(fakty)
    slad = []
    zmiana = True
    while zmiana:
        zmiana = False
        for regula in baza["reguly"]:
            atrybut, wartosc = regula["to"]
            if atrybut not in fakty and regula_spelniona(regula, fakty):
                fakty[atrybut] = wartosc
                slad.append(regula["id"])
                zmiana = True
    return fakty, slad


def wnioskuj_wstecz(baza, cel, fakty, zapytaj, slad=None, powod=None):
    """Ustala wartość atrybutu `cel`. Brakujące dane pobiera funkcją zapytaj(atrybut, powod)."""
    if slad is None:
        slad = []
    if cel in fakty:
        return fakty[cel]
    if cel not in baza["atrybuty"]:
        raise ValueError(f"Niezadeklarowany atrybut: {cel}")

    reguly = [r for r in baza["reguly"] if r["to"][0] == cel]

    if not reguly and baza["atrybuty"][cel]["typ"] == "wniosek":
        fakty[cel] = None
        return None

    if not reguly:
        fakty[cel] = zapytaj(cel, powod)
        return fakty[cel]

    for regula in reguly:
        spelniona = True
        for atrybut, op, wartosc in regula["jesli"]:
            znana = wnioskuj_wstecz(baza, atrybut, fakty, zapytaj, slad, regula)
            if znana is None or not OPERATORY[op](znana, wartosc):
                spelniona = False
                break
        if spelniona:
            fakty[cel] = regula["to"][1]
            slad.append(regula["id"])
            return fakty[cel]

    fakty[cel] = None
    return None


def opisz_regule(regula):
    """Reguła jako zdanie: R1: JEŚLI ... TO ..."""
    warunki = " ORAZ ".join(f"{a} {op} {w!r}" for a, op, w in regula["jesli"])
    atrybut, wartosc = regula["to"]
    return f"{regula['id']}: JEŚLI {warunki} TO {atrybut} = {wartosc!r}"


def wyjasnij_jak(baza, slad):
    """„Jak?”: każda odpalona reguła po kolei + jej metafora."""
    po_id = {r["id"]: r for r in baza["reguly"]}
    kroki = []
    for nr, id_reguly in enumerate(slad, start=1):
        regula = po_id[id_reguly]
        kroki.append(f"{nr}. {opisz_regule(regula)}")
        kroki.append(f"   → {regula['metafora']}")
    return kroki


def coto(baza, slad):
    """„Co to?”: pole coto ostatniej reguły w śladzie, która je ma."""
    po_id = {r["id"]: r for r in baza["reguly"]}
    for id_reguly in reversed(slad):
        opis = po_id[id_reguly].get("coto")
        if opis:
            return opis
    return None


def zapytaj_konsola(baza):
    """Pytanie w konsoli. Odpowiedź „?” pokazuje, dlaczego system pyta."""
    def zapytaj(atrybut, powod):
        opis = baza["atrybuty"].get(atrybut, {})
        podpowiedz = f" ({'/'.join(opis['wartosci'])})" if "wartosci" in opis else ""
        while True:
            odp = input(f"{opis.get('pytanie', atrybut)}{podpowiedz} (? = dlaczego pytam) ").strip()
            if odp == "?":
                if powod is not None:
                    print("   Pytam, bo sprawdzam regułę:", opisz_regule(powod))
                else:
                    print("   Pytam, bo to bezpośrednio potrzebne do ustalenia celu.")
                continue
            if opis.get("typ") == "liczba":
                try:
                    return float(odp.replace(",", "."))
                except ValueError:
                    print("   Podaj liczbę.")
                    continue
            if "wartosci" in opis and odp not in opis["wartosci"]:
                print("   Dozwolone:", ", ".join(opis["wartosci"]))
                continue
            return odp
    return zapytaj


if __name__ == "__main__":
    PLIK_BAZY = Path(__file__).parent.parent / "wiedza" / "moja_dziedzina.json"
    FAKTY = {"budzet": 2800, "zastosowanie": "biuro_studia", "mobilnosc": "wysoka", "system_os": "Windows"}

    baza = wczytaj_baze(PLIK_BAZY)
    cel = baza["cel"]

    print("=== Wnioskowanie w przód ===")
    fakty, slad = wnioskuj_w_przod(baza, FAKTY)
    print("Wynik:", fakty.get(cel), "| reguły:", " -> ".join(slad))

    print("\n=== Wnioskowanie wstecz ===")
    slad = []
    print("Polecam:", wnioskuj_wstecz(baza, cel, {}, zapytaj_konsola(baza), slad))
    print("Reguły:", " -> ".join(slad))

    print("\n=== Jak doszedłem do wniosku? ===")
    for krok in wyjasnij_jak(baza, slad):
        print(krok)
    print("Co to jest?", coto(baza, slad) or "(brak opisu)")