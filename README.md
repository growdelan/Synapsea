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
```

Walidacja lokalna bez aktywnego Ollama:

```bash
uv run python -m synapsea run --skip-ai --source ~/Downloads --data-dir ./data
```

Przeglad propozycji review:

```bash
uv run python -m synapsea review --data-dir ./data
```

Zatwierdzenie lub odrzucenie propozycji:

```bash
uv run python -m synapsea apply rev_001 --data-dir ./data
uv run python -m synapsea reject rev_002 --data-dir ./data
```

## Konfiguracja
- Domyślnie aplikacja analizuje `~/Downloads`.
- Dane aplikacji są zapisywane w katalogu `./data`.
- Domyślnie interpretacja AI korzysta z lokalnego endpointu `http://localhost:11434/api/generate` i modelu `llama3.2`.
- Po uruchomieniu z aktywną warstwą AI pipeline zapisuje kandydatów klastrów do `candidate_clusters.json` oraz propozycje do `review_queue.json`.
- Komendy `apply` i `reject` aktualizują status propozycji oraz synchronizują `taxonomy.json`.
- Skanowanie działa rekurencyjnie w monitorowanym katalogu.
- Pasywne uczenie zapisuje sygnały do `learning_signals.json`, a stan poprzedniego przebiegu do `snapshot.json`.
