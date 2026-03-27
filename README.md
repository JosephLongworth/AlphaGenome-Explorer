# AlphaGenome Explorer

An interactive web application for genomic functional predictions powered by the [AlphaGenome API](https://www.alphagenomedocs.com) (Google DeepMind). Built with [Shiny for Python](https://shiny.posit.co/py/), AlphaGenome Explorer lets researchers explore hundreds of genomic regulatory tracks directly from DNA sequences — no coding required.

Developed by the **Department of Immune and Inflammatory Diseases (DII)** at the **Luxembourg Institute of Health (LIH)**.

---

## Features

| Module | Description |
|---|---|
| **Sequence Prediction** | Predict regulatory tracks from arbitrary DNA sequences (not reference-anchored) |
| **Interval Prediction** | Predict tracks for genomic intervals on hg38 or mm10, with gene lookup and transcript annotation |
| **Variant Analysis** | Compare REF vs. ALT allele predictions for single SNVs with quantile-calibrated scoring |
| **ISM Analysis** | In silico mutagenesis — exhaustively mutate bases in a target window and visualize as a sequence logo |
| **Contact Maps** | Predict Hi-C style 3D chromatin contact maps |
| **Guide** | Searchable reference for all output types and supported tissue/cell types |

Supported genomes: **GRCh38/hg38** (human) and **mm10** (mouse).

---

## Requirements

- Python 3.11+
- An AlphaGenome API key — obtain one at [alphagenomedocs.com](https://www.alphagenomedocs.com)

---

## Getting Started

### Local Development

1. **Clone the repository**

   ```bash
   git clone https://github.com/JosephLongworth/AlphaGenomePortal.git
   cd AlphaGenomePortal
   ```

2. **Install dependencies**

   ```bash
   pip install -r shiny_app/requirements.txt
   ```

3. **Run the app**

   ```bash
   shiny run shiny_app/app.py --reload
   ```

   The app will be available at `http://localhost:8000`.

4. **Enter your API key** via the Settings tab in the top-right corner of the navbar.

   Alternatively, set it as an environment variable before running:

   ```bash
   export ALPHAGENOME_API_KEY="your-key-here"
   ```

### Docker

```bash
docker-compose up --build
```

The app will be available at `http://localhost:8080`.

---

## Project Structure

```
alphagenome/
├── shiny_app/
│   ├── app.py                        # Main entry point
│   ├── shared.py                     # Shared constants, caches, and helpers
│   ├── requirements.txt              # Python dependencies
│   ├── data/
│   │   └── Supplementary_Tables.xlsx # Tissue/cell-type ontology metadata
│   └── modules/
│       ├── landing.py                # Home page
│       ├── sequence_predict.py       # Sequence prediction
│       ├── interval_predict.py       # Interval prediction
│       ├── variant_predict.py        # Variant analysis
│       ├── ism_analysis.py           # In silico mutagenesis
│       ├── contact_maps.py           # Contact maps
│       └── guide.py                  # Reference guide
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Notes

- On first use, GENCODE v46 GTF annotation (~100 MB) is downloaded from Google Cloud Storage and cached in memory.
- Model instances are cached per API key to avoid repeated initialization overhead.
- This application is under active development.

---

## Contact

Luxembourg Institute of Health — Department of Immune and Inflammatory Diseases (DII)
API documentation: [alphagenomedocs.com](https://www.alphagenomedocs.com)
