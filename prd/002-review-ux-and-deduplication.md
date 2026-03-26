## 1. Overview

Celem przyrostu jest poprawa użyteczności kolejki review oraz redukcja duplikatów propozycji,
które utrudniają podejmowanie decyzji przez użytkownika.

Aktualne problemy:
- komenda `review` pokazuje zbyt mało kontekstu do decyzji,
- deduplikacja działa głównie po `cluster_id`, co nie eliminuje semantycznie podobnych propozycji,
- kolejka review może zawierać wiele wariantów tej samej kategorii.

---

## 2. Vision

> Review ma być szybkim, czytelnym i stabilnym etapem akceptacji decyzji AI, bez zalewania użytkownika duplikatami.

---

## 3. Core Principles

1. Użytkownik widzi kontekst decyzji bez ręcznego czytania JSON.
2. Deduplikacja opiera się na znaczeniu propozycji, nie wyłącznie na identyfikatorze klastra.
3. Kontrakt `apply/reject` pozostaje kompatybilny.
4. Kolejka review promuje propozycje najbardziej użyteczne.

---

## 4. Key Features

### 4.1 Rozszerzony widok `review`

- dodatkowe kolumny kontekstowe (np. `target_path`, liczba kandydatów, skrócone uzasadnienie),
- opcjonalny tryb szczegółowy dla pełniejszego podglądu.

### 4.2 Semantyczna deduplikacja

- normalizacja nazw kategorii i stabilny klucz deduplikacyjny,
- wykrywanie propozycji równoważnych semantycznie,
- aktualizacja istniejącej pozycji zamiast dopisywania duplikatu.

### 4.3 Higiena i ranking kolejki

- porządkowanie kolejki według jakości i przydatności propozycji,
- ograniczenie widocznego szumu w przypadku wielu podobnych klastrów.

---

## 5. Acceptance Criteria

1. `review` pokazuje kontekst wystarczający do decyzji bez ręcznego otwierania `review_queue.json`.
2. Dla danych z wieloma podobnymi klastrami (np. Qt/Info.plist) liczba powtarzalnych propozycji jest istotnie niższa.
3. `apply` i `reject` zachowują dotychczasowe zachowanie.
4. Wszystkie testy regresyjne przechodzą lokalnie.
