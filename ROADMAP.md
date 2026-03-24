# Roadmapa (milestones)

## Statusy milestone’ów
Dozwolone statusy:
- planned
- in_progress
- done
- blocked

---

## Milestone 0.5: Minimal end-to-end slice (done)

Cel:
- uruchomić minimalny przepływ od wejścia CLI do zapisu wyniku na lokalnych danych testowych
- potwierdzić podstawowy kontrakt danych między skanowaniem, klasyfikacją i kolejką review
- przygotować repo do dalszej implementacji kolejnych komponentów MVP

Definition of Done:
- aplikację da się uruchomić jednym poleceniem (opisanym w README.md)
- istnieje co najmniej jeden smoke test przechodzący przez minimalny przepływ end-to-end
- testy przechodzą lokalnie
- brak placeholderów w kodzie dla zaimplementowanego przepływu
- minimalny przebieg kończy się zapisem przykładowej decyzji lub propozycji w lokalnym magazynie danych

Zakres:
- minimalny entrypoint CLI uruchamiający pojedynczy przebieg analizy
- podstawowy skan jednego folderu wejściowego
- minimalna klasyfikacja plików dla prostego przypadku
- zapis wyniku do kolejki review lub historii decyzji
- smoke test end-to-end na stubach lub danych testowych

---

## Milestone 1: Kontrakty danych i walidacja ryzyk MVP (done)

Cel:
- zredukować ryzyko błędnego kształtu danych wejściowych dla warstwy AI i review
- potwierdzić, że heurystyki klastrowania oraz integracja lokalna z Ollama są wykonalne w ramach MVP

Definition of Done:
- istnieje opisana i używana struktura danych dla klasyfikacji, `candidate_cluster`, kolejki review i taksonomii
- zdefiniowano co najmniej trzy typy wzorców wykrywanych heurystycznie
- zweryfikowano na reprezentatywnych danych, że lokalny przepływ z Ollama zwraca odpowiedź możliwą do zapisania w review
- zidentyfikowane ryzyka i ograniczenia są odzwierciedlone w dalszych milestone’ach

Zakres:
- doprecyzowanie kontraktów danych i stanów obiektów domenowych
- walidacja heurystyk grupowania po tokenach, rozszerzeniach i wzorcach nazw
- walidacja lokalnej komunikacji z Ollama oraz formatu odpowiedzi
- doprecyzowanie kryteriów confidence threshold i jakości propozycji

Uwagi:
- milestone redukujący ryzyko dla projektu o dużym zakresie

---

## Milestone 2: Klasyfikacja plików i historia decyzji (done)

Cel:
- dostarczyć stabilny lokalny przepływ skanowania folderu, ekstrakcji cech i klasyfikacji plików
- zapewnić trwały zapis historii decyzji klasyfikacyjnych

Definition of Done:
- system skanuje wskazany folder i analizuje pliki w trybie lokalnym
- dla każdego analizowanego pliku powstaje zestaw cech wymaganych przez PRD
- decyzje klasyfikacyjne są zapisywane w trwałym magazynie historii
- operacje są idempotentne dla ponownego uruchomienia na tym samym zbiorze danych

Zakres:
- skaner plików i obsługa wejścia z CLI
- ekstrakcja cech z nazw, rozszerzeń i prostych sygnałów heurystycznych
- przypisanie plików do istniejących kategorii roboczych
- zapis logu decyzji klasyfikacyjnych

Uwagi:
- bez generowania nowych kategorii przez AI

---

## Milestone 3: Detekcja wzorców i generowanie kandydatów klastrów (done)

Cel:
- zbudować warstwę heurystyczną przygotowującą dane dla interpretacji AI
- wykrywać wzorce prowadzące do propozycji nowych kategorii lub zmian w taksonomii

Definition of Done:
- system wykrywa co najmniej trzy typy wzorców wskazane w PRD
- powstają obiekty `candidate_cluster` zawierające komplet wymaganych pól
- klastrowanie działa bez użycia AI i produkuje wyniki nadające się do dalszej interpretacji
- wyniki można powiązać z historią klasyfikacji i przykładowymi plikami

Zakres:
- grupowanie po tokenach
- grupowanie po rozszerzeniach
- wykrywanie wzorców nazw, dat, wersji i numeracji
- scoring klastrów i przygotowanie kandydatów do interpretacji

Uwagi:
- milestone zamyka heurystyczną część pipeline’u

---

## Milestone 4: Interpretacja AI i kolejka review (done)

Cel:
- przekształcać kandydatów klastrów w audytowalne propozycje zmian struktury
- zachować pełną kontrolę użytkownika nad akceptacją decyzji

Definition of Done:
- kandydaci klastrów są przekazywani do lokalnego modelu przez Ollama
- system zapisuje propozycje do `review_queue.json` wraz z uzasadnieniem i confidence
- nie są wykonywane automatyczne zmiany struktury bez decyzji użytkownika
- kolejka review przechowuje status co najmniej `pending` oraz identyfikator propozycji

Zakres:
- integracja warstwy interpretacji AI z kandydatami klastrów
- mapowanie odpowiedzi modelu na propozycje domenowe
- zapis i odczyt kolejki review
- podstawowe reguły ograniczające over-clustering i złe nazewnictwo

Uwagi:
- milestone realizuje audytowalny human-in-the-loop

---

## Milestone 5: CLI review/apply/reject i taksonomia MVP (done)

Cel:
- udostępnić użytkownikowi pełny przepływ obsługi propozycji przez CLI
- utrwalać zaakceptowane decyzje w taksonomii projektu

Definition of Done:
- dostępne są komendy CLI do przeglądu, akceptacji i odrzucania propozycji
- zaakceptowanie propozycji aktualizuje taksonomię w lokalnym magazynie danych
- odrzucenie propozycji zmienia jej status bez skutków ubocznych dla danych źródłowych
- MVP spełnia definicję done z PRD w zakresie klasyfikacji, propozycji kategorii i obsługi przez CLI

Zakres:
- implementacja komend `review`, `apply` i `reject`
- aktualizacja `taxonomy.json` na podstawie zaakceptowanych propozycji
- obsługa statusów elementów kolejki review
- walidacja scenariuszy akceptacji i odrzucenia

Uwagi:
- milestone domyka deklarowany zakres MVP

---

## Milestone 6: Pasywne uczenie i ewolucja taksonomii (done)

Cel:
- rozszerzyć system o uczenie z zachowań użytkownika i rekomendacje ewolucji struktury
- przygotować bazę pod rozwój po MVP bez naruszania modelu audytowalności

Definition of Done:
- system rejestruje sygnały z ręcznych przeniesień, zmian nazw lub cofnięć decyzji
- powstają propozycje split, merge, nowych podkategorii lub wykrycia martwych kategorii
- nowe propozycje korzystają z istniejącej ścieżki review
- zakres future enhancements pozostaje poza tym milestone’em

Zakres:
- zbieranie sygnałów pasywnego uczenia
- analiza zmian użytkownika względem istniejącej taksonomii
- rekomendacje ewolucji kategorii
- integracja z kolejką review i historią decyzji

Uwagi:
- milestone wykracza poza minimalne MVP, ale wynika z głównej wizji produktu
