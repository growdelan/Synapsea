# Aktualny stan projektu

## Co działa
- Istnieje bazowy opis produktu w `prd/000-initial-prd.md`.
- Istnieje uzupełniona specyfikacja wysokopoziomowa w `spec.md`.
- Istnieje rozbita roadmapa milestone'ów w `ROADMAP.md`, zaczynająca się od `Milestone 0.5`.
- Działa minimalny entrypoint CLI `synapsea run` uruchamiany przez `uv`.
- Minimalny pipeline klasyfikuje pliki po rozszerzeniach i zapisuje decyzje do lokalnej bazy SQLite.
- Istnieje smoke test bez IO dyskowego dla podstawowego przepływu end-to-end.

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

## Co jest w trakcie
- Projekt przeszedł z etapu samej dokumentacji do etapu pierwszej implementacji.
- Kolejnym krokiem jest `Milestone 1: Kontrakty danych i walidacja ryzyk MVP`.

## Co jest następne
- Doprecyzowanie kontraktów danych dla klasyfikacji, klastrów, review i taksonomii.
- Walidacja heurystyk wzorców i integracji z lokalną warstwą interpretacji AI.
- Rozszerzenie testów o przypadki obejmujące nowe kontrakty domenowe.

## Blokery i ryzyka
- Zakres produktu jest szeroki, więc utrzymanie małych milestone'ów będzie krytyczne dla tempa prac.
- Jakość odpowiedzi z lokalnego modelu Ollama będzie wymagała wczesnej walidacji na reprezentatywnych danych.
- Skuteczność klasyfikacji i akceptowalność propozycji review trzeba będzie potwierdzić na ręcznie zweryfikowanej próbce plików.

## Ostatnie aktualizacje
- 2026-03-24: wygenerowano i uzupełniono `spec.md` oraz `ROADMAP.md` na podstawie `prd/000-initial-prd.md`.
- 2026-03-24: doprecyzowano założenia MVP dotyczące systemu operacyjnego, katalogu wejściowego, trybu działania procesu i kryteriów jakości.
- 2026-03-24: zrealizowano `Milestone 0.5`, dodając bootstrap aplikacji, podstawowy pipeline klasyfikacji, zapis decyzji oraz smoke test.
