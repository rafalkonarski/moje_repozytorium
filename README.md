# System doboru laptopa roboczego i studenckiego

System ekspertowy regułowy — zadania Z2–Z4 z przedmiotu Inżynieria wiedzy i maszynowe uczenie.
Wiedza jest zapisana w `wiedza/moja_dziedzina.json`, a silnik wnioskujący w `se/silnik.py`
(wnioskowanie w przód i wstecz).

## Uruchomienie

```
python se/sprawdz_format.py wiedza/moja_dziedzina.json
python se/test_silnik.py
python se/test_moja_dziedzina.py
python se/silnik.py
```

## Konsultacja w trybie wstecz

```
> python se/silnik.py
=== Wnioskowanie w przód ===
Wynik: ACER_SWIFT_3 | reguły: P1 -> R1

=== Wnioskowanie wstecz ===
Jakie jest główne zastosowanie sprzętu? (biuro_studia/programowanie/grafika_3d) biuro_studia
Jaki jest Twoj maksymalny budżet na zakup laptopa (w PLN)? 2800
Czy wymagana jest wysoka mobilność sprzętu? (wysoka/stacjonarna) wysoka
Polecam: ACER_SWIFT_3
Reguły: P1 -> R1
```

### Dlaczego system zadał te pytania

Silnik zaczyna od celu `laptop` i sprawdza reguły od góry. Pierwsza reguła R0 zaczyna się od
warunku `zastosowanie == grafika_3d`, dlatego najpierw padło pytanie o zastosowanie; odpowiedź
`biuro_studia` odrzuciła R0 bez kolejnych pytań. Reguła R1 wymaga wniosku pośredniego
`klasa_sprzetu`, więc silnik sprawdził reguły P1–P3 i zapytał o budżet (2800 PLN → `budzetowa`),
a na końcu o mobilność. O system operacyjny nie zapytał, bo reguła R1 go nie wymaga.

## Kolejność reguł

Przy konflikcie wygrywa reguła stojąca wyżej w pliku, dlatego wyjątek R0 (grafika 3D + premium +
macOS → APPLE_MACBOOK_PRO_14) stoi przed ogólną regułą R16 (grafika 3D + premium → ASUS_PROART_STUDIOBOOK).

## Weryfikacja bazy wiedzy (Z3)

```
> python se/weryfikacja.py wiedza/moja_dziedzina.json
Baza wiedzy nie zawiera wykrytych problemów.
```

Weryfikator nie zgłasza ani błędów, ani uwag. Reguły R0 i R16 mają częściowo wspólne warunki,
ale różne wnioski, więc nie są pochłanianiem — R0 to celowy wyjątek dla macOS i stoi wyżej.

Czego weryfikator nie wykrywa w tej bazie:
- **luki w pokryciu:** dla zastosowania „programowanie”, budżetu poniżej 3500 PLN i systemu macOS
  żadna reguła nie daje decyzji (wynik None) — świadomie, bo w tym budżecie nie ma laptopa z macOS;
- **ignorowanie preferencji systemu:** R5 (biuro, premium) i R13 (grafika 3D, budżetowa) polecają
  konkretny model niezależnie od wybranego systemu operacyjnego;
- **trafność wiedzy:** weryfikacja sprawdza tylko budowę bazy, a nie to, czy rekomendacje są dobre
  (to byłaby walidacja).

## Uruchomienie aplikacji

```
python -m streamlit run app.py
```

## Dane i drzewo decyzyjne (Z4)

```
python ml/generator.py   # ml/dane.csv, ml/luki.json, ml/metadane.json
python ml/podzial.py     # ml/podzial.json (identyfikatory testu, zamknięty do Z6)
python ml/trening.py     # ml/drzewo.txt, ml/drzewo.png
```

Pakiety: `pip install -r requirements.txt` (numpy, pandas, scikit-learn, matplotlib, streamlit).

### Słownik danych `ml/dane.csv`

| Kolumna | Znaczenie | Typ | Dozwolone wartości | Rola |
|---|---|---|---|---|
| `sample_id` | identyfikator przypadku (numer losowania) | liczba | 1 … 2000 | identyfikator |
| `budzet` | maksymalny budżet użytkownika [PLN] | liczba | 2000 … 12000, co 100 | cecha X |
| `zastosowanie` | główne zastosowanie laptopa | tekst | biuro_studia, programowanie, grafika_3d | cecha X |
| `mobilnosc` | wymagana mobilność | tekst | wysoka, stacjonarna | cecha X |
| `system_os` | preferowany system operacyjny | tekst | Windows, macOS, Linux | cecha X |
| `laptop` | decyzja silnika (cel bazy) | tekst | 16 modeli z `wiedza/moja_dziedzina.json` | etykieta y |
| `label_source` | źródło etykiety | tekst | rule_engine | metadane |

Metadane generowania (ziarno, sposób próbkowania, liczności klas, szum) są w `ml/metadane.json`,
parametry podziału i liczności trening/test w `ml/podzial.json`.

**Dane.** Generator losuje 2000 wejść (ziarno 42): budżet równomiernie z 2000–12000 PLN co 100 PLN,
zastosowanie, mobilność i system równomiernie z wartości w bazie. Etykietę `laptop` ustala silnik
(`wnioskuj_w_przod`), `label_source = rule_engine`, bez szumu. Wynik: 1970 wierszy, 1200 unikalnych
wejść, 16 klas (najmniejsza: DELL_VOSTRO_3520 — 25 przypadków, 16 unikalnych wejść). 30 losowań bez
decyzji trafiło do `ml/luki.json` — wszystkie to znana luka: programowanie + macOS + budżet < 3500 PLN.

**X i y.** X = `budzet, zastosowanie, mobilnosc, system_os` (tylko dane od użytkownika).
Wniosek pośredni `klasa_sprzetu`, `sample_id` i `label_source` nie trafiają do X (przeciek).

**Podział.** `StratifiedGroupKFold(5, shuffle=True, random_state=42)`, test = jeden fold (394 przypadki,
20%), trening 1576. Grupa = identyczna kombinacja wejść, więc powtórzenia są zawsze w jednej części.
Każda klasa ma przypadki w obu częściach (min. 5 w teście), a udział testu w każdej klasie to 19–21%.
StratifiedGroupKFold wyrównuje liczbę wierszy, a nie liczbę grup: w foldzie 0 cała klasa HP_250_G9
w teście (7 przypadków) była jednym wejściem wylosowanym 7 razy. Dlatego `podzial.py` sprawdza
wszystkie 5 foldów i jako test bierze ten, w którym najsłabiej reprezentowana klasa ma najwięcej
unikalnych wejść (fold 1: min. 3 unikalne wejścia na klasę, HP_250_G9 — 4). Kryterium patrzy tylko
na skład danych, nie na wyniki modelu, więc nie powoduje przecieku.

**Drzewo.** `Pipeline(OneHotEncoder(handle_unknown="ignore") na cechach symbolicznych, budżet bez zmian
→ DecisionTreeClassifier(criterion="entropy", max_depth=8, random_state=42))`, `fit` tylko na treningu.
Wynik: głębokość 6, 17 liści, korzeń `budzet <= 6450`, zgodność z etykietami silnika na treningu 100%.

### Drzewo a reguły eksperta

| Nr | Fragment drzewa (`drzewo.txt`) | Reguła eksperta | Zgodność | Wyjaśnienie |
|---|---|---|---|---|
| 1 | korzeń `budzet <= 6450` oraz `budzet <= 3450` | P3: `budzet >= 6500` → premium; P1: `budzet < 3500` → budżetowa | zgodne na danych | Drzewo znalazło oba progi klasy sprzętu, choć `klasa_sprzetu` nie była cechą. Próg leży w połowie między 6400 a 6500 (3400 a 3500), bo budżet losowano co 100 PLN; dla kwot spoza siatki (np. 3470 PLN) drzewo da klasę średnią, a reguła budżetową. |
| 2 | `budzet > 6450`, nie biuro, `system_os_macOS > 0.5` → APPLE_MACBOOK_PRO_14 | R0 (grafika 3D + premium + macOS) i R10 (programowanie + premium + macOS) | zgodne, inna struktura | Drzewo scaliło dwie reguły z tym samym wnioskiem w jeden liść i sprawdza system przed zastosowaniem. Wyjątek R0 przed R16 jest zachowany: ProArt dostaje tylko grafika 3D bez macOS. |
| 3 | `budzet <= 3450`, programowanie, `system_os_Windows <= 0.5` → DELL_VOSTRO_3520 | R6: programowanie + budżetowa + **Linux** → DELL_VOSTRO_3520 | częściowo | Drzewo nie widziało przypadków z macOS (luka, brak etykiety), więc nie potrzebowało pytania o Linuksa. Dla programowanie + macOS + budżet < 3500 drzewo poleci Della Vostro, a silnik nie daje decyzji — model „zapełnia” lukę bez wiedzy eksperta. |

**Co to mierzy.** Etykiety pochodzą z silnika, więc 100% zgodności oznacza tylko, że drzewo
odtwarza reguły na wylosowanych danych. Nie mówi nic o trafności rekomendacji laptopów (to wymagałoby
etykiet od eksperta). Zbiór testowy nie był używany — ocena na nim dopiero w Z6.

**Ograniczenia.** Progi budżetu zależą od siatki próbkowania (co 100 PLN); drzewo zachowuje się inaczej
niż reguły w lukach pokrycia; bez szumu etykiet drzewo jest „czyste” i nie pokazuje, jak radziłoby sobie
z błędami; klasy z regułami na wąskich obszarach (R6, R7) mają najmniej przykładów.
