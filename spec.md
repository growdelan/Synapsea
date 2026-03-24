# Specyfikacja techniczna

## Cel
Krótki opis celu aplikacji:
- Rozwiązuje problem chaotycznej, ręcznie utrzymywanej struktury plików poprzez lokalne analizowanie plików, wykrywanie wzorców i proponowanie sensownej, rozwijającej się taksonomii danych.
- Jest skierowana do użytkownika pracującego lokalnie na własnych zbiorach plików, który chce porządkować dane bez stałego ręcznego kategoryzowania.
- Zakres obejmuje lokalną klasyfikację plików, ekstrakcję cech, wykrywanie wzorców, generowanie propozycji zmian w strukturze oraz obsługę review przez CLI.
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
  - użytkownik przegląda, akceptuje lub odrzuca propozycje przez CLI.
- Aplikacja **nie** wykonuje automatycznych zmian w strukturze plików bez decyzji użytkownika.
- Aplikacja **nie** dostarcza interfejsu graficznego w MVP.
- Aplikacja **nie** wysyła danych poza lokalną maszynę.
- W MVP domyślnym katalogiem monitorowanym jest `~/Downloads`.
- MVP zakłada pojedynczy katalog wejściowy.

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
   - pliki z folderu wejściowego trafiają do skanera,
   - skaner przekazuje dane do ekstrakcji cech i klasyfikacji,
   - wyniki klasyfikacji są logowane i przekazywane do silnika wzorców,
   - kandydaci na klastry są oceniani przez warstwę AI,
   - propozycje kategorii lub zmian trafiają do kolejki review,
   - decyzje użytkownika aktualizują stan review, historię decyzji i taksonomię.
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
- monitor procesu:
  - uruchamiany ręcznie proces działający ciągle po starcie i oczekujący na zdarzenia w folderze `~/Downloads`.

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
- Ostatnia aktualizacja: 2026-03-24
- Aktualny zakres obowiązywania: bazowy zakres produktu i MVP opisany w `prd/000-initial-prd.md`
