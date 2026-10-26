# Dane testowe

| Plik | Co sprawdza | Polecenie | Oczekiwany wynik |
|---|---|---|---|
| `osoby.csv` | polskie znaki, puste wartości, przecinek i cudzysłów w polu | `python -m converter samples/osoby.csv json -o output` | `osoby.json`: 3 obiekty, klucze w kolejności nagłówka, puste komórki jako `""`, `"Łódź"` bez zmian |
| `produkty_excel.csv` | separator `;` (eksport z polskiego Excela), wartości typu `007`, `2,50` | `python -m converter samples/produkty_excel.csv json -o output` | `"kod": "007"`, `"cena": "2,50"` – wartości jako tekst, puste komórki jako `""` |
| `produkty.json` | `null`, `true/false`, liczby, brakujący klucz | `python -m converter samples/produkty.json csv -o output` | `produkty.csv` z kolumnami `id,nazwa,cena,dostępny,kategoria`; `null` i brakujące pola jako puste komórki |
| `notatka.txt` | polskie znaki, puste linie, typograficzne cudzysłowy, `€` | `python -m converter samples/notatka.txt docx -o output` | `notatka.docx`: 7 akapitów (w tym 2 puste) w tej samej kolejności co linie pliku, polskie znaki bez zmian |
| `dokument.docx` | nagłówek, pogrubienie, kursywa, polskie znaki | `python -m converter samples/dokument.docx pdf -o output` | `dokument.pdf` (1 strona): nagłówek i 3 akapity, formatowanie i polskie znaki zachowane |
| `uszkodzony.docx` | obcięty plik DOCX | `python -m converter samples/uszkodzony.docx pdf -o output` | brak pliku wynikowego; komunikat `LibreOffice zakończył pracę z błędem ...` i kod wyjścia 1 |
| brak LibreOffice | wykrycie braku programu | `$env:LIBREOFFICE_PATH = "C:\brak\soffice.com"`, potem polecenie dla `dokument.docx`; na koniec `Remove-Item Env:LIBREOFFICE_PATH` | komunikat `Nie znaleziono LibreOffice ...` ze wskazówką i kod wyjścia 1 |
| `uszkodzony.json` | błędna składnia JSON | `python -m converter samples/uszkodzony.json csv -o output` | brak pliku wynikowego; komunikat `Niepoprawny JSON (wiersz 2, kolumna 34) ...` i kod wyjścia 1 |
