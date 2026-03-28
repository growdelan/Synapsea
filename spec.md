# Specyfikacja techniczna

## Cel
Krótki opis celu aplikacji:
- Rozwiązuje problem chaotycznej, ręcznie utrzymywanej struktury plików poprzez lokalne analizowanie plików, wykrywanie wzorców i proponowanie sensownej, rozwijającej się taksonomii danych.
- Jest skierowana do użytkownika pracującego lokalnie na własnych zbiorach plików, który chce porządkować dane bez stałego ręcznego kategoryzowania.
- Zakres obejmuje lokalną klasyfikację plików, ekstrakcję cech, wykrywanie wzorców, generowanie propozycji zmian w strukturze, obsługę review przez CLI oraz wykonawcze przenoszenie plików po zatwierdzeniu propozycji.
- Poza zakresem MVP są: GUI, pełna automatyzacja zmian bez zgody użytkownika, zaawansowane embeddings, integracje z zewnętrznymi usługami oraz przetwarzanie wieloźródłowe.
- Pierwsza wersja wspiera wyłącznie środowisko macOS.

---

## Zakres funkcjonalny (high-level)
Opis funkcjonalności na wysokim poziomie:
- Kluczowe use-case’i:
  - uruchomienie procesu analizy wskazanego folderu i automatyczna klasyfikacja plików,
  - przegląd propozycji nowych kategorii lub zmian w taksonomii przez kolejkę review,
  - zatwierdzanie lub odrzucanie propozycji przez CLI,
  - uczenie systemu na podstawie działań użytkownika takich jak ręczne przeniesienia, zmiany nazw i cofanie decyzji.
- Główne przepływy użytkownika:
  - użytkownik uruchamia proces analizy,
  - system skanuje pliki, wyciąga cechy i zapisuje decyzje klasyfikacyjne,
  - silnik wzorców buduje kandydatów na klastry,
  - warstwa AI interpretuje klastry i zapisuje propozycje do kolejki review,
  - użytkownik przegląda, akceptuje lub odrzuca propozycje przez CLI,
  - zatwierdzenie propozycji przez `apply` może uruchomić faktyczne przeniesienia plików kandydujących do docelowej ścieżki kategorii.
- Aplikacja **nie** wykonuje automatycznych zmian w strukturze plików bez decyzji użytkownika, z trwałym wyjątkiem dla etapu bootstrapowej segregacji plików luzem z root aktywnego katalogu źródłowego (domyślnie `~/Downloads`) opisanego w PRD 006.
- Aplikacja **nie** dostarcza interfejsu graficznego w MVP.
- Aplikacja **nie** wysyła danych poza lokalną maszynę.
- W MVP domyślnym katalogiem monitorowanym jest `~/Downloads`.
- MVP zakłada pojedynczy katalog wejściowy.
- W przyroście po MVP (PRD 001) `run` pozostaje trybem jednorazowym, a tryb ciągły jest realizowany osobną komendą `watch`.
- W kolejnym przyroście (PRD 002) warstwa review jest rozszerzana o czytelniejszy widok CLI oraz deduplikację semantyczną propozycji.
- W kolejnym przyroście (PRD 003) `apply` może wykonywać przeniesienia plików po akceptacji review, a komendy `run/watch` przyjmują argument wyboru modelu `--ollama-model`.
- W kolejnym przyroście (PRD 004) system uczy się preferencji użytkownika na podstawie decyzji `apply/reject` i używa ich do korekty rankingu propozycji review.
- W kolejnym przyroście (PRD 005) komendy `apply/reject` wspierają batchową obsługę wielu ID w jednym wywołaniu CLI wraz z raportem zbiorczym.
- W kolejnym przyroście (PRD 006) komendy `run/watch` rozpoczynają działanie od segregacji plików luzem z root aktywnego katalogu źródłowego (domyślnie `~/Downloads`) do standardowych katalogów, a dopiero potem uruchamiają klastrowanie i AI.

Bez wchodzenia w szczegóły implementacyjne.

---

## Architektura i przepływ danych
Opis architektury na poziomie koncepcyjnym.

1. Główne komponenty systemu
   - warstwa skanowania plików odpowiedzialna za wykrywanie i odczyt metadanych wejściowych,
   - warstwa ekstrakcji cech i klasyfikacji budująca opis pliku na potrzeby dalszej analizy,
   - silnik detekcji wzorców i klastrów działający bez AI,
   - warstwa interpretacji AI wykorzystująca lokalny model Ollama do oceny kandydatów na nowe kategorie,
   - warstwa review i zarządzania taksonomią odpowiedzialna za zapis propozycji i obsługę decyzji użytkownika,
   - interfejs CLI do uruchamiania procesu i obsługi review.
2. Przepływ danych między komponentami
   - przy starcie `run/watch` (PRD 006) system wykonuje bootstrapową segregację plików luzem z root aktywnego katalogu źródłowego do katalogów standardowych przed dalszą analizą,
   - pliki z folderu wejściowego trafiają do skanera,
   - skaner przekazuje dane do ekstrakcji cech i klasyfikacji,
   - wyniki klasyfikacji są logowane i przekazywane do silnika wzorców,
   - kandydaci na klastry są oceniani przez warstwę AI,
   - propozycje kategorii lub zmian trafiają do kolejki review,
   - decyzje użytkownika aktualizują stan review, historię decyzji i taksonomię.
   - przy `apply` (PRD 003) akceptacja może dodatkowo uruchomić wykonawcze przeniesienia plików `candidate_files` do ścieżki `target_path`.
   - w przyroście inkrementalnym po MVP (PRD 001) system dodatkowo utrzymuje stan wejścia, wylicza deltę zmian i ogranicza przetwarzanie do plików oraz klastrów dotkniętych zmianą.
   - w przyroście PRD 002 system dodatkowo normalizuje propozycje review i ogranicza duplikaty semantyczne, zachowując zgodność komend `apply/reject`.
   - w przyroście PRD 005 komendy `apply/reject` mogą przetwarzać sekwencyjnie wiele pozycji review i zwracać raport agregowany sukcesów/błędów.
   - w przyroście PRD 006 etap bootstrapowej segregacji działa tylko dla plików bezpośrednio w aktywnym katalogu źródłowym (bez rekurencyjnego przemieszczania podkatalogów), używa fallbacku `Inne` i polityki kolizji `skip + raport`.
3. Granice odpowiedzialności
   - komponenty heurystyczne odpowiadają za wykrywanie wzorców i przygotowanie danych wejściowych dla AI,
   - komponent AI odpowiada wyłącznie za interpretację kandydatów i rekomendacje,
   - komponent review decyduje o trwałym zapisaniu propozycji i chroni przed nieautoryzowanymi zmianami struktury,
   - warstwa CLI nie implementuje logiki analitycznej, a jedynie udostępnia operacje użytkownika.

---

## Komponenty techniczne
Lista kluczowych komponentów technicznych i ich odpowiedzialności.
- `scanner`:
  - skanowanie folderu lub folderów wejściowych i przygotowanie listy plików do analizy.
- `feature_extractor`:
  - ekstrakcja rozszerzeń, tokenów, słów kluczowych i sygnałów wzorców z plików.
- `classifier`:
  - przypisywanie plików do istniejących kategorii roboczych oraz zapis decyzji klasyfikacyjnych.
- `cluster_engine`:
  - grupowanie plików według heurystyk i przygotowanie struktury `candidate_cluster`.
- `ollama_client`:
  - komunikacja z lokalnym modelem i odbiór odpowiedzi o zasadności tworzenia kategorii.
- `taxonomy_engine`:
  - utrzymywanie bieżącej taksonomii oraz przygotowanie propozycji split, merge i nowych podkategorii.
- `review_queue`:
  - zapisywanie propozycji do kolejki review oraz śledzenie ich statusów.
- `evolution_engine`:
  - analiza historii i sygnałów użytkownika w celu pasywnego uczenia oraz ewolucji struktury.
- magazyn danych:
  - trwałe przechowywanie taksonomii, kolejki review i historii decyzji.
- CLI:
  - uruchamianie procesu, przegląd sugestii oraz akceptacja lub odrzucanie decyzji.
- `batch_review_executor` (dotyczy PRD: 005-batch-apply-reject-cli.md):
  - sekwencyjne wykonanie wielu `apply/reject` z agregacją raportu (`requested/succeeded/failed` oraz dla `apply` także `moved/skipped/errors`).
  - kontynuacja batcha mimo błędów pojedynczych ID.
- `apply_executor` (dotyczy PRD: 003-apply-file-moves-and-ollama-model-cli.md):
  - wykonawcza warstwa przenoszenia plików po zatwierdzeniu review item przez `apply`.
  - obsługa polityki kolizji `skip + raport` bez nadpisywania istniejących plików.
- monitor procesu:
  - po MVP uruchamiany ręcznie przez komendę `watch`, działający ciągle i oczekujący na zdarzenia w folderze źródłowym.
- `input_state_repository` (dotyczy PRD: 001-incremental-performance-watcher.md):
  - utrzymywanie trwałego stanu wejścia (inode, mtime, size) do wyliczania delty zmian.
- `delta_engine` (dotyczy PRD: 001-incremental-performance-watcher.md):
  - wykrywanie zmian `created`, `modified` i `deleted` pomiędzy przebiegami.
- `ai_proposal_cache` (dotyczy PRD: 001-incremental-performance-watcher.md):
  - cache odpowiedzi AI po fingerprint klastrów, aby unikać powtarzania identycznych zapytań.
- `review_ranker` (dotyczy PRD: 002-review-ux-and-deduplication.md):
  - ranking i porządkowanie pozycji review według jakości sygnału i użyteczności dla użytkownika.
- `review_normalizer` (dotyczy PRD: 002-review-ux-and-deduplication.md):
  - normalizacja nazw i kluczy deduplikacyjnych dla semantycznie równoważnych propozycji.
- `user_preferences_repository` (dotyczy PRD: 004-user-preference-learning-pl.md):
  - trwałe utrzymywanie lokalnych preferencji użytkownika i statystyk akceptacji/odrzuceń w `user_preferences.json`.
- `preference_scorer` (dotyczy PRD: 004-user-preference-learning-pl.md):
  - wyliczanie korekty `confidence` na podstawie preferencji oraz budowanie strukturalnego explainability dla review item.
- `bootstrap_downloads_segregator` (dotyczy PRD: 006-auto-downloads-bootstrap-segregation.md):
  - segregacja plików luzem z root aktywnego katalogu źródłowego do katalogów `Dokumenty`, `Zdjęcia`, `Filmy`, `Audio`, `Instalatory`, `Archiwa`, `Inne` przed klastrowaniem i AI.
  - raportowanie wyniku etapu (`requested/moved/skipped/errors`) oraz obsługa kolizji polityką `skip + raport`.

---

## Decyzje techniczne
Jawne decyzje techniczne wraz z uzasadnieniem.

Każda decyzja powinna zawierać:
- Decyzja:
- Uzasadnienie:
- Konsekwencje:

- Decyzja:
  - Warstwa interpretacji AI korzysta z lokalnego modelu uruchamianego przez Ollama.
  Uzasadnienie:
  - PRD wymaga lokalności i prywatności oraz wskazuje Ollama jako mechanizm przetwarzania AI.
  Konsekwencje:
  - System wymaga lokalnie dostępnego środowiska Ollama i musi być projektowany z myślą o pracy offline.

- Decyzja:
  - Propozycje zmian w strukturze są zapisywane do pliku kolejki review zamiast być stosowane automatycznie.
  Uzasadnienie:
  - PRD wymaga pełnej audytowalności decyzji i modelu human-in-the-loop.
  Konsekwencje:
  - Proces biznesowy obejmuje dodatkowy krok akceptacji użytkownika, ale ogranicza ryzyko błędnych zmian.

- Decyzja:
  - Wykrywanie wzorców i budowa klastrów przed warstwą AI opiera się na heurystykach, nie na AI.
  Uzasadnienie:
  - PRD rozdziela detekcję wzorców od interpretacji modelu i wskazuje heurystyczne grupowanie jako osobną odpowiedzialność.
  Konsekwencje:
  - Należy utrzymać czytelny kontrakt danych pomiędzy warstwą heurystyczną a warstwą AI.

- Decyzja:
  - Projekt jest pakowany z użyciem `hatchling` jako minimalnego backendu build-systemu.
  Uzasadnienie:
  - Repo wymaga uruchamiania przez `uv run python -m synapsea`, więc potrzebny jest prosty backend umożliwiający instalację pakietu z układem `src/`.
  Konsekwencje:
  - Konfiguracja projektu pozostaje lekka, ale backend build-systemu staje się jawną zależnością narzędziową repo.

- Decyzja:
  - Structured outputs dla warstwy Ollama są walidowane przez `pydantic`, a schema JSON jest przekazywana bezpośrednio do pola `format`.
  Uzasadnienie:
  - Propozycje review queue muszą mieć stabilny kontrakt danych, a sama odpowiedź modelu nie powinna zależeć od swobodnego formatowania tekstu.
  Konsekwencje:
  - Repo dodaje zależność `pydantic`, ale integracja AI jest bardziej deterministyczna i odporniejsza na błędy parsowania.

- Decyzja:
  - Inkrementalny tryb po MVP przetwarza tylko deltę zmian plików oraz ogranicza AI do nowych lub zmienionych klastrów (dotyczy PRD: 001-incremental-performance-watcher.md).
  Uzasadnienie:
  - Problem wydajności wynika z pełnego reprocessingu i rosnącej liczby wywołań AI wraz ze wzrostem historii danych.
  Konsekwencje:
  - Wymagane jest trwałe utrzymywanie stanu wejścia oraz mechanizm wyliczania delty przed etapem klasyfikacji i klastrowania.

- Decyzja:
  - `run` pozostaje komendą one-shot, a tryb ciągły jest realizowany przez osobną komendę `watch` (dotyczy PRD: 001-incremental-performance-watcher.md).
  Uzasadnienie:
  - Zachowanie kompatybilności obecnych scenariuszy CLI i czytelne rozdzielenie trybu wsadowego od ciągłego.
  Konsekwencje:
  - Interfejs CLI rozszerza się o nową komendę oraz parametry watchera, ale bez zmiany semantyki istniejących komend review/apply/reject.

- Decyzja:
  - Warstwa AI używa cache po fingerprint klastra oraz budżetu wywołań per cykl (dotyczy PRD: 001-incremental-performance-watcher.md).
  Uzasadnienie:
  - Należy ograniczyć koszt lokalnego modelu przy zachowaniu audytowalności i jakości propozycji.
  Konsekwencje:
  - System musi utrzymywać dodatkowy magazyn cache i kolejkę odroczeń dla klastrów przekraczających budżet.

- Decyzja:
  - Deduplikacja review po PRD 002 opiera się na stabilnym kluczu semantycznym (parent category + znormalizowana propozycja kategorii), a nie wyłącznie na `cluster_id` (dotyczy PRD: 002-review-ux-and-deduplication.md).
  Uzasadnienie:
  - Ten sam lub bardzo podobny pomysł kategorii może pochodzić z wielu klastrów i reindexowanych identyfikatorów.
  Konsekwencje:
  - Repozytorium review musi utrzymywać dodatkową logikę normalizacji i zastępowania wpisów o równoważnym znaczeniu.

- Decyzja:
  - Komenda `review` po PRD 002 pokazuje rozszerzony kontekst propozycji i może mieć tryb szczegółowy, przy zachowaniu zgodności `apply/reject` (dotyczy PRD: 002-review-ux-and-deduplication.md).
  Uzasadnienie:
  - Użytkownik musi móc podjąć decyzję bez ręcznego analizowania surowego JSON kolejki.
  Konsekwencje:
  - Interfejs CLI review rozszerza format wyjścia i wymaga testów regresyjnych formattera.

- Decyzja:
  - Komenda `apply` po PRD 003 wykonuje faktyczne przeniesienia plików `candidate_files` do docelowej ścieżki kategorii, ale tylko po ręcznej akceptacji review (dotyczy PRD: 003-apply-file-moves-and-ollama-model-cli.md).
  Uzasadnienie:
  - Należy domknąć przepływ od propozycji do wykonania operacji na plikach bez łamania zasady human-in-the-loop.
  Konsekwencje:
  - `apply` staje się operacją wykonawczą na systemie plików i wymaga raportowania wyniku przeniesień.

- Decyzja:
  - Warstwa CLI udostępnia wybór modelu lokalnego przez argument `--ollama-model` dla komend `run` i `watch` (dotyczy PRD: 003-apply-file-moves-and-ollama-model-cli.md).
  Uzasadnienie:
  - Użytkownik potrzebuje sterowania modelem per uruchomienie bez zmiany kodu i bez utraty domyślnej konfiguracji.
  Konsekwencje:
  - Konfiguracja runtime przekazuje nazwę modelu do klienta Ollama, a testy CLI obejmują nowy argument.

- Decyzja:
  - Polityka kolizji podczas przenoszeń `apply` to `skip + raport` (brak nadpisywania plików docelowych) (dotyczy PRD: 003-apply-file-moves-and-ollama-model-cli.md).
  Uzasadnienie:
  - Priorytetem jest bezpieczeństwo danych i brak utraty istniejących plików.
  Konsekwencje:
  - Wynik `apply` musi raportować liczbę kolizji i pominiętych plików.

- Decyzja:
  - Preferencje użytkownika są utrzymywane lokalnie w czytelnym pliku `data/user_preferences.json`, bez zewnętrznej bazy danych (dotyczy PRD: 004-user-preference-learning-pl.md).
  Uzasadnienie:
  - PRD wymaga local-first, audytowalności i niskiego kosztu utrzymania.
  Konsekwencje:
  - System dodaje nowy magazyn JSON i musi utrzymać kompatybilność jego odczytu/zapisu między wersjami.

- Decyzja:
  - Ranking review używa `final_confidence` wyliczanego jako połączenie bazowego confidence oraz korekty preferencji, a nie wyłącznie confidence warstwy AI (dotyczy PRD: 004-user-preference-learning-pl.md).
  Uzasadnienie:
  - Celem przyrostu jest personalizacja propozycji przy zachowaniu istniejącego workflow review.
  Konsekwencje:
  - `ReviewItem` zawiera pola explainability i musi pozostać kompatybilny wstecz ze starszymi wpisami bez tych pól.

- Decyzja:
  - Uczenie z odrzuceń jest konserwatywne: najsilniejszy negatywny sygnał dotyczy pary propozycji (`parent_category`, `proposed_category`), a sygnały cech są słabsze lub pomijane (dotyczy PRD: 004-user-preference-learning-pl.md).
  Uzasadnienie:
  - Odrzucenie nie zawsze oznacza błędność wszystkich cech plików, lecz często dotyczy kontekstu lub nazewnictwa.
  Konsekwencje:
  - Formuła scoringu preferencji musi ograniczać overfitting i wzmacniać wpływ dopiero po powtarzalnym sygnale.

- Decyzja:
  - Komendy `apply` i `reject` wspierają przyjmowanie wielu ID pozycyjnie (`apply <id1> <id2> ...`, `reject <id1> <id2> ...`) z polityką kontynuacji batcha mimo błędów pojedynczych pozycji (dotyczy PRD: 005-batch-apply-reject-cli.md).
  Uzasadnienie:
  - Dla większych kolejek review użytkownik potrzebuje operacji masowych bez wielokrotnego ręcznego uruchamiania komend.
  Konsekwencje:
  - CLI musi raportować wynik zbiorczy i zwracać kod zakończenia `!= 0` przy częściowej porażce.

- Decyzja:
  - PRD 006 dodaje bootstrapową segregację plików luzem z root aktywnego katalogu źródłowego jako etap startowy `run/watch`, wykonywany przed klastrowaniem i AI (dotyczy PRD: 006-auto-downloads-bootstrap-segregation.md).
  Uzasadnienie:
  - Celem jest zmniejszenie szumu wejściowego i uporządkowanie danych przed etapami heurystycznymi i AI.
  Konsekwencje:
  - Pipeline `run/watch` zyskuje nową fazę wykonawczą na systemie plików oraz raport jej wyniku.

- Decyzja:
  - Występuje konflikt pomiędzy zasadą „Aplikacja **nie** wykonuje automatycznych zmian w strukturze plików bez decyzji użytkownika.” a automatycznym etapem segregacji PRD 006 (dotyczy PRD: 006-auto-downloads-bootstrap-segregation.md).
  Uzasadnienie:
  - PRD 006 zakłada automatyczne przeniesienia plików już na starcie `run/watch`, bez kroku review/apply.
  Konsekwencje:
  - Bootstrapowa segregacja aktywnego katalogu źródłowego jest trwałym wyjątkiem od zasady human-in-the-loop i nie wymaga dodatkowego mechanizmu zgody przed uruchomieniem.

---

## Jakość i kryteria akceptacji
Wspólne wymagania jakościowe dla całego projektu.
- Wszystkie operacje muszą działać lokalnie bez wysyłania danych poza maszynę użytkownika.
- Operacje klasyfikacji i review muszą być audytowalne przez trwały zapis decyzji i propozycji.
- Operacje na plikach muszą być idempotentne i bezpieczne względem ponownego uruchomienia procesu.
- Zmiany w strukturze plików muszą być rollback-safe.
- System musi obsługiwać przetwarzanie wsadowe dla większych folderów przy ograniczonym zużyciu pamięci.
- MVP jest zaakceptowane, gdy:
  - pliki są automatycznie klasyfikowane,
  - system wykrywa co najmniej trzy typy wzorców,
  - generowane są propozycje kategorii,
  - użytkownik może zatwierdzić propozycję przez CLI,
  - system zapisuje historię decyzji.
- Minimalnie akceptowalna skuteczność klasyfikacji to co najmniej 80% poprawnych klasyfikacji dla trzech głównych typów plików, takich jak `images`, `documents` i `archives`, mierzona na ręcznie zweryfikowanej próbce 200-300 plików.
- Maksymalnie 10% przypadków może wymagać ręcznej korekty przez użytkownika.
- Co najmniej 70% propozycji w kolejce review powinno być akceptowanych bez zmian jako sygnał, że wykryte wzorce są użyteczne.

---

## Zasady zmian i ewolucji
- zmiany funkcjonalne → aktualizacja `ROADMAP.md`
- zmiany architektoniczne → aktualizacja tej specyfikacji
- nowe zależności → wpis do `## Decyzje techniczne`
- refactory tylko w ramach aktualnego milestone’u

---

## Powiązanie z roadmapą
- Szczegóły milestone’ów i ich statusy znajdują się w `ROADMAP.md`.

---

## Status specyfikacji
- Data utworzenia: 2026-03-24
- Ostatnia aktualizacja: 2026-03-28
- Aktualny zakres obowiązywania: bazowy zakres produktu i MVP opisany w `prd/000-initial-prd.md`, przyrost wydajnościowy opisany w `prd/001-incremental-performance-watcher.md`, przyrost review opisany w `prd/002-review-ux-and-deduplication.md`, przyrost wykonawczy i konfiguracyjny opisany w `prd/003-apply-file-moves-and-ollama-model-cli.md`, przyrost uczenia preferencji opisany w `prd/004-user-preference-learning-pl.md`, przyrost batchowego `apply/reject` opisany w `prd/005-batch-apply-reject-cli.md` oraz przyrost bootstrapowej segregacji `~/Downloads` opisany w `prd/006-auto-downloads-bootstrap-segregation.md`
