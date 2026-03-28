# PRD: Automatyczna segregacja `~/Downloads` przed klastrowaniem i AI

## Metadane
- **PRD ID:** 006-auto-downloads-bootstrap-segregation
- **Projekt:** Synapsea
- **Status:** Draft / Ready for implementation
- **Data utworzenia:** 2026-03-28
- **Zależności:** istniejące MVP + PRD 001, 002, 003, 004, 005
- **Typ zakresu:** przyrost funkcjonalny

---

## 1. Cel

Dodać etap wstępnej, automatycznej segregacji plików „luzem” z katalogu `~/Downloads`, uruchamiany na starcie `run` i `watch`, tak aby dopiero po uporządkowaniu danych wejściowych uruchamiał się obecny pipeline klastrowania i interpretacji AI.

---

## 2. Problem

Aktualny pipeline zaczyna od klasyfikacji i klastrowania na stanie katalogu, w którym pliki w `~/Downloads` często leżą bez struktury.

Skutki:
- większy szum wejściowy dla kolejnych etapów analizy,
- mniej przewidywalny kontekst dla klastrów i review,
- gorsza ergonomia codziennego użycia przy dużej liczbie plików tymczasowych.

---

## 3. Oczekiwany rezultat

Po wdrożeniu:
1. `synapsea run` i `synapsea watch` rozpoczynają się od fazy segregacji plików leżących bezpośrednio w `~/Downloads`.
2. Pliki są przenoszone do standardowych katalogów.
3. Następnie uruchamiany jest istniejący etap klastrów i AI, już na uporządkowanym drzewie.

Docelowe katalogi:
- `Dokumenty`
- `Zdjęcia`
- `Filmy`
- `Audio`
- `Instalatory`
- `Archiwa`
- `Inne`

---

## 4. Poza zakresem

Ta funkcja **nie** obejmuje:
- zmian architektury review/apply/reject,
- zmian kontraktów `review_queue.json` i `taxonomy.json`,
- wprowadzania GUI/TUI dla segregacji,
- modyfikacji algorytmu AI poza zmianą kolejności etapów,
- segregacji rekurencyjnej plików już znajdujących się w podkatalogach `~/Downloads`.

---

## 5. Zasady produktowe

1. **Kolejność etapów**
   - segregacja „luzem” zawsze wykonuje się przed klastrowaniem i AI.

2. **Bezpieczeństwo danych**
   - przy kolizji nazw obowiązuje `skip + raport` (bez nadpisywania).

3. **Spójność operacyjna**
   - zachowanie jest spójne dla `run` i `watch` na starcie procesu.

4. **Konserwatywna ingerencja**
   - modyfikowane są wyłącznie pliki z poziomu root `~/Downloads`.

---

## 6. User stories

### 6.1 Automatyczny porządek wejścia
Jako użytkownik chcę, aby pliki luzem z `~/Downloads` były automatycznie rozkładane do standardowych katalogów, żebym nie zaczynał analizy od chaosu.

### 6.2 Przewidywalny start pipeline
Jako użytkownik chcę, aby klastrowanie i AI uruchamiały się dopiero po tej segregacji, aby propozycje review były bardziej spójne.

### 6.3 Brak ryzyka nadpisania
Jako użytkownik chcę, aby przy konflikcie nazw system nie nadpisywał istniejących plików i jawnie raportował pominięcia.

---

## 7. Zakres wysokopoziomowy

Funkcja obejmuje:
- dodanie fazy bootstrapowej segregacji dla `run` i `watch`,
- mapowanie plików do standardowych katalogów na podstawie typu/rozszerzenia,
- fallback do katalogu `Inne` dla nieznanych przypadków,
- raport wykonania segregacji przed uruchomieniem istniejącego pipeline.

---

## 8. Wymagania funkcjonalne

### 8.1 Kontrakt uruchomienia

- Faza segregacji uruchamia się na początku:
  - `synapsea run`
  - `synapsea watch`
- Po zakończeniu segregacji (niezależnie od częściowych pominięć) uruchamia się standardowy pipeline klastrów i AI.

### 8.2 Zakres danych wejściowych

- Segregowane są wyłącznie pliki leżące bezpośrednio w `~/Downloads`.
- Podkatalogi i ich zawartość nie są rekurencyjnie przemieszczane w ramach tej funkcji.

### 8.3 Kategorie docelowe

System mapuje pliki do katalogów:
- `Dokumenty`
- `Zdjęcia`
- `Filmy`
- `Audio` (kategoria łącząca wcześniejsze „Muzyka” i „Audio”)
- `Instalatory`
- `Archiwa`
- `Inne` (fallback dla plików niepasujących do znanych reguł)

### 8.4 Polityka kolizji i błędów

- Jeśli plik docelowy już istnieje: element jest pomijany (`skip`), bez nadpisania.
- Błędy pojedynczych plików nie blokują całej fazy segregacji.
- Raport segregacji zawiera co najmniej: `requested`, `moved`, `skipped`, `errors`.

### 8.5 Wymóg kolejności pipeline

- Klastrowanie oraz interpretacja AI są uruchamiane dopiero po zakończeniu fazy segregacji startowej.

---

## 9. Kryteria akceptacji

- `run` i `watch` uruchamiają fazę segregacji na starcie.
- Pliki z root `~/Downloads` trafiają do właściwych katalogów standardowych.
- Nieznane typy trafiają do `Inne`.
- Kolizje nazw są pomijane i raportowane bez nadpisania danych.
- Pliki z podkatalogów `~/Downloads` nie są przemieszczane przez tę funkcję.
- Po fazie segregacji istniejący pipeline klastrów/AI działa bez regresji.

---

## 10. Ryzyka

- ryzyko błędnego mapowania nietypowych rozszerzeń do `Inne`,
- ryzyko wzrostu czasu startu `run/watch` przy bardzo dużej liczbie plików luzem,
- ryzyko niespójnych oczekiwań użytkownika co do obsługi plików już posegregowanych w podkatalogach.

---

## 11. Weryfikacja

Minimalny zestaw walidacji:
- test `run` z plikami luzem i potwierdzenie kolejności: segregacja -> pipeline,
- test `watch` potwierdzający fazę startową segregacji,
- test mapowania kategorii standardowych oraz fallbacku do `Inne`,
- test kolizji nazw (`skip + raport`),
- test braku rekurencyjnego przenoszenia plików z podkatalogów,
- test regresji uruchomienia klastrów/AI po zakończonej segregacji.
