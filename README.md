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
```

Walidacja lokalna bez aktywnego Ollama:

```bash
uv run python -m synapsea run --skip-ai --source ~/Downloads --data-dir ./data
```

Tryb ciągłego monitoringu:

```bash
uv run python -m synapsea watch --source ~/Downloads --data-dir ./data --watch-interval 2
```

Przeglad propozycji review:

```bash
uv run python -m synapsea review --data-dir ./data
uv run python -m synapsea review --data-dir ./data --verbose
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
- Domyślny timeout żądania do Ollama wynosi `60` sekund.
- Domyślny budżet AI to `20` wywołań na cykl (`--ai-budget`).
- Domyślnie do AI trafiają maksymalnie `3` przykładowe pliki z klastra (`--ai-max-examples`).
- `watch` uruchamia pętlę monitoringu i przyjmuje `--watch-interval` (sekundy).
- `review` pokazuje rozszerzony kontekst (`target_path`, liczba kandydatów, skrót uzasadnienia), a `--verbose` pokazuje pełne uzasadnienie i podgląd plików.
- Kolejka review deduplikuje semantycznie podobne propozycje (np. warianty nazwy różniące się formatowaniem), nie tylko identyczne `cluster_id`.
- Lista review jest rankowana: najpierw `pending`, potem wyższy confidence i bogatszy kontekst (więcej plików kandydujących).
- Po uruchomieniu z aktywną warstwą AI pipeline zapisuje kandydatów klastrów do `candidate_clusters.json` oraz propozycje do `review_queue.json`.
- `run` działa inkrementalnie: przetwarza tylko pliki nowe lub zmodyfikowane od poprzedniego przebiegu i usuwa wpisy historii dla plików usuniętych.
- Pipeline utrzymuje `ai_proposal_cache.json` (cache odpowiedzi AI po fingerprint klastra) i `deferred_clusters.json` (odroczone klastry ponad budżet cyklu).
- `watch` startuje bez bootstrapowego przetwarzania istniejącego katalogu i reaguje na zmiany od momentu uruchomienia.
- Komendy `apply` i `reject` aktualizują status propozycji oraz synchronizują `taxonomy.json`.
- Skanowanie działa rekurencyjnie w monitorowanym katalogu.
- Pasywne uczenie zapisuje sygnały do `learning_signals.json`, a stan poprzedniego przebiegu do `snapshot.json`.
