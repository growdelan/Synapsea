# PRD: Terminalowa aplikacja TUI dla Synapsea oparta o Textual

## Metadane
- **PRD ID:** 005-textual-tui-workstation
- **Projekt:** Synapsea
- **Status:** Draft / Ready for implementation
- **Data utworzenia:** 2026-03-28
- **Zależności:** istniejące MVP + PRD 001, 002, 003, 004
- **Typ zakresu:** przyrost funkcjonalny / nowy frontend terminalowy

---

## 1. Cel

Celem tego PRD jest dodanie do Synapsea pełnej, wygodnej **aplikacji terminalowej TUI** opartej o framework **Textual**, która stanie się operacyjnym frontendem do istniejącego backendu projektu.

Aplikacja ma umożliwiać w jednym miejscu:
- uruchamianie `run` w celu analizy nowych lub zmodyfikowanych plików,
- przeglądanie kolejki review,
- zaznaczanie wielu pozycji jednocześnie,
- hurtowe wykonywanie `apply` i `reject`,
- szybki podgląd statusu systemu,
- późniejsze rozszerzenie o preferences i history.

Nowy interfejs ma zwiększyć wygodę codziennej pracy, ale **nie może duplikować logiki domenowej** istniejącego backendu.

---

## 2. Problem

Obecny interfejs Synapsea jest poprawny technicznie, ale jest ograniczony pod kątem ergonomii codziennego użycia.

Najważniejsze obecne problemy:
- `review` działa jako tekstowy output CLI, co utrudnia wygodną pracę na większej liczbie pozycji,
- brak wygodnego multi-select,
- brak hurtowego `apply` / `reject`,
- brak jednego miejsca, z którego można uruchomić `run`, zobaczyć wynik i od razu przejść do review,
- brak operacyjnego dashboardu pokazującego stan systemu,
- użytkownik musi mentalnie składać workflow z kilku oddzielnych komend.

W praktyce system ma już sensowny backend, ale brakuje mu **wygodnej warstwy obsługi operacyjnej**.

---

## 3. Oczekiwany rezultat

Po wdrożeniu tej funkcji użytkownik powinien móc uruchomić Synapsea w trybie TUI i obsługiwać główny workflow z jednego miejsca.

Docelowy flow:
1. użytkownik uruchamia aplikację terminalową,
2. widzi dashboard ze stanem systemu,
3. może uruchomić `run` dla nowych plików,
4. po zakończeniu `run` review queue automatycznie się odświeża,
5. użytkownik przechodzi do widoku review,
6. zaznacza wiele pozycji,
7. wykonuje `apply selected` albo `reject selected`,
8. wynik działań jest czytelnie raportowany,
9. użytkownik wraca do dashboardu lub kończy pracę.

TUI ma być **nakładką operacyjną** na istniejący backend Synapsea, a nie osobnym niezależnym systemem.

---

## 4. Poza zakresem

Ten przyrost **nie** obejmuje:
- GUI desktopowego,
- aplikacji webowej,
- synchronizacji z chmurą,
- zmian w podstawowej logice klasyfikacji,
- zmian w podstawowej logice review poza tym, co jest potrzebne do obsługi TUI,
- pełnego watch dashboard w pierwszej wersji,
- zaawansowanych wykresów i wizualizacji,
- automatyzacji działań bez potwierdzenia użytkownika,
- uruchamiania backendu przez shell subprocess jako podstawowego mechanizmu integracji.

---

## 5. Zasady projektowe

1. **Backend remains source of truth**
   - logika domenowa pozostaje w istniejących komponentach Synapsea.

2. **TUI jako frontend operacyjny**
   - aplikacja Textual ma zarządzać stanem widoków i akcjami użytkownika, ale nie ma duplikować logiki klasyfikacji, review ani storage.

3. **Keyboard-first UX**
   - wszystkie kluczowe operacje mają być wygodne z klawiatury.

4. **Batch-friendly**
   - operacje na wielu review items muszą być obsługiwane jako funkcja pierwszej klasy.

5. **Safety-first**
   - ponieważ `apply` wykonuje realne przenoszenie plików, każda akcja batch musi mieć czytelne potwierdzenie i raport wyniku.

6. **Progressive enhancement**
   - pierwsza wersja ma dawać duży skok ergonomii bez budowy zbyt dużego interfejsu.

---

## 6. User stories

### 6.1 Dashboard
Jako użytkownik chcę po uruchomieniu aplikacji zobaczyć stan systemu, liczbę pending review items i podstawową konfigurację, abym wiedział, co wymaga mojej uwagi.

### 6.2 Run z poziomu TUI
Jako użytkownik chcę móc uruchomić `run` bez wychodzenia do shella, aby szybko przeskanować nowe pliki i od razu zobaczyć wynik.

### 6.3 Review na wielu pozycjach
Jako użytkownik chcę zaznaczać wiele pozycji review i wykonywać na nich hurtowo `apply` albo `reject`, aby praca była szybka i wygodna.

### 6.4 Szczegóły rekordu
Jako użytkownik chcę widzieć szczegóły aktualnie zaznaczonej pozycji review bez opuszczania listy, aby łatwo podejmować decyzje.

### 6.5 Czytelny wynik działań
Jako użytkownik chcę dostać czytelny raport po `run`, `apply` i `reject`, abym wiedział, co się faktycznie wydarzyło.

### 6.6 Zachowanie prostego CLI
Jako użytkownik chcę, aby stare CLI nadal działało, bo TUI ma być dodatkiem, a nie wymuszonym zastępstwem.

---

## 7. Zakres wysokopoziomowy

Nowa funkcja obejmuje:
- nowy tryb uruchomienia aplikacji TUI,
- dashboard z podstawowymi statystykami,
- ekran review z listą i panelem szczegółów,
- multi-select i batch actions,
- uruchamianie `run` z poziomu TUI,
- automatyczne odświeżenie danych po `run`,
- obsługę potwierdzeń i raportów wyników,
- architekturę pozwalającą później dodać preferences i history.

---

## 8. Wymagania funkcjonalne

### 8.1 Nowy tryb uruchomienia TUI

System musi udostępnić nowy sposób uruchomienia TUI.

Rekomendowana forma:
```bash
uv run python -m synapsea tui
```

Wymaganie:
- TUI musi być osobnym trybem pracy,
- istniejące komendy CLI (`run`, `review`, `apply`, `reject`) muszą nadal działać.

### 8.2 Dashboard jako ekran startowy

Po uruchomieniu TUI użytkownik musi zobaczyć ekran główny typu dashboard.

Dashboard powinien pokazywać co najmniej:
- aktywny `source_dir`,
- aktywny `data_dir`,
- czy AI review jest aktywne,
- aktywny model Ollama,
- liczbę review items w statusie `pending`,
- liczbę pozycji `applied`,
- liczbę pozycji `rejected`,
- informację o ostatnim uruchomieniu `run`,
- status ostatniej operacji: sukces / błąd / brak danych.

Dashboard musi udostępniać szybkie akcje:
- przejście do review,
- uruchomienie `run`,
- uruchomienie `run with options`,
- wyjście z aplikacji.

### 8.3 Uruchamianie `run` z poziomu TUI

Użytkownik musi móc uruchomić pipeline `run` z poziomu TUI bez przechodzenia do shella.

Implementacja musi korzystać z istniejącego backendu Synapsea bez opierania głównej ścieżki na subprocess shell command.

Preferowane podejście:
- zbudowanie `AppConfig`,
- utworzenie `SynapseaApp.from_config(config)`,
- wywołanie `run_once()` bezpośrednio w kodzie aplikacji.

Wymagania:
- po zakończeniu `run` TUI musi automatycznie odświeżyć dane dashboardu i review queue,
- użytkownik musi dostać czytelny rezultat operacji,
- błędy muszą być obsłużone i pokazane w interfejsie bez crashowania całej aplikacji.

### 8.4 Dwa tryby uruchamiania `run`

TUI powinno wspierać dwa sposoby uruchamiania `run`.

#### 8.4.1 Run standardowy
Szybka akcja typu:
- `Run now`

Zachowanie:
- używa aktualnej konfiguracji,
- nie wymaga dodatkowej interakcji,
- po zakończeniu odświeża dane.

#### 8.4.2 Run rozszerzony
Akcja typu:
- `Run with options`

Użytkownik może zmienić przed uruchomieniem:
- `source_dir`,
- `data_dir`,
- `skip_ai`,
- `ollama_model`,
- `ai_budget`,
- `ai_max_examples`.

W pierwszej wersji wystarczy prosty formularz / modal z podstawowymi polami.

### 8.5 Ekran Review

TUI musi zawierać główny ekran review służący do codziennej pracy na kolejce propozycji.

Układ powinien zawierać:
- listę/tabelę review items,
- panel szczegółów aktualnie wybranego elementu,
- pasek statusu / pasek skrótów klawiszowych.

Lista review items powinna pokazywać co najmniej:
- stan zaznaczenia `[ ]` / `[x]`,
- `item_id`,
- `status`,
- `parent_category`,
- `proposed_category`,
- `confidence`,
- liczbę `candidate_files`.

Panel szczegółów powinien pokazywać co najmniej:
- `target_path`,
- pełny `reason`,
- preview przykładowych `candidate_files`,
- później opcjonalnie `base_confidence`, `preference_delta`, `final_confidence`.

### 8.6 Multi-select jako funkcja pierwszej klasy

Użytkownik musi móc zaznaczać wiele elementów review jednocześnie.

Wymagania:
- zaznaczenie musi być niezależne od aktualnego focusa,
- użytkownik może poruszać się po liście bez utraty zaznaczenia,
- akcje batch działają na zbiorze zaznaczonych pozycji, a nie tylko na aktualnym wierszu,
- możliwe musi być szybkie zaznaczanie i odznaczanie.

Minimalny zestaw operacji:
- zaznacz / odznacz bieżący element,
- zaznacz wszystkie widoczne,
- wyczyść zaznaczenie.

### 8.7 Batch `apply`

TUI musi umożliwiać batchowe `apply` dla zaznaczonych pozycji.

Wymagania:
- przed wykonaniem akcji musi pojawić się modal potwierdzenia,
- modal powinien pokazać liczbę zaznaczonych elementów,
- modal powinien ostrzegać, że `apply` wykonuje realne operacje na plikach,
- po zatwierdzeniu akcja powinna być wykonywana sekwencyjnie,
- po zakończeniu użytkownik musi dostać zbiorczy raport wyniku.

Raport końcowy powinien pokazywać co najmniej:
- liczbę pozycji skutecznie zastosowanych,
- łączną liczbę `moved`,
- łączną liczbę `skipped`,
- łączną liczbę `errors`,
- liczbę pozycji, których nie udało się zastosować.

System nie może przerwać całego batcha tylko dlatego, że pojedynczy item zakończył się błędem.

### 8.8 Batch `reject`

TUI musi umożliwiać batchowe `reject` dla zaznaczonych pozycji.

Wymagania:
- przed wykonaniem musi pojawić się modal potwierdzenia,
- akcja powinna być wykonywana sekwencyjnie,
- wynik zbiorczy powinien być pokazany użytkownikowi,
- błędy pojedynczych elementów nie mogą zatrzymać całej operacji.

Raport końcowy powinien pokazywać co najmniej:
- liczbę pozycji skutecznie odrzuconych,
- liczbę błędów.

### 8.9 Automatyczne odświeżanie danych po akcjach

Po każdej z poniższych operacji TUI musi odświeżyć stan interfejsu:
- `run`,
- `apply`,
- `reject`.

Odświeżenie powinno objąć:
- dashboard,
- review queue,
- liczniki statusów,
- bieżący widok, jeśli użytkownik na nim pozostaje.

### 8.10 Filtrowanie i sortowanie review

Pierwsza wersja TUI powinna umożliwiać minimum podstawowe filtrowanie i sortowanie review items.

Minimalny zestaw:
- filtr `pending only`,
- pokazanie wszystkich statusów,
- prosty filtr tekstowy,
- sortowanie po confidence,
- sortowanie po liczbie candidate files.

Jeśli pełna implementacja filtrowania nie zmieści się do pierwszego milestone’u, to `pending only`, `all statuses` i sortowanie po confidence są obowiązkowe.

### 8.11 Pełny podgląd szczegółów

Użytkownik powinien móc przejść do pełniejszego podglądu pozycji review.

Minimalny zakres:
- pełny `reason`,
- pełna lista lub większy preview `candidate_files`,
- najważniejsze pola review item.

Może to być:
- osobny modal,
- albo rozszerzony panel szczegółów,
- albo osobny ekran details.

### 8.12 Czytelna obsługa błędów

TUI musi obsługiwać błędy w sposób nieprzerywający pracy użytkownika.

Wymagania:
- błąd `run` nie może crashować aplikacji,
- błąd pojedynczego `apply` lub `reject` nie może crashować aplikacji,
- komunikat błędu musi być pokazany użytkownikowi,
- system powinien zachować spójny stan interfejsu po błędzie.

### 8.13 Zachowanie kompatybilności starego CLI

Istniejące komendy tekstowe muszą nadal działać:
- `run`
- `review`
- `apply`
- `reject`

TUI ma być dodatkowym frontendem, a nie zastępstwem CLI.

---

## 9. Wymagania UX

### 9.1 Model nawigacji

Aplikacja powinna mieć spójny model nawigacji oparty o ekrany.

Minimalny zestaw ekranów:
- `DashboardScreen`
- `ReviewScreen`

Dodatkowe elementy:
- `RunDialog` albo `RunScreen`
- `ConfirmBatchActionModal`

W kolejnych iteracjach przewidziane:
- `PreferencesScreen`
- `HistoryScreen`

### 9.2 Keyboard-first shortcuts

Minimalny zestaw skrótów globalnych:
- `d` → dashboard
- `w` → review
- `r` → run now
- `R` → run with options
- `q` → quit

Minimalny zestaw skrótów w review:
- `↑/↓` → poruszanie po liście
- `space` → zaznacz / odznacz
- `x` → zaznacz wszystkie widoczne
- `u` → wyczyść zaznaczenie
- `a` → apply selected
- `r` → reject selected
- `/` → filtr tekstowy
- `p` → tylko pending
- `A` → wszystkie statusy
- `enter` → szczegóły
- `tab` → przełącz fokus lista / szczegóły
- `esc` → powrót do dashboardu

### 9.3 Status bar / help bar

TUI powinno posiadać pasek statusu lub pasek skrótów pokazujący najważniejsze dostępne akcje.

### 9.4 Czytelność wyniku `run`

Po uruchomieniu `run` użytkownik powinien otrzymać czytelne podsumowanie:
- czy operacja zakończyła się sukcesem,
- ile plików zostało przetworzonych,
- ile nowych review items pojawiło się po przebiegu albo ile ich jest po odświeżeniu,
- czy wystąpił błąd.

---

## 10. Architektura

### 10.1 Zasada architektoniczna

TUI nie implementuje logiki domenowej.
TUI wywołuje istniejący backend Synapsea.

Niedopuszczalne jako główna ścieżka:
- poleganie na wywoływaniu shell subprocessów dla każdej operacji biznesowej.

### 10.2 Preferowany model warstw

Rekomendowany podział odpowiedzialności:

- **backend Synapsea**
  - klasyfikacja
  - clustering
  - review queue
  - apply / reject
  - storage

- **controller TUI**
  - wywoływanie backendu
  - odświeżanie danych
  - mapowanie wyników backendu na stan UI

- **screeny / widgety Textual**
  - prezentacja danych
  - zbieranie inputu użytkownika
  - nawigacja
  - potwierdzenia i komunikaty

### 10.3 Sugerowana struktura kodu

```text
src/synapsea/tui/
├── app.py
├── controllers/
│   └── app_controller.py
├── screens/
│   ├── dashboard.py
│   ├── review.py
│   ├── run.py
│   ├── preferences.py
│   └── history.py
├── widgets/
│   ├── review_table.py
│   ├── review_detail.py
│   └── summary_cards.py
└── modals/
    ├── confirm_batch_action.py
    └── run_options.py
```

### 10.4 Controller aplikacji

Rekomendowane jest dodanie warstwy `controller`, np. `app_controller.py`, odpowiedzialnej za:
- budowę `AppConfig`,
- tworzenie `SynapseaApp`,
- wywoływanie `run_once()`,
- pobieranie review items,
- wykonywanie `apply_review_item()` i `reject_review_item()`,
- agregowanie raportów batch,
- odświeżanie danych dla widoków.

---

## 11. Wymagania techniczne

### 11.1 Nowa zależność

Projekt może dodać zależność:
- `textual`

Dopuszczalne jest dodanie tej zależności do `pyproject.toml`.

### 11.2 Integracja z istniejącym CLI

CLI musi zostać rozszerzone o nową komendę uruchamiającą TUI.

Przykład:
```bash
uv run python -m synapsea tui
```

Implementacja powinna być spójna z istniejącym `argparse`.

### 11.3 Wydajność

TUI musi pozostać lekkie i sprawne dla lokalnego użycia.

Wymagania:
- brak zbędnych reloadów całego stanu przy każdej drobnej interakcji,
- ładowanie review items powinno być wystarczająco szybkie dla typowych lokalnych zbiorów,
- batch actions powinny raportować postęp lub przynajmniej nie blokować użytkownika w nieczytelny sposób.

### 11.4 Bezpieczeństwo

Ponieważ `apply` wykonuje realne operacje na plikach, TUI musi:
- wymagać jawnego potwierdzenia przed batch `apply`,
- jasno komunikować skutki operacji,
- raportować błędy i kolizje,
- nie ukrywać, że operacja działa na systemie plików.

---

## 12. Szczegóły działania ekranu Dashboard

Dashboard powinien pokazywać:
- aktywny katalog źródłowy,
- aktywny katalog danych,
- model Ollama,
- AI enabled / disabled,
- liczby review items per status,
- informację o ostatnim `run`.

Dashboard powinien umożliwiać:
- przejście do review,
- uruchomienie `run now`,
- uruchomienie `run with options`,
- wyjście z aplikacji.

---

## 13. Szczegóły działania ekranu Review

Lista musi wspierać:
- focus,
- zaznaczanie,
- odświeżanie po akcjach,
- filtrowanie,
- sortowanie.

Panel szczegółów powinien aktualizować się zgodnie z aktualnym focusem listy, a nie tylko zaznaczeniem batch.

Zaznaczenie batch ma być przechowywane jako osobny stan.
Zmiana focusa nie może czyścić zaznaczenia.

Domyślny widok review powinien pokazywać tylko `pending`.
Użytkownik powinien móc przełączyć widok na wszystkie statusy.

---

## 14. Scenariusze użytkownika

### 14.1 Codzienna praca
1. Użytkownik uruchamia TUI.
2. Widzi dashboard.
3. Uruchamia `run now`.
4. Po zakończeniu widzi zaktualizowaną liczbę pending.
5. Przechodzi do review.
6. Zaznacza kilka pozycji.
7. Robi batch `apply`.
8. Otrzymuje raport i wraca do listy.

### 14.2 Szybki review bez run
1. Użytkownik uruchamia TUI.
2. Od razu przechodzi do review.
3. Filtruje pending.
4. Wykonuje batch `reject`.
5. Wraca do dashboardu i kończy pracę.

### 14.3 Run z opcjami
1. Użytkownik uruchamia TUI.
2. Otwiera `Run with options`.
3. Zmienia np. `skip_ai` i `ollama_model`.
4. Uruchamia przebieg.
5. Otrzymuje wynik.
6. Review queue zostaje odświeżone.

---

## 15. Kryteria akceptacji

Funkcja jest zaakceptowana, gdy:
1. projekt udostępnia nową komendę uruchamiającą TUI,
2. po uruchomieniu użytkownik widzi dashboard,
3. z poziomu TUI można wykonać `run now`,
4. po `run` dane są automatycznie odświeżane,
5. TUI udostępnia ekran review z listą pozycji,
6. można zaznaczać wiele pozycji jednocześnie,
7. można wykonać batch `apply`,
8. można wykonać batch `reject`,
9. batch `apply` wymaga potwierdzenia,
10. wynik akcji jest raportowany użytkownikowi,
11. błąd pojedynczej operacji nie crashuje aplikacji,
12. istniejące klasyczne CLI dalej działa,
13. TUI nie duplikuje logiki domenowej backendu.

---

## 16. Sugerowane scenariusze testowe

- start aplikacji i pokazanie dashboardu,
- `run now` z odświeżeniem review queue,
- multi-select utrzymujący stan zaznaczenia,
- batch `apply` z raportem zbiorczym,
- batch `reject` z raportem zbiorczym,
- odporność na błąd pojedynczego elementu,
- kompatybilność wstecz starego CLI.

---

## 17. Ryzyka

1. **Przeniesienie zbyt dużej ilości logiki do UI**
   - ograniczać przez wyraźny controller i reuse backendu.

2. **Nieczytelna obsługa batch actions**
   - ograniczać przez modale potwierdzeń i dobre raporty wyniku.

3. **Zbyt duży pierwszy zakres**
   - ograniczać przez wdrożenie etapowe.

4. **Blokowanie UI podczas dłuższego `run`**
   - ograniczać przez jasny stan „running” i późniejsze ulepszenie o lepszy progress handling.

---

## 18. Plan wdrożenia etapami

### 18.1 Etap 1 — MVP TUI
Zakres obowiązkowy:
- komenda `tui`,
- `DashboardScreen`,
- `ReviewScreen`,
- `Run now`,
- multi-select,
- batch `apply`,
- batch `reject`,
- auto-refresh po akcjach,
- podstawowa obsługa błędów.

### 18.2 Etap 2 — rozszerzenie ergonomii
Zakres rekomendowany:
- `Run with options`,
- lepsze filtrowanie,
- sortowanie,
- pełniejszy panel szczegółów,
- czytelniejsze podsumowanie po `run`,
- lepsze modale i komunikaty.

### 18.3 Etap 3 — dalszy rozwój
Zakres przyszły:
- `PreferencesScreen`,
- `HistoryScreen`,
- status `watch`,
- dodatkowe skróty i lepsza nawigacja.

---

## 19. Uwagi implementacyjne dla agenta kodującego

Najważniejsza zasada: **nie budować drugiego backendu w TUI**.

Priorytet implementacyjny:
1. dodać zależność `textual`,
2. dodać komendę `tui`,
3. zbudować prosty controller spinający TUI z `SynapseaApp`,
4. dodać dashboard,
5. dodać review z multi-select,
6. dodać batch `apply/reject`,
7. dodać `run now`,
8. dodać `run with options`.

W trade-offach preferować:
- prostotę,
- stabilność,
- bezpieczeństwo operacji na plikach,
- spójność z backendem,
- wygodę keyboard-first.

---

## 20. Definition of done

Funkcja jest ukończona, gdy:
- użytkownik może uruchomić Synapsea jako aplikację TUI,
- może z dashboardu odpalić `run`,
- po `run` review queue odświeża się automatycznie,
- może zaznaczać wiele review items,
- może wykonywać batch `apply` i `reject`,
- dostaje czytelne raporty wyników,
- stare CLI nadal działa,
- TUI pozostaje lekką i sensowną nakładką operacyjną na istniejący backend.
