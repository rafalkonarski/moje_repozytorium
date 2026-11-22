"""Z4: generator danych uczących z silnika regułowego.

Losuje wejścia z domen zadeklarowanych w bazie wiedzy, etykietę ustala silnik
(wnioskowanie w przód). Wejścia bez decyzji trafiają do raportu luk.
Uruchom z katalogu repozytorium: python ml/generator.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KATALOG = Path(__file__).resolve().parent
sys.path.insert(0, str(KATALOG.parent / "se"))
from silnik import wczytaj_baze, wnioskuj_w_przod  # noqa: E402

PLIK_BAZY = KATALOG.parent / "wiedza" / "moja_dziedzina.json"
SEED = 42
N = 2000          # liczba losowań
KROK_BUDZETU = 100  # budżet losowany co 100 PLN (realne kwoty, celowe powtórzenia wejść)
SZUM = 0.0        # brak szumu etykiet: etykieta = decyzja silnika

baza = wczytaj_baze(PLIK_BAZY)
A = baza["atrybuty"]
CEL = baza["cel"]
# wejścia = atrybuty pytane użytkownika; wnioski (klasa_sprzetu, laptop) nie trafiają do X
WEJSCIA = [n for n, opis in A.items() if opis["typ"] != "wniosek"]


def losuj_wejscie(rng):
    x = {}
    for n in WEJSCIA:
        if A[n]["typ"] == "liczba":
            lo, hi = A[n]["zakres"]
            x[n] = int(rng.integers(lo // KROK_BUDZETU, hi // KROK_BUDZETU + 1)) * KROK_BUDZETU
        else:
            x[n] = str(rng.choice(A[n]["wartosci"]))
    return x


def main():
    rng = np.random.default_rng(SEED)
    wiersze, luki = [], []
    for i in range(1, N + 1):
        x = losuj_wejscie(rng)
        fakty, slad = wnioskuj_w_przod(baza, x)
        decyzja = fakty.get(CEL)
        if decyzja is None:
            luki.append({"sample_id": i, **x, "slad": slad})
            continue
        wiersze.append({"sample_id": i, **x, CEL: decyzja, "label_source": "rule_engine"})

    df = pd.DataFrame(wiersze)
    df.to_csv(KATALOG / "dane.csv", index=False, encoding="utf-8")

    # grupy luk: ta sama kombinacja atrybutów symbolicznych + przedział budżetu
    raport_luk = {
        "opis": "Wejścia, dla których silnik nie ustalił celu (brak reguły).",
        "liczba": len(luki),
        "kombinacje": sorted({f"{l['zastosowanie']} | {l['system_os']} | budzet<3500" if l["budzet"] < 3500
                              else f"{l['zastosowanie']} | {l['system_os']} | budzet={l['budzet']}"
                              for l in luki}),
        "przypadki": luki,
    }
    (KATALOG / "luki.json").write_text(json.dumps(raport_luk, ensure_ascii=False, indent=2), encoding="utf-8")

    unikalne = df[WEJSCIA].drop_duplicates().shape[0]
    meta = {
        "baza": str(PLIK_BAZY.relative_to(KATALOG.parent)),
        "seed": SEED,
        "losowania": N,
        "probkowanie": {
            "budzet": f"równomiernie z [{A['budzet']['zakres'][0]}, {A['budzet']['zakres'][1]}] co {KROK_BUDZETU} PLN",
            **{n: "równomiernie z " + "/".join(A[n]["wartosci"]) for n in WEJSCIA if A[n]["typ"] == "wybor"},
        },
        "wiersze": len(df),
        "unikalne_wejscia": int(unikalne),
        "luki": len(luki),
        "szum_etykiet": SZUM,
        "cechy_X": WEJSCIA,
        "etykieta_y": CEL,
        "klasy": df[CEL].value_counts().to_dict(),
        "unikalne_wejscia_na_klase": df.drop_duplicates(WEJSCIA)[CEL].value_counts().to_dict(),
    }
    (KATALOG / "metadane.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wiersze: {len(df)}, unikalne wejścia: {unikalne}, luki: {len(luki)}, klasy: {df[CEL].nunique()}")
    print(df[CEL].value_counts().to_string())


if __name__ == "__main__":
    main()
