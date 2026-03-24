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

## Konfiguracja
- Domyślnie aplikacja analizuje `~/Downloads`.
- Dane aplikacji są zapisywane w katalogu `./data`.
