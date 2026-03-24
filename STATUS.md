# Aktualny stan projektu

## Co działa
- Istnieje bazowy opis produktu w `prd/000-initial-prd.md`.
- Istnieje uzupełniona specyfikacja wysokopoziomowa w `spec.md`.
- Istnieje rozbita roadmapa milestone'ów w `ROADMAP.md`, zaczynająca się od `Milestone 0.5`.

## Co jest skończone
- Zdefiniowano wizję produktu, zakres MVP i ograniczenia poza MVP.
- Udokumentowano główne komponenty systemu, przepływ danych i kluczowe decyzje techniczne.
- Doprecyzowano założenia operacyjne pierwszej wersji:
  - wsparcie wyłącznie dla macOS,
  - domyślny katalog `~/Downloads`,
  - ręczne uruchamianie procesu, który po starcie działa ciągle i nasłuchuje zdarzeń,
  - mierzalne kryteria jakości dla klasyfikacji i review queue.

## Co jest w trakcie
- Projekt jest na etapie przygotowanej dokumentacji produktowo-technicznej.
- Implementacja `Milestone 0.5` nie została jeszcze rozpoczęta.

## Co jest następne
- Rozpoczęcie `Milestone 0.5: Minimal end-to-end slice`.
- Przygotowanie minimalnego entrypointu CLI i prostego przepływu analizy dla `~/Downloads`.
- Zbudowanie smoke testu end-to-end zgodnie z wymaganiami roadmapy.

## Blokery i ryzyka
- Zakres produktu jest szeroki, więc utrzymanie małych milestone'ów będzie krytyczne dla tempa prac.
- Jakość odpowiedzi z lokalnego modelu Ollama będzie wymagała wczesnej walidacji na reprezentatywnych danych.
- Skuteczność klasyfikacji i akceptowalność propozycji review trzeba będzie potwierdzić na ręcznie zweryfikowanej próbce plików.

## Ostatnie aktualizacje
- 2026-03-24: wygenerowano i uzupełniono `spec.md` oraz `ROADMAP.md` na podstawie `prd/000-initial-prd.md`.
- 2026-03-24: doprecyzowano założenia MVP dotyczące systemu operacyjnego, katalogu wejściowego, trybu działania procesu i kryteriów jakości.
