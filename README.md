# SupeRR Selector Season 2 — Pressure Performance Analytics

A client-side sports analytics platform and evaluation modeling codebase designed for the Rajasthan Royals (RR) SupeRR Selector competition. The model measures T20 player reliability under pressure by identifying athletes who consistently beat context expectation across match-leverage phases.

---

## Repository Contents (Source Code Only)

```text
├── analysis/                      # Python Analytical Pipeline & Modeling Scripts
│   ├── pipeline.py                # Win probability modeling & Pressure Index calculation
│   ├── robustness.py              # 24-scenario sensitivity & stability audits
│   ├── content.py                 # Mathematical and analytical text generation
│   ├── export.py / export2.py     # Derived results formatting pipelines
│   ├── build_excel.py / build_excel2.py   # Analytical workbook generators
│   ├── build_ppt_final.py / build_ppt_final2.py # Presentation generators
│   └── build_report.py / build_report2.py       # Methodology report generators
│
├── dashboard/                     # Client-Side Dashboard Web Application
│   ├── index.html                 # Main dashboard application interface
│   ├── source_code/
│   │   ├── app.js                 # UI engine, scrollspy, comparison tool, What-If calculator
│   │   └── vendor/
│   │       └── chart.umd.min.js   # Local Chart.js library (zero external API calls)
│   ├── styles/
│   │   └── style.css              # Rajasthan Royals theme styling & responsive layout
│   └── robots.txt                 # Search engine directives
│
├── requirements.txt               # Python package dependencies
└── README.md                      # Project documentation
```

> **Note on Data Confidentiality:** In strict compliance with competition submission guidelines, all raw delivery data packs, CSV match files, player photos, and generated submission documents (PDF, DOCX, XLSX, PPTX) have been intentionally excluded from this public source code repository.

---

## Analytical Methodology

### 1. Pressure Index (PI)
Pressure is evaluated ball-by-ball on a 0–100 scale:

$$\text{PI} = 100 \times \text{Balance} \times [0.30 + 0.70 \times \text{Stage}]$$

Where:
* **Balance:** Measures proximity to an even contest: $\text{Balance} = 1 - 2 \times |\text{WP} - 0.50|$, with $\text{WP}$ derived from a leak-free 5-fold cross-validated logistic regression model.
* **Stage:** Proportion of regulation deliveries elapsed ($\text{balls\_elapsed} / 240$).
* **High-Pressure Cutoff:** Top 25% of balls by PI per innings (1st Innings: $\text{PI} \ge 56.3$; Chase: $\text{PI} \ge 32.9$).

### 2. Player Scoring Formula
Approved multi-dimensional scoring model:

$$\text{Score} = 50 + 15 \times (0.40 \times Z_{\text{output}} + 0.20 \times Z_{\text{wickets}} + 0.20 \times Z_{\text{lift}} + 0.20 \times Z_{\text{consistency}})$$

Adjusted via Empirical Bayes shrinkage:

$$\text{Shrinkage Factor} = \frac{n}{n + 100}$$

---

## Local Setup & Execution

### 1. Running the Analysis Pipeline
Install the required analytical dependencies:
```bash
pip install -r requirements.txt
```

Run the core modeling pipeline:
```bash
cd analysis
python pipeline.py
python robustness.py
```

### 2. Running the Interactive Dashboard
The dashboard is a static, zero-backend web application. Serve it locally via any HTTP server:
```bash
cd dashboard
python -m http.server 8000
```
Open **`http://localhost:8000`** in any modern web browser.
