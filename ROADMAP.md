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

---

## Milestone 7: Inkrementalny silnik przetwarzania (done)

Cel:
- ograniczyć koszt przebiegu do realnej delty zmian w folderze źródłowym
- zredukować ryzyko regresji wydajności przy rosnącej historii danych

Definition of Done:
- system utrzymuje trwały stan wejścia i wylicza deltę `created/modified/deleted`
- klasyfikacja i aktualizacja historii decyzji działają dla delty bez pełnego reprocessingu
- klastrowanie przelicza tylko obszary dotknięte zmianą
- dwa kolejne uruchomienia `run` bez zmian wejścia nie wykonują pełnej pracy jak przy pierwszym przebiegu

Zakres:
- dodanie repozytorium stanu wejścia i mechanizmu wyliczania delty
- aktualizacja pipeline do przetwarzania inkrementalnego
- dostosowanie zapisu i usuwania rekordów historii klasyfikacji dla plików usuniętych
- testy jednostkowe i integracyjne dla scenariuszy create/modify/delete

Uwagi:
- milestone redukcji ryzyka dla dużego przyrostu wydajnościowego (PRD 001)

---

## Milestone 8: Optymalizacja warstwy AI (done)

Cel:
- zredukować koszt interpretacji AI przy zachowaniu jakości i audytowalności propozycji
- ograniczyć liczbę i rozmiar zapytań do lokalnego modelu

Definition of Done:
- payload dla interpretacji klastra jest skrócony i nie zawiera pełnej listy `candidate_files`
- działa cache propozycji AI po fingerprint klastra
- istnieje budżet liczby wywołań AI per cykl i mechanizm odraczania nadmiarowych klastrów
- liczba realnych wywołań AI dla niezmienionych danych jest istotnie niższa niż bez cache

Zakres:
- redukcja kontraktu wejściowego do warstwy Ollama
- dodanie trwałego magazynu cache odpowiedzi AI
- dodanie konfiguracji budżetu AI i obsługi odroczeń
- testy dla fingerprint, cache hit/miss i limitu wywołań

---

## Milestone 9: Tryb ciągły watch i stabilizacja operacyjna (done)

Cel:
- dostarczyć ciągły tryb pracy oparty na eventach systemowych bez pełnego skanu na starcie
- zapewnić odporność działania watchera na błędy runtime i odpowiedzi AI

Definition of Done:
- dostępna jest komenda CLI `watch` dla ciągłego monitorowania
- watcher startuje bez bootstrap pełnego skanu i reaguje na nowe eventy
- mikro-przebiegi uruchamiane przez eventy korzystają z inkrementalnego pipeline
- błąd pojedynczego eventu lub pojedynczego zapytania AI nie zatrzymuje całego procesu watchera

Zakres:
- implementacja pętli watchera i integracja z CLI
- obsługa zdarzeń utworzenia, modyfikacji i usunięcia
- logika odporności (retry/backoff lub bezpieczne pomijanie błędnych eventów)
- testy integracyjne trybu watch

---

## Milestone 10: Rozszerzony widok review CLI (done)

Cel:
- zwiększyć czytelność i użyteczność komendy `review` bez zmiany semantyki `apply/reject`
- umożliwić podejmowanie decyzji bez ręcznej analizy pliku `review_queue.json`

Definition of Done:
- `review` pokazuje rozszerzone kolumny kontekstowe (w tym `target_path`, skrócone uzasadnienie, liczba kandydatów)
- dostępny jest tryb szczegółowy `review --verbose`
- istnieją testy formattera wyjścia `review` dla trybu podstawowego i szczegółowego
- komendy `apply` i `reject` działają bez regresji

Zakres:
- rozszerzenie parsera CLI dla opcji `review --verbose`
- aktualizacja renderowania listy review w `cli.py`
- aktualizacja testów CLI review

---

## Milestone 11: Semantyczna deduplikacja propozycji review (done)

Cel:
- wyeliminować powtarzalne propozycje tej samej kategorii pochodzące z różnych klastrów
- ustabilizować zachowanie deduplikacji niezależnie od reindexu `cluster_id`

Definition of Done:
- repozytorium review deduplikuje wpisy po stabilnym kluczu semantycznym
- normalizacja nazwy propozycji eliminuje duplikaty różniące się jedynie formatowaniem
- zachowana jest kompatybilność istniejącego formatu `review_queue.json`
- testy jednostkowe pokrywają scenariusze duplikatów Qt/Info.plist i wariantów nazewnictwa

Zakres:
- implementacja normalizacji klucza deduplikacyjnego
- modyfikacja `add_item` w repozytorium review
- testy deduplikacji semantycznej

Uwagi:
- milestone redukuje ryzyko nadmiaru pozycji review i szumu decyzyjnego

---

## Milestone 12: Ranking i higiena kolejki review (done)

Cel:
- uporządkować kolejkę review i promować najbardziej użyteczne propozycje
- ograniczyć percepcję „zalania” podobnymi wpisami przy dużej liczbie klastrów

Definition of Done:
- elementy review są prezentowane w stabilnej kolejności preferującej wyższy confidence i bogatszy kontekst
- system ogranicza widoczny szum poprzez scalanie lub obniżanie priorytetu wpisów podobnych
- istnieją testy integracyjne jakości kolejki po wielu podobnych klastrach
- pełny zestaw testów regresyjnych przechodzi

Zakres:
- wprowadzenie prostego rankingu elementów review
- uporządkowanie kolejności zapisu/odczytu queue
- testy integracyjne dla jakości listy review

---

## Milestone 13: Wykonawcze apply i bezpieczne przenoszenie plików (done)

Cel:
- domknąć przepływ review o realne wykonanie operacji na plikach po zatwierdzeniu propozycji
- zapewnić bezpieczne przenoszenie bez nadpisywania danych przy kolizjach nazw

Definition of Done:
- `apply` po akceptacji propozycji wykonuje przeniesienie plików `candidate_files` do `target_path` w drzewie źródłowym
- wynik `apply` raportuje co najmniej liczbę plików przeniesionych, pominiętych i błędnych
- kolizje nazw nie nadpisują plików docelowych i są raportowane jako pominięte
- testy obejmują scenariusze sukcesu, kolizji i częściowych błędów I/O

Zakres:
- dodanie warstwy wykonawczej przenoszeń uruchamianej przez komendę `apply`
- przygotowanie katalogów docelowych kategorii przed przeniesieniem
- implementacja polityki kolizji `skip + raport`
- testy jednostkowe/integracyjne dla wykonawczego `apply`

---

## Milestone 14: Konfigurowalny model Ollama w CLI run/watch (done)

Cel:
- umożliwić wybór modelu Ollama per uruchomienie bez zmiany kodu i bez utraty kompatybilności CLI
- utrzymać dotychczasowe zachowanie domyślne przy braku nowego argumentu

Definition of Done:
- komendy `run` i `watch` przyjmują argument `--ollama-model`
- wskazany model jest przekazywany do warstwy Ollama dla bieżącego przebiegu
- brak podanego argumentu zachowuje domyślny model projektu
- testy regresyjne CLI i pipeline przechodzą dla wariantu domyślnego i jawnie wskazanego modelu

Zakres:
- rozszerzenie parsera CLI dla `run` i `watch` o opcję `--ollama-model`
- rozszerzenie konfiguracji runtime i przekazania modelu do klienta Ollama
- aktualizacja dokumentacji uruchomienia oraz testów CLI/pipeline

---

## Milestone 15: Redukcja ryzyka PRD 004 i kontrakty kompatybilności (done)

Cel:
- zredukować ryzyko wdrożenia personalizacji przez doprecyzowanie kontraktów danych preferencji
- potwierdzić kompatybilność wsteczną formatów review przy nowych polach explainability

Definition of Done:
- istnieje opisany i przetestowany kontrakt lokalnego magazynu `user_preferences.json`
- odczyt starszych wpisów review bez pól preferencji działa bez wyjątków
- zdefiniowano i przetestowano konserwatywną zasadę wpływu pojedynczego sygnału na score
- testy kontraktowe i regresyjne dla warstwy modeli/review przechodzą

Zakres:
- doprecyzowanie kontraktów modeli preferencji i rozszerzeń `ReviewItem`
- testy kompatybilności wstecz dla `review_queue.json`
- testy walidujące zachowanie scoringu dla pojedynczego i powtarzalnego sygnału

---

## Milestone 16: Repozytorium preferencji użytkownika (done)

Cel:
- dostarczyć trwały, lokalny magazyn preferencji użytkownika zgodny z PRD 004
- zapewnić prosty i audytowalny mechanizm aktualizacji liczników i score

Definition of Done:
- istnieje komponent repozytorium preferencji oparty o `data/user_preferences.json`
- wspierane są statystyki co najmniej dla tokenów, heurystyk, wzorców i par propozycji
- zapis i odczyt danych jest deterministyczny i odporny na brak pliku początkowego
- testy jednostkowe repozytorium i modelu preferencji przechodzą

Zakres:
- implementacja persystencji preferencji użytkownika
- implementacja modelu statystyk preferencji i wyliczania score
- testy read/write i aktualizacji liczników accept/reject

---

## Milestone 17: Uczenie preferencji na apply/reject (done)

Cel:
- zintegrować uczenie preferencji z decyzjami użytkownika w komendach `apply` i `reject`
- utrzymać konserwatywny charakter uczenia dla sygnałów odrzucenia

Definition of Done:
- `apply` aktualizuje pozytywne sygnały preferencji na podstawie pary propozycji oraz dostępnych cech
- `reject` aktualizuje co najmniej negatywny sygnał dla pary propozycji
- brakujące pliki kandydatów nie zatrzymują procesu uczenia
- testy pokrywają scenariusze `apply`, `reject` i częściowo brakujących `candidate_files`

Zakres:
- integracja repozytorium preferencji z pipeline po decyzjach review
- ekstrakcja evidence z review item i historii klasyfikacji
- testy integracyjne aktualizacji preferencji po decyzjach użytkownika

---

## Milestone 18: Scoring preferencji i explainability review (done)

Cel:
- użyć wyuczonych preferencji do korekty confidence przyszłych propozycji review
- zapewnić audytowalny breakdown wpływu preferencji na wynik

Definition of Done:
- podczas tworzenia review item wyliczany jest `final_confidence` oparty o base confidence i korekty preferencji
- ranking review używa finalnego confidence przy zachowaniu dotychczasowej logiki statusów
- review item zawiera kompatybilne wstecz pola explainability (`base`, `delta`, `final`, `reasons`)
- testy potwierdzają boost dla powtarzalnych akceptacji i karę dla powtarzalnych odrzuceń

Zakres:
- integracja scorer preferencji z etapem generowania review queue
- rozszerzenie modelu review item i repozytorium queue o pola explainability
- testy rankingowe i kontraktowe dla nowych pól

---

## Milestone 19: CLI preferences i wgląd w confidence breakdown (done)

Cel:
- udostępnić użytkownikowi czytelną komendę inspekcji wyuczonych preferencji
- rozszerzyć widok `review --verbose` o strukturę confidence breakdown

Definition of Done:
- dostępna jest komenda `preferences` z opcjami `--limit` i `--verbose`
- output pokazuje top pozytywne/negatywne pary propozycji oraz mapowania token/heurystyka
- `review --verbose` pokazuje base/delta/final confidence i powody korekty, gdy dane są dostępne
- testy CLI dla `preferences` i rozszerzonego verbose review przechodzą

Zakres:
- rozszerzenie parsera CLI i warstwy prezentacji
- formatowanie podsumowania preferencji z repozytorium
- testy formattera i parsera nowych opcji

---

## Milestone 20: Stabilizacja end-to-end PRD 004 (done)

Cel:
- domknąć jakość i spójność funkcji uczenia preferencji w pełnym przepływie produktu
- potwierdzić brak regresji dla istniejącego workflow i danych

Definition of Done:
- działa pełny przepływ: decyzja review -> aktualizacja preferencji -> korekta kolejnych propozycji
- pełny zestaw testów regresyjnych przechodzi
- dokumentacja operacyjna i status projektu są zaktualizowane do finalnego stanu PRD 004
- brak otwartych problemów krytycznych po self-review i ewentualnych poprawkach

Zakres:
- testy integracyjne end-to-end dla PRD 004
- końcowa walidacja kompatybilności i wydajnościowej lekkości rozwiązania
- finalizacja dokumentacji i domknięcie operacyjne zmiany

---

## Milestone 21: Kontrakt CLI dla batch apply/reject (done)

Cel:
- dodać ergonomiczny kontrakt CLI dla obsługi wielu ID w `apply` i `reject`
- zachować pełną kompatybilność scenariusza pojedynczego ID

Definition of Done:
- parser CLI przyjmuje wiele ID pozycyjnie dla `apply` i `reject`
- wynik komendy zwraca raport `requested/succeeded/failed` dla batcha
- polityka kodów wyjścia jest spójna: `0` bez błędów, `1` przy co najmniej jednym błędzie
- istnieją testy parsera i kontraktu wyjścia CLI dla pojedynczego i wieloelementowego wywołania

Zakres:
- rozszerzenie parsera CLI (`nargs='+'`) dla `apply` i `reject`
- dostosowanie warstwy CLI do raportowania zbiorczego i kodów zakończenia
- testy kontraktu wejścia/wyjścia dla komend batch

---

## Milestone 22: Sekwencyjne wykonanie batch i walidacja regresji (planned)

Cel:
- zapewnić stabilne, sekwencyjne wykonanie wielu `apply/reject` w warstwie aplikacji
- domknąć jakość przez testy częściowych błędów i regresję istniejącego workflow

Definition of Done:
- batch `apply/reject` przetwarza wszystkie ID w kolejności wejścia, bez przerywania na pierwszym błędzie
- `apply` agreguje raport `moved/skipped/errors` dla całego batcha
- częściowa porażka jest jawnie raportowana i nie blokuje sukcesów dla pozostałych ID
- pełny zestaw testów regresyjnych CLI/review przechodzi

Zakres:
- implementacja sekwencyjnego executor’a batch dla `apply/reject` w backendzie
- agregacja metryk wykonawczych `apply` oraz listy błędów per ID
- testy integracyjne dla sukcesu, częściowej porażki i kompatybilności pojedynczego ID
