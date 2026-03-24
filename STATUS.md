# Aktualny stan projektu

## Co działa
- Istnieje bazowy opis produktu w `prd/000-initial-prd.md`.
- Istnieje uzupełniona specyfikacja wysokopoziomowa w `spec.md`.
- Istnieje rozbita roadmapa milestone'ów w `ROADMAP.md`, zaczynająca się od `Milestone 0.5`.
- Działa minimalny entrypoint CLI `synapsea run` uruchamiany przez `uv`.
- Minimalny pipeline klasyfikuje pliki po rozszerzeniach i zapisuje decyzje do lokalnej bazy SQLite.
- Istnieje smoke test bez IO dyskowego dla podstawowego przepływu end-to-end.
- Istnieją kontrakty domenowe dla `candidate_cluster`, review queue, propozycji AI i taksonomii.
- Działa heurystyczne wykrywanie klastrów dla tokenów, rozszerzeń i wzorców nazw.
- Istnieje warstwa walidacji odpowiedzi z Ollama oraz zapis review i taksonomii w formacie zgodnym ze spec.

## Co jest skończone
- Zdefiniowano wizję produktu, zakres MVP i ograniczenia poza MVP.
- Udokumentowano główne komponenty systemu, przepływ danych i kluczowe decyzje techniczne.
- Doprecyzowano założenia operacyjne pierwszej wersji:
  - wsparcie wyłącznie dla macOS,
  - domyślny katalog `~/Downloads`,
  - ręczne uruchamianie procesu, który po starcie działa ciągle i nasłuchuje zdarzeń,
  - mierzalne kryteria jakości dla klasyfikacji i review queue.
- Zrealizowano `Milestone 0.5: Minimal end-to-end slice`.
- Repo ma bootstrap projektu w układzie `src/`, plik `pyproject.toml` i podstawową komendę uruchomieniową opisaną w `README.md`.
- Zrealizowano `Milestone 1: Kontrakty danych i walidacja ryzyk MVP`.
- Zweryfikowano kontrakt lokalnej komunikacji HTTP z Ollama oraz mapowanie odpowiedzi AI do review queue.

## Co jest w trakcie
- Projekt ma ukończony bootstrap i warstwę kontraktów domenowych.
- Kolejnym krokiem jest `Milestone 2: Klasyfikacja plików i historia decyzji`.

## Co jest następne
- Rozszerzenie klasyfikacji o pełniejszą ekstrakcję cech zgodną z PRD.
- Utrwalenie historii decyzji i zapewnienie idempotencji ponownych uruchomień.
- Przygotowanie danych wejściowych pod dalsze klastrowanie bez generowania kategorii przez AI.

## Blokery i ryzyka
- Zakres produktu jest szeroki, więc utrzymanie małych milestone'ów będzie krytyczne dla tempa prac.
- Jakość odpowiedzi z lokalnego modelu Ollama będzie wymagała wczesnej walidacji na reprezentatywnych danych.
- Skuteczność klasyfikacji i akceptowalność propozycji review trzeba będzie potwierdzić na ręcznie zweryfikowanej próbce plików.

## Ostatnie aktualizacje
- 2026-03-24: wygenerowano i uzupełniono `spec.md` oraz `ROADMAP.md` na podstawie `prd/000-initial-prd.md`.
- 2026-03-24: doprecyzowano założenia MVP dotyczące systemu operacyjnego, katalogu wejściowego, trybu działania procesu i kryteriów jakości.
- 2026-03-24: zrealizowano `Milestone 0.5`, dodając bootstrap aplikacji, podstawowy pipeline klasyfikacji, zapis decyzji oraz smoke test.
- 2026-03-24: zrealizowano `Milestone 1`, dodając kontrakty domenowe, heurystyki klastrów oraz walidację odpowiedzi z Ollama.
