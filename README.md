# System doboru laptopa roboczego i studenckiego

System ekspertowy regułowy — zadanie Z2 z przedmiotu Inżynieria wiedzy i maszynowe uczenie.
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
