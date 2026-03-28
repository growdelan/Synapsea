# PRD: Uczenie preferencji użytkownika dla lokalnej organizacji plików

## Metadane
- **PRD ID:** 004-user-preference-learning
- **Projekt:** Synapsea
- **Status:** Draft / Ready for implementation
- **Data utworzenia:** 2026-03-28
- **Zależności:** istniejące MVP + PRD 001, 002, 003
- **Typ zakresu:** przyrost funkcjonalny

---

## 1. Cel

Dodać lekką, **lokalną warstwę uczenia preferencji użytkownika**, dzięki której Synapsea będzie z czasem dopasowywać się do realnych nawyków porządkowania plików, bez potrzeby ręcznego definiowania rozszerzeń, typów plików ani rozbudowanego zestawu reguł.

System powinien uczyć się głównie na podstawie:
- zaakceptowanych pozycji review (`apply`),
- odrzuconych pozycji review (`reject`),
- pasywnych sygnałów uczenia już zbieranych przez system,
- powtarzalnych wzorców w nazwach plików, tokenach i prostych heurystykach.

Funkcja musi pozostać:
- w pełni lokalna,
- lekka,
- audytowalna,
- bezpieczna,
- zgodna z istniejącym workflow opartym o CLI.

---

## 2. Problem

Obecne działanie Synapsea opiera się głównie na:
- heurystykach zaszytych w kodzie,
- tokenach z nazw plików,
- rozszerzeniach,
- prostym klastrowaniu,
- opcjonalnej interpretacji AI.

To działa, ale system jest nadal przede wszystkim **generyczny**, a nie **spersonalizowany**.

Przykłady obecnych ograniczeń:
- użytkownik może chcieć trzymać screenshoty w osobnej kategorii, ale system nie posiada trwałego modelu takiej preferencji,
- użytkownik może wielokrotnie akceptować kategorie związane z fakturami/finansami, ale przyszły ranking nie poprawia się wystarczająco na podstawie tego wzorca,
- użytkownik może wielokrotnie odrzucać określony typ propozycji, ale system nie internalizuje mocno, że taka sugestia zwykle nie jest pożądana.

W efekcie jakość propozycji może dojść do plateau, mimo że użytkownik stale dostarcza feedback przez review.

---

## 3. Oczekiwany rezultat

Po wdrożeniu tej funkcji Synapsea powinien stopniowo uczyć się preferencji takich jak:

- pliki zawierające tokeny typu `invoice`, `faktura`, `receipt` częściej należą do gałęzi finansowej,
- pliki podobne do screenshotów powinny preferować kategorię związaną ze screenshotami,
- wielokrotnie odrzucane nazwy kategorii powinny dostawać karę w przyszłym rankingu,
- wielokrotnie akceptowane relacje token/kategoria powinny dostawać wzrost confidence,
- system powinien udostępniać czytelny, lokalny podgląd tego, czego się nauczył.

Funkcja ma poprawić:
- trafność przyszłych sugestii review,
- stabilność ewolucji taksonomii,
- zaufanie użytkownika,
- dopasowanie do osobistych nawyków,
bez wprowadzania ciężkiej infrastruktury ML.

---

## 4. Poza zakresem

Ta funkcja **nie** obejmuje:
- synchronizacji z chmurą,
- zewnętrznych usług AI,
- embeddings / vector database,
- GUI,
- pełnej automatyzacji zmian taksonomii bez review,
- utrzymywanego przez użytkownika systemu mapowania rozszerzeń,
- zaawansowanego rozumienia semantycznego treści dokumentów,
- ekstrakcji treści z wnętrza plików (to należy do późniejszego feature’a).

---

## 5. Zasady produktowe

1. **Local-first**
   - wszystkie dane uczące muszą pozostać na lokalnej maszynie.

2. **Human-in-the-loop**
   - wyuczone preferencje wpływają na ranking i jakość rekomendacji, ale nie omijają review.

3. **Low-maintenance**
   - użytkownik nie powinien ręcznie definiować dziesiątek reguł.

4. **Explainable**
   - system musi umieć pokazać, czego się nauczył i dlaczego confidence się zmieniło.

5. **Conservative learning**
   - system powinien wzmacniać preferencje dopiero po powtarzalnym sygnale, aby ograniczyć szum.

---

## 6. User stories

### 6.1 Core
Jako użytkownik chcę, aby Synapsea uczył się na podstawie moich zaakceptowanych i odrzuconych decyzji review, tak aby przyszłe sugestie lepiej pasowały do mojego stylu porządkowania plików.

### 6.2 Transparency
Jako użytkownik chcę móc sprawdzić, czego system się nauczył, tak abym mógł ufać jego działaniu i je zweryfikować.

### 6.3 Niski koszt konfiguracji
Jako użytkownik nie chcę ręcznie definiować wszystkich rozszerzeń plików ani reguł folderów, ponieważ system powinien sam wyciągać użyteczne preferencje z mojego zachowania.

### 6.4 Safety
Jako użytkownik chcę, aby wyuczone preferencje poprawiały ranking, a nie powodowały ciche przenoszenie plików bez mojej decyzji.

---

## 7. Zakres wysokopoziomowy

Funkcja wprowadza nową warstwę uczenia preferencji, która obejmuje:

- trwały lokalny magazyn preferencji,
- logikę aktualizacji preferencji na podstawie działań użytkownika,
- logikę scoringu przyszłych pozycji review z użyciem wyuczonych preferencji,
- komendę CLI do podglądu wyuczonych preferencji,
- opcjonalne lekkie ręczne override’y dla niewielkiej liczby preferencji wysokiego poziomu.

---

## 8. Wymagania funkcjonalne

## 8.1 Trwały magazyn preferencji

System musi zapisywać wyuczone preferencje w nowym lokalnym pliku:

- `data/user_preferences.json`

Magazyn musi być czytelnym JSON-em.

Musi wspierać co najmniej następujące typy sygnałów:
- preferencje token → kategoria,
- preferencje klasa heurystyczna → kategoria,
- preferencje wzorzec → kategoria,
- statystyki akceptacji proponowanej kategorii,
- statystyki odrzuceń proponowanej kategorii,
- statystyki pary parent-category + proposed-category.

Struktura nie musi być identyczna jak w przykładzie poniżej, ale musi wspierać następujący model pojęciowy:

```json
{
  "token_preferences": {
    "invoice": {
      "documents/finance": {
        "accept_count": 3,
        "reject_count": 0,
        "score": 0.75
      }
    }
  },
  "heuristic_preferences": {
    "screenshot_like": {
      "images/screenshots": {
        "accept_count": 4,
        "reject_count": 1,
        "score": 0.65
      }
    }
  },
  "pattern_preferences": {
    "dated_or_numbered": {
      "documents/reports": {
        "accept_count": 2,
        "reject_count": 0,
        "score": 0.4
      }
    }
  },
  "proposal_preferences": {
    "documents::finance": {
      "accept_count": 5,
      "reject_count": 1,
      "score": 0.8
    }
  },
  "metadata": {
    "version": 1
  }
}
```

Implementacja może normalizować klucze kategorii jako:
- target path,
- albo `parent_category/proposed_category`,
- albo inny stabilny klucz wewnętrzny.

Wybrany format klucza musi być spójny i opisany w kodzie.

---

## 8.2 Uczenie na `apply`

Gdy pozycja review zostanie zastosowana, system musi zaktualizować preferencje przy użyciu zaakceptowanej kategorii docelowej.

Sygnały, które powinny brać udział:
- tokeny pochodzące z plików kandydatów,
- dostępne klasy heurystyczne,
- istotne wzorce lub sygnały klastra,
- para (`parent_category`, `proposed_category`),
- `target_path`.

System powinien:
- zwiększać liczniki akceptacji,
- zwiększać score preferencji dla pasujących relacji,
- zapisywać wystarczająco dużo danych, aby później wyjaśnić wynik scoringu.

Jeśli pozycja review zawiera wiele plików kandydatów, aktualizacja uczenia może agregować cechy z całego zestawu.

Jeśli część plików źródłowych już nie istnieje, uczenie nadal powinno działać na podstawie metadanych pozycji review tam, gdzie to możliwe.

---

## 8.3 Uczenie na `reject`

Gdy pozycja review zostanie odrzucona, system musi zapisać negatywny sygnał dla proponowanej relacji kategorii.

Minimalne wymaganie:
- zwiększenie licznika odrzuceń dla pary propozycji,
- obniżenie przyszłego score dla semantycznie równoważnych propozycji,
- zachowanie audytowalności.

Opcjonalnie, ale rekomendowane:
- zastosowanie słabszych negatywnych sygnałów do mocno reprezentowanych tokenów lub klas heurystycznych powiązanych z odrzuconą propozycją.

Uczenie na odrzuceniach musi być bardziej konserwatywne niż uczenie na akceptacjach, ponieważ odrzucenie może oznaczać:
- złą nazwę kategorii,
- złą lokalizację w taksonomii,
- zły moment,
- niewystarczający confidence,
a niekoniecznie to, że wszystkie cechy plików są błędne.

---

## 8.4 Konserwatywny próg dowodu

System musi unikać overfittingu do pojedynczych zdarzeń.

Minimalne wymaganie:
- pojedynczy odosobniony sygnał nie może tworzyć silnej preferencji,
- preferencje powinny mieć realny wpływ dopiero po powtarzalnym sygnale.

Rekomendowana implementacja:
- liczniki są zawsze zapisywane,
- wpływ score jest słaby dla count=1,
- score staje się znaczący od count>=2,
- score staje się mocny od count>=3.

Dokładna formuła zależy od implementacji, ale musi spełniać powyższą zasadę.

---

## 8.5 Scoring przyszłych propozycji na bazie preferencji

Zanim pozycja review zostanie dodana lub zaktualizowana w review queue, Synapsea musi policzyć **korektę score wynikającą z preferencji**.

Ta korekta powinna wpływać na:
- końcowy confidence używany do rankingu,
- albo bezpośrednio na kolejność rankingu,
- albo na oba elementy.

System nie może całkowicie zastępować istniejącego confidence score’em preferencji.
Zamiast tego powinien łączyć:
- oryginalny confidence AI / heurystyki,
- boost wynikający z preferencji,
- karę wynikającą z negatywnych preferencji.

Rekomendowane zachowanie końcowe:
- silne wcześniejsze akceptacje podobnych propozycji podnoszą score,
- powtarzalne odrzucenia obniżają score,
- brak historii pozostawia oryginalny confidence prawie bez zmian.

Przykład:
- original confidence: `0.78`
- preference boost: `+0.08`
- rejection penalty: `-0.03`
- final confidence: `0.83`

Implementacja może ograniczać finalny wynik do bezpiecznego zakresu, np. `0.0..0.99`.

---

## 8.6 Pola explainability w review items

Pozycje review powinny zawierać wystarczająco dużo informacji, aby zrozumieć wpływ preferencji.

Minimalnie musi istnieć jedno z poniższych:
- dodatkowe pole typu `preference_score`,
- dodatkowe pole typu `confidence_breakdown`,
- albo rozszerzone tekstowe wyjaśnienie w `reason`.

Preferowane podejście:
- dodać pola strukturalne do `ReviewItem`, np.:
  - `base_confidence`
  - `preference_delta`
  - `final_confidence`
  - `preference_reasons: list[str]`

To podejście jest mocno preferowane względem kodowania wszystkiego wyłącznie w wolnym tekście.

Musi zostać zachowana kompatybilność wstecz z istniejącymi zapisanymi review items.

---

## 8.7 Komenda CLI do inspekcji preferencji

Dodać nową komendę CLI:

```bash
uv run python -m synapsea preferences --data-dir ./data
```

Komenda powinna wyświetlać czytelne podsumowanie wyuczonych preferencji.

Minimalne oczekiwania wobec outputu:
- top zaakceptowane pary propozycji,
- top odrzucone pary propozycji,
- najsilniejsze wyuczone preferencje tokenów,
- najsilniejsze wyuczone preferencje klas heurystycznych.

Rekomendowane opcjonalne flagi:
- `--verbose` dla pełnych szczegółów,
- `--limit N` do kontroli wielkości outputu.

Przykładowe użycie:

```bash
uv run python -m synapsea preferences --data-dir ./data
uv run python -m synapsea preferences --data-dir ./data --verbose
uv run python -m synapsea preferences --data-dir ./data --limit 20
```

---

## 8.8 Opcjonalne lekkie manual override

System może wspierać mały plik ręcznych override’ów dla preferencji wysokiego poziomu.

Przykładowy plik:
- `data/user_preference_overrides.json`

Dozwolone use-case’i:
- aliasowanie preferowanych nazw kategorii,
- blokowanie wybranych nazw kategorii,
- wzmacnianie niewielkiej liczby jawnych mapowań.

To jest opcjonalne w pierwszej implementacji i musi pozostać małe zakresem.
Nie może przerodzić się w rozbudowany system konfiguracji rozszerzeń.

---

## 9. Wymagania dla modelu danych

## 9.1 Nowe repozytorium
Dodać repozytorium odpowiedzialne za odczyt i zapis preferencji użytkownika, np.:

- `user_preferences.py`

Sugerowana klasa:
- `UserPreferencesRepository`

Odpowiedzialności:
- ładowanie danych preferencji,
- aktualizacja liczników i score,
- trwały zapis,
- udostępnianie helperów do scoringu i raportowania.

---

## 9.2 Nowy model domenowy
Dodać jeden lub więcej modeli domenowych dla wyuczonych preferencji.

Przykładowe nazwy:
- `PreferenceStats`
- `PreferenceScoreBreakdown`
- `UserPreferencesSnapshot`

Dokładny projekt modeli zależy od implementacji, ale musi wspierać:
- accept count,
- reject count,
- derived score,
- strukturalny dostęp dla logiki scoringu.

---

## 9.3 Kompatybilność wstecz
Funkcja nie może psuć:
- istniejącego `review_queue.json`,
- istniejącego `taxonomy.json`,
- istniejącego `learning_signals.json`,
- istniejącego `candidate_clusters.json`,
- istniejącego `classification_log.db`.

Jeśli do zapisanych review items zostaną dodane nowe pola, logika ładowania musi tolerować brak tych pól.

---

## 10. Zasady działania

## 10.1 Czego należy uczyć się z zaakceptowanej propozycji
Dla zastosowanej pozycji review system powinien uczyć się przede wszystkim z:
- `candidate_files`,
- wyekstrahowanych tokenów plików,
- klas heurystycznych,
- typu wzorca / typu klastra,
- `(parent_category, proposed_category)`,
- `target_path`.

Jeśli ekstrakcja cech z plików jest nadal możliwa, należy jej użyć.
Jeśli nie, system powinien użyć metadanych dostępnych w review item.

---

## 10.2 Czego należy uczyć się z odrzuconej propozycji
Dla odrzuconej pozycji review najsilniejszy negatywny sygnał powinien dotyczyć:
- `(parent_category, proposed_category)`.

Dodatkowe negatywne uczenie na poziomie cech powinno być słabsze niż uczenie na akceptacjach.

---

## 10.3 Jak łączyć scoring
Rekomendowany styl formuły:

```text
final_confidence =
  clamp(
    base_confidence
    + proposal_pair_boost
    + token_boost
    + heuristic_boost
    + pattern_boost
    - rejection_penalty
  )
```

Dokładne stałe liczbowe zależą od implementacji.

Ważne ograniczenia:
- wpływ preferencji ma być zauważalny, ale nie dominujący,
- trzeba zapobiegać skrajnemu wzrostowi score,
- powtarzalny sygnał ma znaczyć więcej niż pojedyncze zdarzenie.

---

## 10.4 Wpływ na ranking
Ranking review queue powinien używać final confidence, a nie wyłącznie oryginalnego confidence.

Istniejąca zasada sortowania powinna zostać zachowana:
1. najpierw pending,
2. potem wyższy score,
3. potem bogatszy kontekst.

---

## 11. Wymagania UX dla CLI

## 11.1 Output komendy review
Komenda `review` powinna dalej działać bez łamania istniejących oczekiwań względem outputu.

Jeśli dodatkowe pola confidence są dostępne, komenda może:
- pokazywać final confidence w głównej kolumnie score,
- opcjonalnie pokazywać preference delta w trybie verbose.

Przykładowa koncepcja verbose:

```text
rev_003    pending    documents    finance    0.86    documents/finance    6
base=0.78 pref=+0.08 reasons=token:invoice, pair:documents->finance
```

Dokładny format zależy od implementacji.

---

## 11.2 Output komendy preferences
Komenda `preferences` powinna być zoptymalizowana pod czytelność, a nie pod zrzut surowego JSON-a.

Rekomendowane sekcje:
- najsilniejsze pozytywne preferencje,
- najsilniejsze negatywne preferencje,
- pary propozycji,
- mapowania token/kategoria,
- mapowania heurystyka/kategoria.

---

## 12. Wskazówki techniczne do implementacji

## 12.1 Punkty integracji
Agent kodujący powinien rozważyć następujące prawdopodobne punkty integracji:

- `models.py`
  - rozszerzenie `ReviewItem` lub dodanie modeli preferencji

- `pipeline.py`
  - aktualizacja preferencji przy `apply`
  - aktualizacja preferencji przy `reject`
  - liczenie korekty score przy tworzeniu review items

- `review_queue.py`
  - zapis dodatkowych pól score / explainability, jeśli będą potrzebne

- `cli.py`
  - dodanie komendy `preferences`
  - opcjonalne rozszerzenie `review --verbose`

- `feature_extractor.py`
  - ponowne użycie istniejącej ekstrakcji tokenów i heurystyk jako wejścia do uczenia

- możliwy nowy moduł:
  - `user_preferences.py`

---

## 12.2 Preferowane podejście architektoniczne
Użyć dedykowanego komponentu preferencji, a nie rozproszonej logiki ad hoc.

Rekomendowany kształt:
- repozytorium do persystencji,
- serwis scorer do liczenia delta score,
- mały helper do wyciągania evidence z klastra / review item.

Nie należy rozrzucać logiki preferencji po wielu niepowiązanych modułach, jeśli można ją zamknąć w jednym komponencie.

---

## 12.3 Ograniczenia wydajnościowe
Funkcja musi pozostać lekka.

Wymagania:
- brak dużych indeksów trzymanych w pamięci,
- brak zewnętrznej bazy danych poza obecnymi lokalnymi plikami/SQLite, chyba że pojawi się bardzo mocne uzasadnienie,
- scoring musi być wystarczająco tani, aby działał podczas normalnego `run` i `watch`,
- aktualizacje mają być inkrementalne.

Ponieważ jest to narzędzie lokalne, prosty zapis do JSON-a jest akceptowalny.

---

## 13. Kryteria akceptacji

Funkcja jest zaakceptowana, gdy wszystkie poniższe warunki są spełnione:

1. Synapsea zapisuje wyuczone preferencje lokalnie w dedykowanym magazynie.
2. `apply` aktualizuje pozytywne sygnały preferencji.
3. `reject` aktualizuje negatywne sygnały preferencji co najmniej na poziomie par propozycji.
4. Ranking przyszłych review items odzwierciedla wyuczone preferencje.
5. System pozostaje local-only.
6. Istniejące flow CLI dalej działa.
7. Nowa komenda CLI pozwala podejrzeć wyuczone preferencje.
8. Pojedyncze odosobnione akcje użytkownika nie powodują zbyt silnych zmian score.
9. Istniejące pliki danych pozostają kompatybilne.
10. Implementacja jest audytowalna: użytkownik może zrozumieć, dlaczego confidence się zmieniło.

---

## 14. Sugerowane scenariusze testowe

## 14.1 Uczenie preferencji z zaakceptowanych propozycji
- Given: powtarzalnie zaakceptowane propozycje dla `documents -> finance`,
- when: później pojawia się podobny klaster,
- then: final confidence powinien być wyższy niż base confidence.

## 14.2 Kara za odrzucenia
- Given: powtarzalne odrzucenia tej samej pary propozycji,
- when: semantycznie równoważna propozycja pojawia się ponownie,
- then: final confidence powinien być niższy.

## 14.3 Konserwatywne uczenie
- Given: dokładnie jedna zaakceptowana akcja,
- when: pojawia się podobna propozycja,
- then: wzrost score powinien być niewielki.

## 14.4 CLI preferences
- Given: istnieją wyuczone preferencje,
- when: użytkownik uruchamia `preferences`,
- then: output powinien pokazać najsilniejsze wyuczone sygnały.

## 14.5 Kompatybilność wstecz
- Given: stare zapisane review items bez pól preferencji,
- when: Synapsea je ładuje,
- then: nie może zostać rzucony wyjątek.

## 14.6 Brak części candidate files
- Given: review item zostaje zastosowany, ale część plików kandydatów została już wcześniej przeniesiona lub usunięta,
- when: uruchomi się uczenie preferencji,
- then: system nadal powinien zaktualizować preferencje na poziomie par propozycji i nie może się wywrócić.

---

## 15. Ryzyka

1. **Szum wynikający ze słabego evidence**
   - ograniczany przez konserwatywne progi i słaby wpływ pojedynczych zdarzeń.

2. **Zbyt mocne karanie odrzuconych sugestii**
   - ograniczane przez silniejsze odrzucenia na poziomie par propozycji niż na poziomie cech.

3. **Nieczytelne zmiany confidence**
   - ograniczane przez strukturalny confidence breakdown i komendę CLI do inspekcji.

4. **Dryf magazynu preferencji**
   - ograniczany przez zapis surowych liczników i deterministyczne wyliczanie score.

---

## 16. Możliwe rozszerzenia w przyszłości (poza zakresem tego PRD)

Te elementy są jawnie poza zakresem tego PRD, ale powinny pozostać możliwe w kolejnych iteracjach:

- uczenie na treści plików,
- bogatsze modelowanie intencji taksonomii,
- undo / rollback dla wyuczonych preferencji,
- wygaszanie bardzo starych preferencji,
- eksport/import profili preferencji,
- lekki TUI/GUI do inspekcji preferencji.

---

## 17. Uwagi implementacyjne dla agenta kodującego

Celem **nie** jest budowa złożonego rule engine.

Celem jest zbudowanie **małej, lokalnej, wyjaśnialnej warstwy uczenia preferencji**, która z czasem poprawia jakość rankingu.

Priorytet implementacyjny:
1. trwałe repozytorium preferencji,
2. update-on-apply,
3. update-on-reject,
4. korekta score podczas tworzenia propozycji,
5. CLI `preferences`,
6. opcjonalny verbose confidence breakdown.

Gdy pojawiają się trade-offy, należy preferować:
- prostotę,
- explainability,
- kompatybilność wstecz,
- niski koszt runtime.

---

## 18. Definition of done

Funkcja jest ukończona, gdy:
- cały przepływ od review decision -> learned preference -> future ranking działa end-to-end,
- użytkownik może podejrzeć wyuczone preferencje z CLI,
- funkcja poprawia personalizację bez potrzeby ręcznego mapowania rozszerzeń,
- implementacja pozostaje lokalna, lekka i oparta o review.
