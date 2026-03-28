# Synapsea
Synapsea to system, który zamienia chaos plików w ewoluującą strukturę wiedzy.

## Uruchamianie
Podstawowa komenda uruchomienia:

```bash
uv run python -m synapsea run
```

Przydatne opcje podczas lokalnej pracy:

```bash
uv run python -m synapsea run --source ~/Downloads --data-dir ./data
uv run python -m synapsea run --source ~/Downloads --data-dir ./data --ai-budget 10 --ai-max-examples 2
uv run python -m synapsea run --source ~/Downloads --data-dir ./data --ollama-model llama3.1:8b
```

Walidacja lokalna bez aktywnego Ollama:

```bash
uv run python -m synapsea run --skip-ai --source ~/Downloads --data-dir ./data
```

Tryb ciągłego monitoringu:

```bash
uv run python -m synapsea watch --source ~/Downloads --data-dir ./data --watch-interval 2
uv run python -m synapsea watch --source ~/Downloads --data-dir ./data --watch-interval 2 --ollama-model qwen2.5:7b
```

Terminalowy interfejs TUI:

```bash
uv run python -m synapsea tui
uv run python -m synapsea tui --source ~/Downloads --data-dir ./data --skip-ai
uv run python -m synapsea tui --ollama-model llama3.1:8b --ai-budget 5 --ai-max-examples 2
```

Przeglad propozycji review:

```bash
uv run python -m synapsea review --data-dir ./data
uv run python -m synapsea review --data-dir ./data --verbose
uv run python -m synapsea review --data-dir ./data --all-statuses
```

Inspekcja wyuczonych preferencji:

```bash
uv run python -m synapsea preferences --data-dir ./data
uv run python -m synapsea preferences --data-dir ./data --verbose --limit 20
```

Zatwierdzenie lub odrzucenie propozycji:

```bash
uv run python -m synapsea apply rev_001 --data-dir ./data
uv run python -m synapsea reject rev_002 --data-dir ./data
```

## Konfiguracja
- Domyślnie aplikacja analizuje `~/Downloads`.
- Dane aplikacji są zapisywane w katalogu `./data`.
- Domyślnie interpretacja AI korzysta z lokalnego endpointu `http://localhost:11434/api/generate` i modelu `gemma3:4b-it-qat`.
- Komendy `run` i `watch` wspierają `--ollama-model`, aby wskazać model dla bieżącego uruchomienia.
- Komenda `tui` uruchamia terminalowy frontend Textual i przyjmuje ten sam bazowy zestaw opcji runtime co `run`.
- TUI startuje na dashboardzie, pozwala uruchomić `run now` lub `run with options` i przejść do ekranu review.
- Ekran review wspiera multi-select, batch `apply/reject`, filtr tekstowy, sortowanie po confidence i liczbie plików oraz modal pełnych szczegółów.
- Batch `apply` w TUI pokazuje ostrzeżenie o realnych operacjach na plikach i raport zbiorczy po zakończeniu.
- Domyślny timeout żądania do Ollama wynosi `60` sekund.
- Domyślny budżet AI to `20` wywołań na cykl (`--ai-budget`).
- Domyślnie do AI trafiają maksymalnie `3` przykładowe pliki z klastra (`--ai-max-examples`).
- `watch` uruchamia pętlę monitoringu i przyjmuje `--watch-interval` (sekundy).
- `review` domyślnie pokazuje tylko pozycje `pending`.
- `review --all-statuses` pokazuje także pozycje `applied` i `rejected`.
- `review` pokazuje zwięzły, stały format: `id`, `status`, `parent_category`, `proposed_category`, `confidence`, `target_path`, `candidate_count`.
- Komenda `preferences` pokazuje top wyuczonych preferencji (pozytywnych i negatywnych) dla par propozycji oraz mapowań token/heurystyka.
- Kolejka review deduplikuje semantycznie podobne propozycje (np. warianty nazwy różniące się formatowaniem), nie tylko identyczne `cluster_id`.
- Lista review jest rankowana: najpierw `pending`, potem wyższy confidence i bogatszy kontekst (więcej plików kandydujących).
- Po uruchomieniu z aktywną warstwą AI pipeline zapisuje kandydatów klastrów do `candidate_clusters.json` oraz propozycje do `review_queue.json`.
- `run` działa inkrementalnie: przetwarza tylko pliki nowe lub zmodyfikowane od poprzedniego przebiegu i usuwa wpisy historii dla plików usuniętych.
- Pipeline utrzymuje `ai_proposal_cache.json` (cache odpowiedzi AI po fingerprint klastra) i `deferred_clusters.json` (odroczone klastry ponad budżet cyklu).
- `watch` startuje bez bootstrapowego przetwarzania istniejącego katalogu i reaguje na zmiany od momentu uruchomienia.
- Komenda `apply` aktualizuje status propozycji, synchronizuje `taxonomy.json` i wykonuje przeniesienie plików `candidate_files` do docelowej sciezki kategorii.
- Podczas `apply` kolizje nazw sa obslugiwane polityka `skip` (brak nadpisywania), a wynik komendy raportuje `moved`, `skipped` i `errors`.
- Komenda `reject` aktualizuje status propozycji bez operacji na plikach.
- Skanowanie działa rekurencyjnie w monitorowanym katalogu.
- Skanowanie ignoruje ukryte pliki i katalogi (np. `.DS_Store`), aby ograniczyć fałszywe delty.
- Pasywne uczenie zapisuje sygnały do `learning_signals.json`, a stan poprzedniego przebiegu do `snapshot.json`.
