"""Z4: podział grupowany i warstwowy na trening/test -> ml/podzial.json.

Grupa = identyczna kombinacja wejść (powtórzenia zawsze w jednej części).
Warstwowanie po etykiecie. Jeden fold z StratifiedGroupKFold(5) to test,
który pozostaje zamknięty do Z6.
Uruchom: python ml/podzial.py
"""
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

KATALOG = Path(__file__).resolve().parent
SEED = 42
N_SPLITS = 5  # test ~ 1/5 danych

meta = json.loads((KATALOG / "metadane.json").read_text(encoding="utf-8"))
CECHY, CEL = meta["cechy_X"], meta["etykieta_y"]

df = pd.read_csv(KATALOG / "dane.csv")
grupy = df[CECHY].astype(str).agg("|".join, axis=1)

sgkf = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
# StratifiedGroupKFold wyrównuje liczbę WIERSZY klas, a nie liczbę grup: przy powtórzonych
# wejściach mała klasa może dostać w teście jedno wejście powtórzone kilka razy.
# Dlatego sprawdzamy wszystkie foldy i jako test bierzemy ten, w którym najsłabiej
# reprezentowana klasa ma najwięcej NIEZALEŻNYCH (unikalnych) wejść. Kryterium patrzy
# tylko na skład danych, nie na wyniki modelu, więc nie ma tu przecieku.
def min_unikalnych(idx):
    czesc = df.iloc[idx]
    return grupy.iloc[idx].groupby(czesc[CEL].values).nunique().min()

foldy = list(sgkf.split(df, df[CEL], groups=grupy))
NR_FOLDU = max(range(N_SPLITS), key=lambda k: min_unikalnych(foldy[k][1]))  # remis -> pierwszy
idx_trening, idx_test = foldy[NR_FOLDU]

trening, test = df.iloc[idx_trening], df.iloc[idx_test]
assert not set(grupy.iloc[idx_trening]) & set(grupy.iloc[idx_test]), "przeciek: ta sama grupa w obu częściach"

tabela = pd.DataFrame({
    "przypadki": df[CEL].value_counts(),
    "unikalne_wejscia": df.drop_duplicates(CECHY)[CEL].value_counts(),
    "trening": trening[CEL].value_counts(),
    "test": test[CEL].value_counts(),
}).fillna(0).astype(int).sort_values("przypadki", ascending=False)

podzial = {
    "metoda": f"StratifiedGroupKFold(n_splits={N_SPLITS}, shuffle=True, random_state={SEED}); test = fold {NR_FOLDU} (najwięcej unikalnych wejść najmniejszej klasy w teście)",
    "grupa": "identyczna kombinacja wejść: " + ", ".join(CECHY),
    "warstwowanie": CEL,
    "test_size": round(len(test) / len(df), 3),
    "random_state": SEED,
    "liczba_trening": len(trening),
    "liczba_test": len(test),
    "liczba_grup": int(grupy.nunique()),
    "klasy": tabela.to_dict(orient="index"),
    "test_sample_id": sorted(int(i) for i in test["sample_id"]),
}
(KATALOG / "podzial.json").write_text(json.dumps(podzial, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"trening: {len(trening)}, test: {len(test)} ({podzial['test_size']:.1%}), grupy: {podzial['liczba_grup']}")
print(tabela.to_string())
print("Razem", tabela.sum().to_dict())
