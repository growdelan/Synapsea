## 1. Overview

**Synapsea** to AI-native aplikacja do zarządzania plikami, która nie tylko je kategoryzuje, ale **uczy się struktury danych użytkownika i dynamicznie ją rozwija**.

Zamiast statycznych folderów:

* system sam wykrywa wzorce,
* proponuje nowe kategorie,
* optymalizuje strukturę danych w czasie.

To nie jest file sorter.
To jest **self-evolving knowledge filesystem layer**.

---

## 2. Vision

> Synapsea uczy się, jak wygląda Twój osobisty porządek danych — i rozwija go razem z Tobą.

---

## 3. Core Principles

1. **AI jako warstwa interpretacji, nie wykonania**
2. **Brak wymuszonej interakcji użytkownika**
3. **Decyzje są audytowalne (review queue)**
4. **System uczy się z zachowania użytkownika**
5. **Lokalność i prywatność (Ollama + local processing)**

---

## 4. Key Features

### 4.1 Autonomous File Classification

* Monitorowanie folderu (np. `/downloads`)
* Automatyczne przypisywanie do kategorii
* Obsługa przez lokalny model (Ollama)

---

### 4.2 Feature Extraction Engine

System analizuje każdy plik i wyciąga:

* extension
* tokens z nazwy
* słowa kluczowe
* patterny (daty, wersje, numeracje)
* heurystyczne klasy (np. screenshot-like, invoice-like)

---

### 4.3 Pattern Detection Engine

Bez użycia AI:

* grupowanie po:

  * tokenach
  * rozszerzeniach
  * wzorcach nazw
* scoring klastrów

Output:
→ `candidate_cluster`

---

### 4.4 AI Interpretation Layer (Ollama)

Dla każdego `candidate_cluster`:

Model odpowiada:

* czy warto stworzyć kategorię
* jak ją nazwać
* uzasadnienie
* confidence

---

### 4.5 Review Queue (Human-in-the-loop)

System NIE zmienia struktury automatycznie.

Zamiast tego:

* zapisuje propozycje do `review_queue.json`

User może:

```bash
synapsea review
synapsea apply <id>
synapsea reject <id>
```

---

### 4.6 Self-Evolving Taxonomy

System:

* proponuje split kategorii
* proponuje merge kategorii
* sugeruje nowe podkategorie
* wykrywa martwe kategorie

---

### 4.7 Passive Learning

System uczy się z:

* ręcznych przeniesień plików
* rename
* cofania decyzji

---

## 5. System Architecture

### 5.1 Components

```
/core
  ├── scanner.py
  ├── classifier.py
  ├── feature_extractor.py
  ├── cluster_engine.py
  ├── evolution_engine.py
  ├── ollama_client.py
  ├── review_queue.py
  ├── taxonomy_engine.py

/data
  ├── taxonomy.json
  ├── review_queue.json
  ├── classification_log.db
```

---

### 5.2 Data Flow

1. Scan folder
2. Extract features
3. Classify file
4. Log decision
5. Detect patterns
6. Build clusters
7. Send cluster → Ollama
8. Generate proposal
9. Save to review queue

---

## 6. Data Structures

### 6.1 candidate_cluster

```json
{
  "cluster_id": "cluster_001",
  "parent_category": "images",
  "file_count": 89,
  "dominant_extensions": ["png", "jpg"],
  "top_tokens": ["screenshot", "zrzut"],
  "pattern_signals": {
    "has_date_ratio": 0.91,
    "pattern_similarity": 0.86
  },
  "example_files": ["Screenshot ..."],
  "candidate_files": ["/path/file.png"],
  "heuristic_score": 0.88
}
```

---

### 6.2 review_queue.json

```json
{
  "items": [
    {
      "id": "rev_001",
      "type": "create_category",
      "status": "pending",
      "confidence": 0.92,
      "parent_category": "images",
      "proposed_category": "screenshots",
      "target_path": "images/screenshots",
      "candidate_files": [],
      "reason": "Detected consistent naming pattern"
    }
  ]
}
```

---

### 6.3 taxonomy.json

```json
{
  "images": {
    "children": ["screenshots", "designs"],
    "status": "stable"
  }
}
```

---

## 7. CLI Interface

### Commands

```bash
synapsea run        # start daemon
synapsea review     # show suggestions
synapsea apply ID   # apply suggestion
synapsea reject ID  # reject suggestion
```

---

## 8. Non-Functional Requirements

### Performance

* działa lokalnie
* minimalne użycie RAM
* batch processing dla dużych folderów

### Privacy

* brak wysyłania danych poza lokalną maszynę
* Ollama local-only

### Reliability

* idempotent operations
* rollback-safe moves

---

## 9. MVP Scope

### Must Have

* file classification
* feature extraction
* basic clustering (keywords + extensions)
* Ollama integration
* review queue
* CLI

### Not in MVP

* GUI
* pełna automatyzacja zmian
* zaawansowane embeddings

---

## 10. Future Enhancements

* GUI (dashboard)
* embeddings clustering
* multi-folder intelligence
* cross-domain linking (files ↔ notes ↔ tasks)
* API integration (Notion, Drive, etc.)
* real-time streaming classification

---

## 11. Success Metrics

* % poprawnych klasyfikacji
* liczba zaakceptowanych propozycji
* liczba utworzonych kategorii
* redukcja chaosu (files in root)

---

## 12. Risks

| Risk                | Mitigation           |
| ------------------- | -------------------- |
| Over-clustering     | confidence threshold |
| Bad naming          | human review         |
| Performance issues  | batching             |
| Model inconsistency | strict prompts       |

---

## 13. Guiding Philosophy

Synapsea nie zarządza plikami.

Synapsea:

* obserwuje
* rozumie
* proponuje
* uczy się

---

## 14. Definition of Done (MVP)

✔ pliki są automatycznie klasyfikowane
✔ system wykrywa co najmniej 3 typy wzorców
✔ generowane są propozycje kategorii
✔ user może je zatwierdzić przez CLI
✔ system zapisuje historię decyzji

---

## 15. One-liner

**Synapsea to system, który zamienia chaos plików w ewoluującą strukturę wiedzy.**

---

