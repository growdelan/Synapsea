## 1. Overview

Celem tego przyrostu jest domknięcie pętli decyzyjnej review przez dodanie wykonawczej fazy `apply`,
która faktycznie przenosi pliki do zatwierdzonej kategorii, oraz udostępnienie jawnej kontroli modelu Ollama
z poziomu CLI.

Aktualne problemy:
- `apply` aktualizuje status review i taksonomię, ale nie wykonuje realnych przeniesień plików,
- użytkownik nie może wybrać modelu Ollama per uruchomienie `run`/`watch`,
- brak jawnej polityki kolizji nazw przy wykonawczych przeniesieniach.

---

## 2. Vision

> Synapsea ma nie tylko proponować strukturę, ale po świadomej decyzji użytkownika wykonywać bezpieczne,
audytowalne przeniesienia plików z pełną kontrolą konfiguracji modelu AI.

---

## 3. Core Principles

1. Human-in-the-loop pozostaje nienaruszony: przeniesienia tylko po ręcznym `apply`.
2. Bezpieczeństwo danych ponad agresywne wykonanie: brak nadpisywania przy kolizjach.
3. Jawna i lokalna konfiguracja warstwy AI przez CLI.
4. Audytowalność wyniku `apply` i jego skutków na system plików.
5. Kompatybilność istniejących przepływów `review/reject/run/watch`.

---

## 4. Key Features

### 4.1 Wykonawcze `apply` z faktycznym przenoszeniem

- po zatwierdzeniu pozycji review system przenosi `candidate_files` do `<source_dir>/<target_path>`,
- katalog docelowy jest przygotowywany automatycznie, jeżeli nie istnieje,
- wynik operacji zawiera podsumowanie: liczba plików przeniesionych, pominiętych i błędnych.

### 4.2 Polityka kolizji: skip + raport

- jeżeli w ścieżce docelowej istnieje już plik o tej samej nazwie, plik źródłowy nie jest nadpisywany,
- kolizja jest raportowana w wyniku `apply` jako przypadek pominięty,
- proces kontynuuje obsługę pozostałych plików zamiast przerywania całej operacji.

### 4.3 Sterowanie modelem Ollama przez CLI

- `synapsea run` przyjmuje argument `--ollama-model <model_name>`,
- `synapsea watch` przyjmuje argument `--ollama-model <model_name>`,
- przekazany model nadpisuje wartość domyślną dla bieżącego uruchomienia.

---

## 5. System Architecture

### 5.1 New/extended components

- `apply_executor` (nowa odpowiedzialność w warstwie aplikacyjnej):
  - realizacja fizycznych operacji przenoszenia po zatwierdzeniu review,
  - raportowanie wyników wykonania per plik i sumarycznie.
- rozszerzenie konfiguracji CLI:
  - przekazywanie wybranego modelu Ollama do konfiguracji runtime.

### 5.2 Updated data flow

1. Użytkownik uruchamia `apply <id>`.
2. System aktualizuje status pozycji review i taksonomię jak dotychczas.
3. System wyznacza docelową ścieżkę kategorii w monitorowanym drzewie źródłowym.
4. System przenosi pliki kandydujące zgodnie z polityką kolizji `skip + raport`.
5. System zapisuje/eksponuje podsumowanie wyniku wykonania.

---

## 6. CLI Interface

Nowe/rozszerzone interfejsy:

```bash
synapsea run --ollama-model gemma3:4b-it-qat
synapsea watch --ollama-model llama3.1:8b
synapsea apply rev_001
```

Semantyka:
- `apply` wykonuje przeniesienia dopiero po akceptacji propozycji,
- `reject` nie wykonuje operacji na plikach,
- `run/watch` bez `--ollama-model` zachowują model domyślny.

---

## 7. Non-Functional Requirements

### Reliability
- przeniesienia muszą być odporne na częściowe błędy I/O i raportować stan końcowy,
- kolizje nazw nie mogą prowadzić do utraty danych.

### Auditability
- wynik `apply` musi dać się odtworzyć w logice decyzji i skutków wykonania,
- zachowany zostaje model audytowalnych decyzji review.

### Privacy
- bez zmian: wszystkie operacje lokalnie.

---

## 8. Acceptance Criteria

1. `apply` przenosi pliki z `candidate_files` do docelowej ścieżki kategorii.
2. Przy kolizji nazwy plik nie jest nadpisywany i jest oznaczany jako pominięty.
3. `apply` zwraca/drukuje podsumowanie: przeniesione, pominięte, błędne.
4. `run --ollama-model` i `watch --ollama-model` przekazują wybrany model do warstwy Ollama.
5. `review`, `reject`, `run`, `watch` pozostają kompatybilne z dotychczasowym kontraktem poza nowymi rozszerzeniami.
6. Testy regresyjne dla CLI i przepływu review przechodzą lokalnie.
