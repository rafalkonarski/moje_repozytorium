"""Z4: Pipeline (one-hot + drzewo CART), uczenie tylko na treningu.

Wyniki: ml/drzewo.txt (export_text), ml/drzewo.png (plot_tree).
Zbiór testowy z ml/podzial.json NIE jest tu używany (zamknięty do Z6).
Uruchom: python ml/trening.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder  # noqa: E402
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree  # noqa: E402

KATALOG = Path(__file__).resolve().parent
SEED = 42

meta = json.loads((KATALOG / "metadane.json").read_text(encoding="utf-8"))
podzial = json.loads((KATALOG / "podzial.json").read_text(encoding="utf-8"))
CECHY, CEL = meta["cechy_X"], meta["etykieta_y"]
df = pd.read_csv(KATALOG / "dane.csv")
# typ cechy z danych: liczby (budżet) bez zmian, tekst (zastosowanie, mobilność, system) -> one-hot
SYMB = [c for c in CECHY if not pd.api.types.is_numeric_dtype(df[c])]
trening = df[~df["sample_id"].isin(set(podzial["test_sample_id"]))]
X_train, y_train = trening[CECHY], trening[CEL]  # tylko wejścia; bez sample_id, label_source i wniosków

kod = ColumnTransformer(
    [("sym", OneHotEncoder(handle_unknown="ignore"), SYMB)],
    remainder="passthrough",          # budżet bez zmian, drzewo samo szuka progów
    verbose_feature_names_out=False)
model = Pipeline([
    ("kod", kod),
    ("drzewo", DecisionTreeClassifier(criterion="entropy", max_depth=8,
                                      random_state=SEED)),
])
model.fit(X_train, y_train)            # fit tylko na treningu

drzewo = model.named_steps["drzewo"]
nazwy = list(model.named_steps["kod"].get_feature_names_out())
tekst = export_text(drzewo, feature_names=nazwy, decimals=1)
(KATALOG / "drzewo.txt").write_text(tekst, encoding="utf-8")

fig, ax = plt.subplots(figsize=(38, 13))
etykiety = plot_tree(drzewo, feature_names=nazwy, class_names=list(drzewo.classes_), filled=True,
                     impurity=False, proportion=False, rounded=True, fontsize=10, ax=ax)
for t in etykiety:  # wektor liczności 16 klas jest nieczytelny na rysunku; zostaje w drzewo.txt/zbiorze
    t.set_text("\n".join(w for w in t.get_text().split("\n")
                         if "<=" in w or w.startswith(("samples", "class"))))
fig.tight_layout()
fig.savefig(KATALOG / "drzewo.png", dpi=110)

zgodnosc = (model.predict(X_train) == y_train).mean()
korzen = nazwy[drzewo.tree_.feature[0]]
print(f"trening: {len(trening)} przypadków, cechy po kodowaniu: {len(nazwy)}")
print(f"kryterium: {drzewo.criterion}, głębokość: {drzewo.get_depth()}, liście: {drzewo.get_n_leaves()}, "
      f"korzeń: {korzen} <= {drzewo.tree_.threshold[0]:.1f}")
print(f"zgodność z etykietami silnika na treningu: {zgodnosc:.3f}")
