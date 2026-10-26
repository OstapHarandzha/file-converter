# Uniwersalny konwerter plików

Projekt 1 – Programowanie V. Aplikacja desktopowa (Python 3 + Tkinter/ttk), która konwertuje pliki
między obsługiwanymi formatami. Logika konwersji jest oddzielona od interfejsu (rejestr konwerterów).

> **Status:** Lab 3 (w trakcie) – działa CSV ↔ JSON i TXT → DOCX w trybie wiersza poleceń (bez GUI).

## Wymagania

- Python 3.10+ (testowane na 3.13, Windows)
- Biblioteki z `requirements.txt`:
  - `python-docx` – tworzenie plików DOCX (TXT → DOCX),
  - `pytest` – testy automatyczne.
- LibreOffice – wymagany dopiero dla konwersji z grupy C

## Instalacja

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uruchomienie (tryb bez GUI)

```powershell
python -m converter --list                                   # obsługiwane konwersje
python -m converter samples/osoby.csv json -o output         # CSV -> JSON
python -m converter samples/produkty.json csv -o output      # JSON -> CSV
python -m converter samples/notatka.txt docx -o output       # TXT -> DOCX
python -m converter samples/osoby.csv json -o output --overwrite
```

- Bez `-o` wynik trafia do katalogu pliku wejściowego. Katalog podany w `-o` jest tworzony, jeśli nie istnieje.
- Jeśli plik wynikowy istnieje, tworzona jest bezpieczna nazwa `nazwa (1).ext`,
  chyba że podano `--overwrite`.
- Operacje i błędy są zapisywane w `converter.log`.

## Obsługiwane konwersje

| Grupa | Konwersja | Status | Znane ograniczenia |
|---|---|---|---|
| A – dane strukturalne | CSV → JSON | ✅ | Wszystkie wartości zapisywane jako tekst |
| A – dane strukturalne | JSON → CSV | ✅ | Tylko lista płaskich obiektów (bez zagnieżdżeń) |
| B – tekst i dokumenty | TXT → DOCX | ✅ | Tylko tekst – bez formatowania, nagłówków i list |

### Semantyka CSV ↔ JSON

- **Kodowanie wejścia:** UTF-8 (z BOM lub bez). Inne kodowanie → czytelny błąd.
- **CSV:** pierwszy niepusty wiersz to nagłówek; nazwy kolumn muszą być niepuste i unikalne.
  Separator wykrywany z nagłówka: `,` `;` lub tabulator. Każdy wiersz musi mieć tyle pól co nagłówek.
  Puste wiersze są pomijane.
- **Akceptowana struktura JSON:** lista płaskich obiektów:
  ```json
  [{"imię": "Anna", "wiek": 30}, {"imię": "Jan", "miasto": null}]
  ```
  Wartości: tekst, liczba, `true`/`false`, `null`. Zagnieżdżone obiekty i listy są odrzucane.
- **CSV → JSON:** kolejność i nazwy kolumn zachowane; wartości jako tekst (np. `"007"` zostaje `"007"`);
  pusta komórka → `""`. Wynik: UTF-8, polskie znaki bez escape'owania.
- **JSON → CSV:** kolumny = wszystkie klucze w kolejności pierwszego wystąpienia; brak klucza lub `null` →
  pusta komórka; `true`/`false` → `true`/`false`. Wynik: separator `,`, UTF-8 z BOM (Excel poprawnie
  wyświetla polskie znaki).

### Semantyka TXT → DOCX

- **Kodowanie wejścia:** UTF-8 (z BOM lub bez). Inne kodowanie, pusty plik lub znaki sterujące
  (np. plik binarny) → czytelny błąd.
- **Akapity:** każda linia pliku tekstowego to jeden akapit, w tej samej kolejności; pusta linia to pusty
  akapit. Końce linii Windows (`\r\n`) i Unix (`\n`) są obsługiwane tak samo.
- **Wynik:** dokument Word z domyślnym stylem, bez dodatkowego formatowania; polskie znaki bez zmian.

### Istniejący plik wynikowy

Dotyczy wszystkich konwersji: istniejący plik nigdy nie jest nadpisywany bez zgody. Domyślnie wynik
dostaje nazwę `nazwa (1).ext`, `nazwa (2).ext`, ...; opcja `--overwrite` zastępuje istniejący plik.
Wynik jest zapisywany do pliku tymczasowego i podmieniany dopiero po udanej konwersji.

## Testy

```powershell
python -m pytest -v
```

Dane przykładowe i oczekiwane wyniki: [samples/README.md](samples/README.md).

## Struktura projektu

```
converter/
  registry.py     # rejestr, ConversionRequest, walidacja, execute(), model błędów
  data.py         # grupa A: CSV <-> JSON
  documents.py    # grupa B: TXT -> DOCX
  __main__.py     # tryb wiersza poleceń
  app_logging.py  # logowanie do converter.log
samples/          # dane testowe
tests/            # testy pytest
```

## Źródła, biblioteki i narzędzia AI

- Biblioteka standardowa Pythona: `csv`, `json`, `pathlib`, `argparse`, `logging`, `tempfile`.
- [python-docx](https://python-docx.readthedocs.io/) – tworzenie plików DOCX.
- [pytest](https://docs.pytest.org/) – testy automatyczne.
- Wzorzec rejestru konwerterów – na podstawie kodu inspiracyjnego z instrukcji projektu.
- Narzędzia AI: GitHub Copilot (asystent AI w VS Code) – pomoc przy projektowaniu struktury,
  kodu, testów i dokumentacji. Kod został przejrzany i jest rozumiany przez autora.

## Autor

Ostap Harandzha
