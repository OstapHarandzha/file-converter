# Dane testowe

| Plik | Co sprawdza | Polecenie | Oczekiwany wynik |
|---|---|---|---|
| `osoby.csv` | polskie znaki, puste wartości, przecinek i cudzysłów w polu | `python -m converter samples/osoby.csv json -o output` | `osoby.json`: 3 obiekty, klucze w kolejności nagłówka, puste komórki jako `""`, `"Łódź"` bez zmian |
| `produkty_excel.csv` | separator `;` (eksport z polskiego Excela), wartości typu `007`, `2,50` | `python -m converter samples/produkty_excel.csv json -o output` | `"kod": "007"`, `"cena": "2,50"` – wartości jako tekst, puste komórki jako `""` |
| `produkty.json` | `null`, `true/false`, liczby, brakujący klucz | `python -m converter samples/produkty.json csv -o output` | `produkty.csv` z kolumnami `id,nazwa,cena,dostępny,kategoria`; `null` i brakujące pola jako puste komórki |
| `uszkodzony.json` | błędna składnia JSON | `python -m converter samples/uszkodzony.json csv -o output` | brak pliku wynikowego; komunikat `Niepoprawny JSON (wiersz 2, kolumna 34) ...` i kod wyjścia 1 |
