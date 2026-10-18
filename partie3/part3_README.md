# Reproducibility

This document explains how to reproduce all results (tables and figures) of Part 3.

## Requirements

- Python **3.10 to 3.13**
- `pip`
- The files `part3_requirements.txt` and `part3_acceptability.ipynb`

## Setup

### 1. Create a virtual environment

```bash
python -m venv venv3
```

### 2. Activate it

**Linux / macOS:**

```bash
source venv3/bin/activate
```

**Windows:**

```bash
venv3\Scripts\Activate.ps1
```


### 3. Install the dependencies

```bash
pip install -r part3_requirements.txt
```

### 4. Launch the notebook

```bash
jupyter lab part3_acceptability.ipynb
```

## Running the experiments

Run **all cells of `part3_acceptability.ipynb` from top to bottom.**


## Determinism

Random seeds are fixed in the `SEEDS` variable: **2026, 2027, 2028, 2029, 2030**.
Every experiment is run once per seed, so results are reproducible across runs.

## Outputs

All tables and figures are saved to the `results/` directory.
