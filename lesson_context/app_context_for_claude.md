# AlphaGenome Explorer — App Context for Lesson Preparation

This document gives Claude full context about the **AlphaGenome Explorer** Shiny app
built by the Department of Immune and Inflammatory Diseases (DII) / Luxembourg Institute
of Health (LIH). It is intended to be uploaded to a Claude session so that Claude can
help facilitate or explain the 30-minute app demo portion of the AlphaGenome lesson.

---

## 1. What is AlphaGenome?

**AlphaGenome** is a foundation model from Google DeepMind that predicts hundreds of
genomic functional tracks (chromatin accessibility, gene expression, splicing signals,
TF binding, etc.) directly from raw DNA sequence.

- Input: DNA sequence of a fixed length (16 KB, 100 KB, 500 KB, or 1 MB)
- Output: predicted signal tracks for up to 10 assay types, filtered by tissue / cell type
- Access: via a REST API (API key required from alphagenomedocs.com)
- Supported organisms: Human (GRCh38/hg38) and Mouse (mm10)

---

## 2. The AlphaGenome Explorer App

**Purpose:** An interactive, no-code research interface that wraps the AlphaGenome API
into five prediction modules accessible through a web browser.

**Technology stack:**
- Shiny for Python (reactive web framework)
- Matplotlib (visualisation)
- alphagenome Python SDK

**How to run:**
```
shiny run shiny_app/app.py --reload
```

**Navigation:** A top navbar (dark, #1a252f) with these tabs:
`Home | Sequence Prediction | Interval Prediction | Variant Analysis | ISM Analysis | Guide | Settings`

A red development banner reads:
> UNDER DEVELOPMENT — Department of Immune and Inflammatory Diseases (DII) | Luxembourg Institute of Health (LIH)

---

## 3. First-Time Setup (Settings Tab)

Before any prediction can run:
1. Click **Settings** (top-right of the navbar)
2. Paste an AlphaGenome API key into the password field
3. Click **Save Key**
4. A green confirmation box shows the masked key (first 4 + last 4 characters)

The key is stored in memory only for the session. It can also be pre-loaded via the
`ALPHAGENOME_API_KEY` environment variable.

---

## 4. Home Page

The Home page shows:
- A hero banner with a link to alphagenomedocs.com
- Three numbered getting-started steps (Set key → Choose module → Configure & run)
- Four module overview cards (one per prediction module)
- Tips for using ontology terms, sequence lengths, and quantile scores

---

## 5. Module 1 — Sequence Prediction

**Purpose:** Predict genomic tracks from an arbitrary DNA string (not anchored to the
reference genome). Useful for synthetic sequences, mutagenesis experiments, or
sequences from any organism.

**Sidebar inputs:**

| Input | Default | Notes |
|---|---|---|
| DNA Sequence (textarea) | `GATTACA` | A, T, G, C, N characters; centre-padded with N's |
| Pad to length | 1 MB | 16 KB / 100 KB / 500 KB / 1 MB |
| Organism | Human | Human or Mouse |
| Output types (checkboxes) | DNASE | Any of 10 assay types |
| Tissues / cell types (multi-select) | Lung (UBERON:0002048) | Ontology CURIEs |
| Custom ontology term | — | Free-text CURIE override |
| **Run Prediction** button | — | Triggers the API call |

**What happens on Run:**
1. Sequence is upper-cased and centre-padded with N's to the chosen length
2. API call: `model.predict_sequence(sequence, requested_outputs, ontology_terms, organism)`
3. Output: a matplotlib track plot + metadata table (track names, tissue labels)

**Teaching note:** Use the default `GATTACA` + DNASE + Lung to give a fast demo with no
meaningful biology — it shows the mechanics without needing a real gene.

---

## 6. Module 2 — Interval Prediction

**Purpose:** Make predictions for a real chromosomal region from GRCh38/hg38. Overlays
MANE-select transcript annotations. Supports gene-symbol lookup or manual coordinates.

**Sidebar inputs:**

| Input | Default | Notes |
|---|---|---|
| Input mode | Gene symbol | Gene symbol OR manual interval |
| Gene symbol (HGNC) | `CYP2B6` | Looked up in GENCODE v46 annotation |
| Load gene annotations button | — | Downloads ~100 MB GTF on first use |
| Manual: chromosome / start / end | chr19 / 40,991,281 / 41,018,398 | |
| Resize interval to | 1 MB | Centred on the interval midpoint |
| Organism | Human | |
| Output types (checkboxes) | RNA_SEQ | |
| Tissues / cell types | Right liver lobe (UBERON:0001114) | |
| Custom ontology term | — | |
| Overlay transcript annotations | ✓ checked | MANE-select transcripts |
| **Run Prediction** button | — | |

**What happens on Run:**
1. If gene mode: looks up gene span in GENCODE annotation
2. Interval is resized to the chosen sequence length (centred on midpoint)
3. API call: `model.predict_interval(interval, requested_outputs, ontology_terms, organism)`
4. If transcripts enabled and GTF loaded: extracts MANE-select transcripts for the region
5. Output: matplotlib plot with transcript track on top + signal tracks below + metadata table

**Teaching note:** CYP2B6 in right liver lobe is a strong example — it is a highly
expressed liver drug-metabolism gene, so RNA_SEQ signal is clearly visible.

---

## 7. Module 3 — Variant Analysis

**Purpose:** Predict the functional effect of a single nucleotide variant (SNV) by
comparing REF vs ALT allele predictions side-by-side. Optionally runs a recommended
quantile-calibrated scorer.

**Sidebar inputs:**

| Input | Default | Notes |
|---|---|---|
| Chromosome | chr22 | |
| Position (1-based) | 36,201,698 | VCF-style 1-based coordinate |
| REF allele | A | Reference base at that position |
| ALT allele | C | Alternate base to test |
| Sequence length | 1 MB | Window centred on the variant |
| Output type | RNA_SEQ | Only "scoreable" types listed (ATAC/CAGE/DNASE/RNA_SEQ/CHIP_HISTONE/CHIP_TF) |
| Tissues / cell types | Colon Transverse (UBERON:0001157) | |
| Custom ontology term | — | |
| Plot window (zoom) | 16 KB | Controls how much of the result is displayed |
| Also score the variant | ✓ checked | Runs recommended scorer (extra API call) |
| Overlay gene annotations | ✓ checked | Auto-downloads GTF on first run |
| **Run Analysis** button | — | |

**Main panel tabs:**
- **REF vs ALT plot** — overlaid tracks (REF=grey, ALT=red) + variant position marker + transcript annotations
- **Variant scores** — table of top 50 variants sorted by |raw_score|; shows which track / tissue is most affected

**API calls made:**
1. `model.predict_variant(interval, variant, requested_outputs, ontology_terms)` — produces REF and ALT output objects
2. `model.score_variant(interval, variant, variant_scorers=[scorer])` → `variant_scorers.tidy_scores(...)` — produces a ranked DataFrame

**Teaching note:** This is the most biologically rich demo. A variant that disrupts a
regulatory element will show a clear REF/ALT divergence in the track. The scores table
ranks every assay-track combination by effect size, making it easy to identify the most
impacted tissues.

---

## 8. Module 4 — In Silico Mutagenesis (ISM)

**Purpose:** Systematically substitute every base in a target window to a different
nucleotide and score the functional effect. Results shown as a sequence logo where tall
letters mark functionally important positions.

**Warning shown in the UI:**
> ISM can be slow – each batch of ~32 variants requires a separate API call.
> Keep the ISM region small (≤ 256 bp) and context window short (16 KB) to minimise run time.

**Sidebar inputs:**

| Input | Default | Notes |
|---|---|---|
| Chromosome | chr20 | |
| Centre position (bp) | 3,753,200 | Midpoint of context window and ISM region |
| Context window | 16 KB (recommended) | 16 KB or 100 KB only |
| ISM width (bp) | 256 | Width of the mutation scan window; max 1000 bp |
| Output type | DNASE | ATAC/CAGE/DNASE/RNA_SEQ/CHIP_HISTONE/CHIP_TF |
| Tissue / cell type (single) | K562 (EFO:0002067) | One ontology term only |
| Custom ontology term | — | |
| Aggregation | Diff mean (ALT−REF) | Diff mean / Log fold change / Abs diff mean |
| Center mask width (bp) | 501 | CenterMaskScorer sums signal within this window |
| **Run ISM** button | — | |

**What happens on Run:**
1. Builds a context interval (16 KB centred on the chosen position)
2. Builds an ISM interval (256 bp centred on the same point)
3. Creates a `CenterMaskScorer` with the chosen output type and aggregation
4. API call: `model.score_ism_variants(interval=context, ism_interval=ism, variant_scorers=[scorer])`
5. Extracts per-variant scalar scores (one per ontology term match)
6. Builds a (n_positions × 4) ISM matrix and plots it as a sequence logo

**Output panels:**
- **Sequence logo** — tall letters = important positions; letter identity shows which mutation has the strongest effect
- **Top 20 most influential positions** — table with genomic coordinates, best mutant base, and max |score|

**Teaching note:** ISM is the most interpretability-focused module. It answers "which
specific bases in a regulatory element matter?". Great for showing how the model learns
sequence grammar (e.g., TF binding motifs).

---

## 9. Guide Page

A two-tab reference page built into the app:

### Tab 1: Output Types
Cards (3-per-row) for all 10 output types:

| Code | Full name | Category | Scoreable? |
|---|---|---|---|
| ATAC | ATAC-seq | Chromatin accessibility | Yes |
| CAGE | Cap Analysis of Gene Expression | Transcription start sites | Yes |
| DNASE | DNase-seq | Chromatin accessibility | Yes |
| RNA_SEQ | RNA-seq | Gene expression | Yes |
| CHIP_HISTONE | ChIP-seq – Histone marks | Epigenomics | Yes |
| CHIP_TF | ChIP-seq – Transcription factors | Epigenomics | Yes |
| SPLICE_SITES | Splice sites | RNA splicing | No |
| SPLICE_SITE_USAGE | Splice site usage | RNA splicing | No |
| SPLICE_JUNCTIONS | Splice junctions | RNA splicing | No |
| PROCAP | PRO-cap | Transcription start sites | No |

"Scoreable" means the output type can be used with variant scorers in Variant Analysis
and ISM. Plot-only types can be predicted and visualised but have no built-in scorer.

### Tab 2: Tissues & Cell Types
A searchable table of 16 supported ontology terms:

| Ontology ID | Name | Category |
|---|---|---|
| UBERON:0002048 | Lung | Tissue / organ |
| UBERON:0000955 | Brain | Tissue / organ |
| UBERON:0002107 | Liver | Tissue / organ |
| UBERON:0001114 | Right liver lobe | Tissue / organ |
| UBERON:0001157 | Colon – Transverse | Tissue / organ |
| UBERON:0000178 | Blood | Tissue / organ |
| UBERON:0002367 | Prostate gland | Tissue / organ |
| UBERON:0002113 | Kidney | Tissue / organ |
| UBERON:0000948 | Heart muscle | Tissue / organ |
| UBERON:0000310 | Breast | Tissue / organ |
| UBERON:0001013 | Adipose tissue | Tissue / organ |
| UBERON:0000945 | Stomach | Tissue / organ |
| EFO:0002067 | K562 (leukaemia cell line) | Cell line |
| CL:0000084 | T cell | Cell type |
| CL:0000115 | Endothelial cell | Cell type |
| CL:0000047 | Neuroblast | Cell type |

Custom CURIEs can be typed directly in any module's "Custom ontology term" field.

---

## 10. Architecture Summary (for technical students)

```
app.py                  ← Entry point; page_navbar + shared API key reactive.Value
shared.py               ← Constants, caches, get_model(), get_gtf(), help_icon()
modules/landing.py      ← Home page (static)
modules/sequence_predict.py  ← predict_sequence()
modules/interval_predict.py  ← predict_interval() + TranscriptExtractor
modules/variant_predict.py   ← predict_variant() + score_variant()
modules/ism_analysis.py      ← score_ism_variants() + ism.ism_matrix()
modules/guide.py        ← Reference cards; no API calls
```

**Key design patterns:**
- Each module is a Shiny module (`@module.ui` + `@module.server`) for isolation
- API key passed as `api_key_rv` (a `reactive.Value`) from `app.py` into every module server
- Model instances cached in `_model_cache` (dict keyed by API key string) — no repeated initialisation
- GTF annotation cached in `_gtf_cache` — downloaded once from GCS (~100 MB, hg38 GENCODE v46)
- All plots rendered by `alphagenome.visualization.plot_components.plot()`
- `help_icon()` adds ℹ tooltip icons to every sidebar label

---

## 11. Suggested Lesson Flow (30-min App Demo)

| Time | Activity |
|---|---|
| 0–3 min | Open app, show Home page, explain the 4 modules and the Settings tab |
| 3–6 min | Settings: paste API key, show green confirmation |
| 6–13 min | **Interval Prediction**: CYP2B6, RNA_SEQ, right liver lobe, 1 MB — show gene track + transcript overlay |
| 13–20 min | **Variant Analysis**: chr22:36201698 A→C, RNA_SEQ, colon — show REF/ALT plot and scores table |
| 20–26 min | **ISM Analysis**: chr20:3753200, DNASE, K562, 256 bp — show sequence logo, discuss motif interpretation |
| 26–30 min | Guide page: walk through output type cards; Q&A |

**Sequence Prediction** (GATTACA example) can be shown briefly at any point as a
conceptual intro to how the model takes raw DNA — it requires no GTF loading.

---

## 12. Common Student Questions

**Q: Why does the first Interval Prediction take longer?**
A: The GENCODE GTF annotation (~100 MB) is downloaded from Google Cloud Storage on the
first click of "Load gene annotations". Subsequent runs use the in-memory cache.

**Q: What does "1 MB sequence length" mean?**
A: The model always receives a fixed-length DNA input. The chosen interval is resized
(expanded or contracted, keeping the midpoint fixed) to exactly 1 MB before being sent
to the API.

**Q: Why are some output types not available in Variant Analysis?**
A: Only "scoreable" output types (ATAC, CAGE, DNASE, RNA_SEQ, CHIP_HISTONE, CHIP_TF)
have recommended variant scorer configurations built into the SDK. The splicing and
PRO-cap tracks can be predicted but their statistical scoring is not yet standardised.

**Q: What is a quantile score?**
A: After computing a raw effect size, the scorer converts it to a quantile (0–1) relative
to a background distribution of benign variants. This makes scores comparable across
different assay types and tissues.

**Q: Can I use my own coordinates if they're not in hg38?**
A: The reference genome coordinates must match the organism selected. For Mouse, use mm10
coordinates. The Sequence Prediction module does not require reference coordinates at all.

**Q: What does ISM tell us that a single variant analysis doesn't?**
A: ISM exhaustively scans all positions simultaneously, revealing the full sequence grammar
of a regulatory element — equivalent to in vitro saturation mutagenesis but fully in silico.
