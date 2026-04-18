# Experiments

This folder contains experimental scripts and tests for the AI Notepad project.

## Purpose
- Testing new features
- Performance benchmarks
- API experiments
- Data analysis scripts

## Structure
Each experiment should be a self-contained script with a descriptive name:
- `01_vector_search_test.py` - Testing vector search functionality
- `02_ollama_models.py` - Comparing different AI models
- `03_db_performance.py` - Database performance tests

## Usage
```bash
# Run an experiment
cd experiments
python 01_vector_search_test.py

# Or run from project root with explicit path
python experiments/01_vector_search_test.py
```

## Notes
- These are NOT unit tests
- Scripts may be temporary and can be deleted
- Don't import from the main package unless necessary
- Use absolute imports when importing from the package
