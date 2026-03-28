# PRD: Batchowe apply/reject dla kolejki review CLI

## Metadane
- **PRD ID:** 005-batch-apply-reject-cli
- **Projekt:** Synapsea
- **Status:** Draft / Ready for implementation
- **Data utworzenia:** 2026-03-28
- **Zależności:** istniejące MVP + PRD 001, 002, 003, 004
- **Typ zakresu:** przyrost funkcjonalny

---

## 1. Cel

Umożliwić wykonywanie masowych decyzji review przez CLI, tak aby użytkownik mógł w jednym wywołaniu zatwierdzić (`apply`) lub odrzucić (`reject`) wiele pozycji kolejki review.

Funkcja ma skrócić czas pracy na dużych kolejkach i zachować pełną zgodność z zasadą human-in-the-loop.

---

## 2. Problem

Aktualnie CLI obsługuje pojedyncze ID dla `apply` i `reject`, co wymusza wielokrotne uruchamianie komendy przy większej liczbie propozycji.

Skutki:
- wolniejsza operacyjna praca na review queue,
- większe ryzyko błędów ręcznych przy serii poleceń,
- słaba ergonomia względem istniejących scenariuszy batch.

---

## 3. Oczekiwany rezultat

Po wdrożeniu użytkownik może wykonać:

```bash
synapsea apply rev_001 rev_002 rev_003
synapsea reject rev_010 rev_011 rev_012
```

Wynik komendy powinien zwracać raport zbiorczy:
- dla obu komend: `requested`, `succeeded`, `failed`,
- dodatkowo dla `apply`: agregację `moved`, `skipped`, `errors`.

Komenda ma kontynuować przetwarzanie wszystkich ID mimo błędów pojedynczych pozycji.

---

## 4. Poza zakresem

Ta funkcja **nie** obejmuje:
- zmian w TUI batch actions,
- wykonywania równoległego (konkurencyjnego) operacji,
- zmiany formatu `review_queue.json`,
- automatycznej deduplikacji duplikatów ID na wejściu.

---

## 5. Zasady produktowe

1. **Backward compatibility**
   - pojedyncze ID musi nadal działać bez zmiany semantyki.

2. **Partial failure tolerance**
   - błąd pojedynczego ID nie może przerywać całego batcha.

3. **Audytowalność**
   - wynik musi jasno raportować sukcesy i błędy.

4. **Conservative execution**
   - dla `apply` pozostaje obecna polityka przenoszenia i kolizji (`skip + raport`).

---

## 6. User stories

### 6.1 Operacyjny batch
Jako użytkownik chcę zatwierdzić lub odrzucić wiele pozycji review jednym poleceniem, aby szybciej obsługiwać duże kolejki.

### 6.2 Częściowe błędy
Jako użytkownik chcę, aby pojedynczy błąd nie zatrzymywał całej operacji batch, żebym nie musiał restartować całego procesu.

### 6.3 Czytelny wynik
Jako użytkownik chcę dostać podsumowanie sukcesów i błędów po batchu, aby wiedzieć co wymaga ręcznej interwencji.

---

## 7. Zakres wysokopoziomowy

Funkcja obejmuje:
- rozszerzenie parsera CLI (`apply`/`reject`) o listę wielu ID,
- batchowe wykonanie sekwencyjne operacji na review item,
- raportowanie zbiorcze i kod zakończenia procesu.

---

## 8. Wymagania funkcjonalne

### 8.1 Kontrakt wejścia CLI

Komendy `apply` i `reject` przyjmują co najmniej jedno ID:

- `apply <id1> <id2> ...`
- `reject <id1> <id2> ...`

Pojedyncze ID pozostaje w pełni wspierane.

### 8.2 Polityka wykonania batch

- ID są wykonywane sekwencyjnie i w kolejności wejścia.
- Duplikaty ID nie są deduplikowane automatycznie.
- Błąd dla pojedynczego ID jest raportowany, ale nie zatrzymuje batcha.

### 8.3 Raport końcowy

Po zakończeniu komendy:
- `requested=<n> succeeded=<n> failed=<n>` dla obu komend,
- dodatkowo dla `apply`: `moved=<n> skipped=<n> errors=<n>`.

### 8.4 Kody wyjścia

- `0` gdy brak błędów dla wszystkich ID,
- `1` gdy wystąpił co najmniej jeden błąd.

---

## 9. Kryteria akceptacji

- parser CLI przyjmuje wiele ID dla `apply/reject`,
- batch `apply/reject` poprawnie aktualizuje statusy elementów,
- `apply` poprawnie agreguje `moved/skipped/errors`,
- częściowa porażka nie zatrzymuje batcha,
- kod wyjścia jest zgodny z polityką (`0`/`1`),
- brak regresji dla scenariusza pojedynczego ID.

---

## 10. Ryzyka

- ryzyko niejednoznacznych komunikatów przy częściowych błędach,
- ryzyko regresji dotychczasowych testów CLI dla pojedynczego ID,
- ryzyko rozjazdu raportu CLI i faktycznego stanu review queue.

---

## 11. Weryfikacja

Minimalny zestaw walidacji:
- test parsera dla 1 i wielu ID,
- test `apply` batch sukces,
- test `apply` batch częściowa porażka,
- test `reject` batch sukces,
- test `reject` batch częściowa porażka,
- test regresji dla istniejącego scenariusza pojedynczego ID.
