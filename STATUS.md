# Aktualny stan projektu

## Co działa
- Istnieje bazowy opis produktu w `prd/000-initial-prd.md`.
- Istnieje przyrostowy opis wydajności i trybu watch w `prd/001-incremental-performance-watcher.md`.
- Istnieje uzupełniona specyfikacja wysokopoziomowa w `spec.md`.
- Istnieje rozbita roadmapa milestone'ów w `ROADMAP.md`, zaczynająca się od `Milestone 0.5`.
- Działa minimalny entrypoint CLI `synapsea run` uruchamiany przez `uv`.
- Minimalny pipeline klasyfikuje pliki po rozszerzeniach i zapisuje decyzje do lokalnej bazy SQLite.
- Istnieje smoke test bez IO dyskowego dla podstawowego przepływu end-to-end.
- Istnieją kontrakty domenowe dla `candidate_cluster`, review queue, propozycji AI i taksonomii.
- Działa heurystyczne wykrywanie klastrów dla tokenów, rozszerzeń i wzorców nazw.
- Istnieje warstwa walidacji odpowiedzi z Ollama oraz zapis review i taksonomii w formacie zgodnym ze spec.
- Działa jawny skaner plików i ekstraktor cech zgodny z MVP: rozszerzenia, tokeny, słowa kluczowe, sygnały wzorców i klasy heurystyczne.
- Historia klasyfikacji jest utrwalana idempotentnie w SQLite wraz z zapisanymi cechami pliku.
- Pipeline materializuje kandydatów klastrów do `candidate_clusters.json` na podstawie zapisanej historii klasyfikacji.
- Kandydaci klastrów zawierają scoring, typ klastra i przykładowe pliki gotowe do dalszej interpretacji przez AI.
- Pipeline potrafi przekazać kandydatów klastrów do warstwy interpretacji AI i zapisać propozycje do `review_queue.json`.
- Review queue utrzymuje statusy propozycji i deduplikuje wpisy po `cluster_id`.
- Warstwa Ollama korzysta ze structured outputs z walidacją przez `pydantic` zamiast opierać się na swobodnym parsowaniu tekstu.
- Dostępne są komendy CLI `review`, `apply` i `reject`.
- Akceptacja propozycji aktualizuje `taxonomy.json`, a odrzucenie zmienia status bez skutków ubocznych dla danych źródłowych.
- Pipeline zapisuje sygnały pasywnego uczenia w `learning_signals.json` i snapshoty obserwowanego drzewa plików.
- Silnik ewolucji potrafi generować dodatkowe propozycje review dla podkategorii, merge oraz martwych kategorii.
- Potwierdzono lokalne uruchomienie pełnego przebiegu z modelem `gemma3:4b-it-qat`.
- Pipeline utrzymuje stan wejścia (`input_state.json`) i wylicza deltę zmian `created/modified/deleted`.
- `run` klasyfikuje tylko pliki z delty oraz usuwa rekordy historii dla plików usuniętych.
- Przy braku delty przebieg nie wykonuje pełnego przeliczania klastrów.
- Warstwa AI używa skróconego payloadu klastra, cache fingerprintów i budżetu wywołań na cykl.
- System utrzymuje kolejkę odroczonych klastrów do dalszej interpretacji AI.
- Dostępna jest komenda `watch` uruchamiająca tryb ciągłego monitoringu zmian.
- Watcher startuje bez bootstrapowego przetwarzania i uruchamia mikro-przebiegi tylko po wykryciu zmian.
- Błąd pojedynczego przebiegu watchera nie zatrzymuje procesu monitoringu.

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
- Zrealizowano `Milestone 2: Klasyfikacja plików i historia decyzji`.
- Pipeline zapisuje komplet podstawowych cech potrzebnych do dalszego klastrowania bez użycia AI.
- Zrealizowano `Milestone 3: Detekcja wzorców i generowanie kandydatów klastrów`.
- Wyniki klastrowania są zapisywane w trwałym formacie i wynikają bezpośrednio z historii klasyfikacji.
- Zrealizowano `Milestone 4: Interpretacja AI i kolejka review`.
- Dodano próg confidence dla propozycji review i podstawowy tryb `--skip-ai` do lokalnej walidacji bez aktywnego modelu.
- Zrealizowano `Milestone 5: CLI review/apply/reject i taksonomia MVP`.
- Podstawowy przepływ MVP od klasyfikacji po akceptację lub odrzucenie propozycji jest dostępny przez CLI.
- Zrealizowano `Milestone 6: Pasywne uczenie i ewolucja taksonomii`.
- Repo ma już pełną pętlę: klasyfikacja, klastrowanie, review, taksonomia oraz sygnały uczenia do dalszej ewolucji.
- Integracja z Ollama została utwardzona przez structured outputs, walidację schematu oraz wydłużony timeout dla wolniejszego modelu lokalnego.
- Zrealizowano `Milestone 7: Inkrementalny silnik przetwarzania`.
- Zrealizowano `Milestone 8: Optymalizacja warstwy AI`.
- Zrealizowano `Milestone 9: Tryb ciągły watch i stabilizacja operacyjna`.

## Co jest w trakcie
- Wszystkie milestone’y z bieżącej roadmapy oznaczone jako `planned` zostały zrealizowane.

## Co jest następne
- Wyznaczenie kolejnego zakresu po obecnej roadmapie.
- Pomiar jakości i skuteczności heurystyk na reprezentatywnych danych produkcyjnych.
- Dalsza redukcja duplikatów propozycji kategorii przy dużej liczbie podobnych klastrów.

## Blokery i ryzyka
- Zakres produktu jest szeroki, więc utrzymanie małych milestone'ów będzie krytyczne dla tempa prac.
- Jakość odpowiedzi z lokalnego modelu Ollama nadal wymaga walidacji na reprezentatywnych danych i lepszego ograniczania duplikatów propozycji.
- Skuteczność klasyfikacji i akceptowalność propozycji review trzeba będzie potwierdzić na ręcznie zweryfikowanej próbce plików.

## Ostatnie aktualizacje
- 2026-03-26: dodano `prd/001-incremental-performance-watcher.md` i rozszerzono `spec.md` oraz `ROADMAP.md` o milestone’y 7-9.
- 2026-03-26: zrealizowano `Milestone 7`, dodając inkrementalne przetwarzanie delty, usuwanie rekordów dla skasowanych plików i testy M7.
- 2026-03-26: zrealizowano `Milestone 8`, dodając skrócony payload AI, cache propozycji, budżet wywołań i odraczanie klastrów.
- 2026-03-26: zrealizowano `Milestone 9`, dodając komendę `watch`, monitoring zmian bez bootstrapu i testy odporności watchera.
- 2026-03-24: wygenerowano i uzupełniono `spec.md` oraz `ROADMAP.md` na podstawie `prd/000-initial-prd.md`.
- 2026-03-24: doprecyzowano założenia MVP dotyczące systemu operacyjnego, katalogu wejściowego, trybu działania procesu i kryteriów jakości.
- 2026-03-24: zrealizowano `Milestone 0.5`, dodając bootstrap aplikacji, podstawowy pipeline klasyfikacji, zapis decyzji oraz smoke test.
- 2026-03-24: zrealizowano `Milestone 1`, dodając kontrakty domenowe, heurystyki klastrów oraz walidację odpowiedzi z Ollama.
- 2026-03-24: zrealizowano `Milestone 2`, dodając pełniejszą ekstrakcję cech i idempotentny zapis historii klasyfikacji.
- 2026-03-24: zrealizowano `Milestone 3`, spinając historię klasyfikacji z generowaniem i zapisem kandydatów klastrów.
- 2026-03-24: zrealizowano `Milestone 4`, podłączając interpretację AI i trwały zapis propozycji do review queue.
- 2026-03-24: zrealizowano `Milestone 5`, udostępniając review/apply/reject przez CLI i aktualizację taksonomii.
- 2026-03-24: zrealizowano `Milestone 6`, dodając pasywne uczenie, snapshoty i propozycje ewolucji taksonomii.
- 2026-03-24: utwardzono integrację z Ollama przez structured outputs z `pydantic`, model `gemma3:4b-it-qat` i domyślny timeout `60s`.
