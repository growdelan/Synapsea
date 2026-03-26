## 1. Overview

Celem tego przyrostu jest usunięcie problemu degradacji wydajności przy aktywnej warstwie AI,
przy zachowaniu modelu human-in-the-loop i lokalności przetwarzania.

Aktualny problem:
- pełny przebieg `run` skanuje cały katalog i ponownie przelicza całą historię,
- liczba klastrów i wywołań AI rośnie wraz ze stanem historycznym,
- duże klastry przekazują zbyt duży payload do lokalnego modelu.

Docelowo system ma działać inkrementalnie i przewidywalnie szybko przy codziennym napływie małej liczby nowych plików.

---

## 2. Vision

> Synapsea ma skalować się wraz z historią użytkownika bez liniowego wzrostu czasu przetwarzania.

---

## 3. Core Principles

1. Inkrementalność ponad pełny reprocessing.
2. AI tylko tam, gdzie wnosi nową informację.
3. Brak utraty audytowalności decyzji.
4. Kompatybilność CLI (`run` pozostaje one-shot).
5. Lokalność i odporność trybu ciągłego.

---

## 4. Key Features

### 4.1 Inkrementalny pipeline (delta)

- identyfikacja zmian plików: `created`, `modified`, `deleted`,
- klasyfikacja i aktualizacja historii tylko dla delty,
- ograniczenie przeliczeń klastrów do obszarów dotkniętych zmianą.

### 4.2 Optymalizacja kosztu AI

- skrócony payload dla interpretacji klastrów,
- cache odpowiedzi AI po fingerprint klastra,
- budżet wywołań AI na cykl,
- odraczanie nadmiarowych klastrów do kolejnych cykli.

### 4.3 Tryb ciągły `watch`

- nowa komenda CLI `watch`,
- nasłuch zdarzeń systemowych,
- start bez pełnego bootstrap skanu,
- mikro-przebiegi uruchamiane przez eventy,
- błędy AI nie zatrzymują pętli watchera.

---

## 5. System Architecture

### 5.1 New/extended components

- `input_state_repository`:
  - trwały zapis ostatnio widzianego stanu wejścia (mtime/size/inode).
- `delta_engine`:
  - wyliczanie delty między stanem poprzednim a bieżącym.
- `ai_proposal_cache`:
  - trwałe mapowanie fingerprint klastra -> ostatnia poprawna propozycja AI.
- `watch_service`:
  - adaptacyjna pętla eventów folderu + wywołanie inkrementalnego pipeline.

### 5.2 Updated data flow

1. Odczyt poprzedniego stanu wejścia.
2. Wyliczenie delty.
3. Klasyfikacja tylko delty.
4. Aktualizacja wybranych klastrów.
5. AI dla klastrów nowych/zmienionych, do limitu budżetu.
6. Zapis review queue + cache AI + nowy stan wejścia.

---

## 6. CLI Interface

- `synapsea run` pozostaje trybem jednorazowym.
- dodane `synapsea watch` do pracy ciągłej.
- budżet AI i parametry watchera dostępne jako opcje CLI.

---

## 7. Non-Functional Requirements

### Performance
- czas przebiegu ma zależeć głównie od wielkości delty, nie od całej historii,
- liczba wywołań AI ma być ograniczana budżetem per cykl,
- duże klastry nie mogą niekontrolowanie zwiększać payloadu.

### Reliability
- watcher musi kontynuować działanie mimo błędów pojedynczych eventów lub odpowiedzi AI,
- stan wejścia i cache AI muszą być odporne na ponowne uruchomienie.

### Privacy
- bez zmian: wszystkie operacje lokalnie.

---

## 8. Acceptance Criteria

1. Dwa kolejne `run` na tym samym zbiorze:
- drugi przebieg wykonuje istotnie mniej pracy (brak pełnego reprocessingu).

2. Przyrost 2-3 plików między uruchomieniami:
- pipeline przetwarza tylko nową deltę,
- liczba zapytań AI jest istotnie mniejsza niż w modelu pełnego przebiegu.

3. `watch`:
- reaguje na nowe pliki bez pełnego skanu startowego,
- nie kończy działania po błędzie pojedynczego zapytania do AI.

4. Regresja:
- komendy `review`, `apply`, `reject` zachowują zgodność z dotychczasowym kontraktem.
