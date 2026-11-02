# Uniwersalny konwerter plików

Projekt 1 – Programowanie V. Aplikacja desktopowa (Python 3 + Tkinter/ttk), która konwertuje pliki
między obsługiwanymi formatami. Logika konwersji jest oddzielona od interfejsu (rejestr konwerterów).

> **Status:** Lab 4 – interfejs graficzny (Tkinter/ttk) połączony z rejestrem konwerterów;
> działają 4 kierunki: CSV ↔ JSON, TXT → DOCX i DOCX → PDF (LibreOffice). Dostępny także tryb wiersza poleceń.

## Wymagania

- Python 3.10+ (testowane na 3.13, Windows) z modułem Tkinter (instalowany razem z Pythonem
  z python.org; na Linuksie pakiet `python3-tk`)
- Biblioteki z `requirements.txt`:
  - `python-docx` – tworzenie plików DOCX (TXT → DOCX),
  - `pytest` – testy automatyczne.
- [LibreOffice](https://www.libreoffice.org/download/) (testowane na Windows) – program zewnętrzny
  wymagany dla DOCX → PDF. Program jest wyszukiwany kolejno:
  1. w zmiennej środowiskowej `LIBREOFFICE_PATH` (pełna ścieżka do `soffice`),
  2. jako `soffice` / `libreoffice` w `PATH`,
  3. w standardowych katalogach instalacji (Windows, macOS, Linux).

  Przykład: `$env:LIBREOFFICE_PATH = "C:\Program Files\LibreOffice\program\soffice.com"`.
  Brak programu nie blokuje pozostałych konwersji – DOCX → PDF zgłasza wtedy czytelny błąd z instrukcją.

## Instalacja

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uruchomienie – interfejs graficzny (GUI)

```powershell
python -m converter
```

1. **Plik wejściowy → Wybierz…** – wskaż plik. Katalog zapisu ustawia się na katalog pliku (można go zmienić).
2. **Format docelowy** – lista zawiera wyłącznie formaty dostępne dla rozszerzenia pliku (pobierane
   z rejestru konwerterów). Dla nieobsługiwanego pliku lista jest pusta i zablokowana, a status podaje
   obsługiwane rozszerzenia.
3. **Konwertuj** – przycisk jest aktywny tylko przy kompletnym i dozwolonym wyborze. Konwersja działa
   w wątku roboczym: okno nie zamarza, przyciski są zablokowane, widoczny jest pasek postępu.
4. Wynik: okno z komunikatem i ścieżką pliku albo okno błędu z przyczyną i dalszym krokiem.

Jeśli plik wynikowy już istnieje, GUI pyta „Czy chcesz go nadpisać?”: **Tak, nadpisz** – zastąp plik,
**Nie, zapisz nowy plik** – zapisz jako `nazwa (1).ext`, **Anuluj** – nie wykonuj konwersji
(także klawisz Esc lub zamknięcie okna). Domyślny przycisk (Enter) to bezpieczny zapis nowego pliku.

## Uruchomienie – tryb wiersza poleceń

```powershell
python -m converter --list                                   # obsługiwane konwersje
python -m converter samples/osoby.csv json -o output         # CSV -> JSON
python -m converter samples/produkty.json csv -o output      # JSON -> CSV
python -m converter samples/notatka.txt docx -o output       # TXT -> DOCX
python -m converter samples/dokument.docx pdf -o output      # DOCX -> PDF (LibreOffice)
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
| C – formaty biurowe | DOCX → PDF | ✅ | Wymaga LibreOffice; układ stron może się nieznacznie różnić od Worda |

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

### DOCX → PDF (LibreOffice)

- Konwersję wykonuje LibreOffice w trybie bez interfejsu (`--headless --convert-to pdf`). Akapity,
  nagłówki i podstawowe formatowanie (pogrubienie, kursywa) są zachowane; polskie znaki bez zmian.
- Program jest uruchamiany bezpiecznie: lista argumentów (bez `shell=True`), limit czasu 120 s,
  sprawdzany kod zakończenia i to, czy plik wynikowy powstał. Polecenie i kod zakończenia trafiają do logu.
- LibreOffice używa osobnego profilu w katalogu tymczasowym, więc konwersja działa także wtedy,
  gdy LibreOffice jest otwarty.
- Kontrolowane błędy (komunikat z przyczyną i dalszym krokiem, kod wyjścia 1): brak programu,
  nieudane uruchomienie, przekroczenie czasu, kod zakończenia różny od 0, brak pliku wynikowego
  (np. uszkodzony plik DOCX).

### Istniejący plik wynikowy

Dotyczy wszystkich konwersji: istniejący plik nigdy nie jest nadpisywany bez zgody. W GUI użytkownik
wybiera nadpisanie, nową nazwę albo anulowanie. W wierszu poleceń wynik domyślnie dostaje nazwę
`nazwa (1).ext`, `nazwa (2).ext`, ...; opcja `--overwrite` zastępuje istniejący plik.
Wynik jest zapisywany do pliku tymczasowego i podmieniany dopiero po udanej konwersji.

## Testy

```powershell
python -m pytest -v
```

Dane przykładowe i oczekiwane wyniki: [samples/README.md](samples/README.md).

### Testy ręczne GUI

| Przypadek | Kroki | Oczekiwany rezultat |
|---|---|---|
| Poprawna konwersja | `samples/osoby.csv` → `.json` → Konwertuj | Komunikat „Konwersja zakończona” ze ścieżką; plik otwiera się z polskimi znakami |
| Nieobsługiwana para | Wybierz plik `.pdf` lub `.png` | Lista formatów pusta i zablokowana, przycisk nieaktywny, status z listą obsługiwanych rozszerzeń |
| Plik już istnieje | Powtórz konwersję do tego samego katalogu | Pytanie „Czy chcesz go nadpisać?”: Tak, nadpisz / Nie, zapisz nowy plik (`nazwa (1).ext`) / Anuluj (brak zmian) |
| Uszkodzony plik | `samples/uszkodzony.json` → `.csv` | Okno błędu z przyczyną (wiersz, kolumna) i podpowiedzią; aplikacja działa dalej |
| Dłuższa konwersja | `samples/dokument.docx` → `.pdf` | Pasek postępu, zablokowane przyciski, okno można przesuwać |
| Brak LibreOffice | `$env:LIBREOFFICE_PATH="C:\nie\ma\soffice.exe"`, potem DOCX → PDF | Okno błędu z instrukcją naprawy |

## Struktura projektu

```
converter/
  registry.py     # rejestr, ConversionRequest, walidacja, execute(), model błędów
  data.py         # grupa A: CSV <-> JSON
  documents.py    # grupa B: TXT -> DOCX
  office.py       # grupa C: DOCX -> PDF przez LibreOffice (subprocess)
  gui.py          # interfejs Tkinter/ttk (tylko wybór i wywołanie rejestru, wątek roboczy)
  __main__.py     # start: bez argumentów GUI, z argumentami tryb wiersza poleceń
  app_logging.py  # logowanie do converter.log
samples/          # dane testowe
tests/            # testy pytest
```

## Źródła, biblioteki i narzędzia AI

- Biblioteka standardowa Pythona: `csv`, `json`, `pathlib`, `argparse`, `logging`, `tempfile`,
  `tkinter`/`ttk` (GUI, `filedialog`, `messagebox`), `threading` i `queue` (konwersja w tle).
- [python-docx](https://python-docx.readthedocs.io/) – tworzenie plików DOCX.
- [LibreOffice](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html) –
  konwersja DOCX → PDF w trybie headless; uruchamiany przez moduł `subprocess`.
- [pytest](https://docs.pytest.org/) – testy automatyczne.
- Wzorzec rejestru konwerterów – na podstawie kodu inspiracyjnego z instrukcji projektu.
- Narzędzia AI: GitHub Copilot (asystent AI w VS Code) – pomoc przy projektowaniu struktury,
  kodu, testów i dokumentacji. Kod został przejrzany i jest rozumiany przez autora.

## Autor

Ostap Harandzha
