# Screenshot Guide — AlphaGenome Explorer App
## For the 2-Hour Lesson (App Demo Segment)

Take all screenshots at full browser width (≥ 1280 px wide). Suggested tool:
browser built-in screenshot (F12 → screenshot icon) or Windows Snipping Tool (Win+Shift+S).

---

## Screenshot 1 — Home Page
**File name:** `01_home_page.png`
**What to show:** The full Home page including:
- Red "UNDER DEVELOPMENT" banner at top
- Dark navbar with all tab labels visible
- Hero section ("AlphaGenome Explorer")
- Getting-started steps (1, 2, 3)
- Four module cards (Sequence Prediction, Interval Prediction, Variant Analysis, ISM)
- Tips section

**How to get it:** Open app → click **Home** tab → scroll to top → full-page screenshot.

---

## Screenshot 2 — Settings Tab (Key Saved)
**File name:** `02_settings_api_key.png`
**What to show:** Settings tab with the green "Key set: ABCD••••••••WXYZ" confirmation
box visible.

**How to get it:** Click **Settings** tab → paste a valid API key → click **Save Key**
→ screenshot.

---

## Screenshot 3 — Interval Prediction Sidebar
**File name:** `03_interval_sidebar.png`
**What to show:** The left sidebar of the Interval Prediction module with:
- Gene symbol = `CYP2B6`
- "Gene annotations loaded" (green) status
- RNA_SEQ checked
- Right liver lobe selected
- 1 MB chosen

**How to get it:** Click **Interval Prediction** tab → set gene symbol to CYP2B6 →
click **Load gene annotations** (wait for success) → set output type to RNA_SEQ →
set tissue to Right liver lobe → screenshot (before running).

---

## Screenshot 4 — Interval Prediction Result Plot
**File name:** `04_interval_result_cyp2b6.png`
**What to show:** Full result including:
- Green "Interval: … | N transcript(s) extracted." status bar
- Transcript annotation row (gene model drawn at top)
- RNA_SEQ track below showing expression signal over the CYP2B6 locus

**How to get it:** After Screenshot 3, click **Run Prediction** → wait (10–60 s) →
screenshot the main panel.

---

## Screenshot 5 — Variant Analysis Sidebar
**File name:** `05_variant_sidebar.png`
**What to show:** Variant Analysis sidebar with:
- Chromosome = chr22
- Position = 36201698
- REF = A, ALT = C
- Output type = RNA Seq
- Colon Transverse selected
- "Also score the variant" checked
- "Overlay gene annotations" checked

**How to get it:** Click **Variant Analysis** tab → verify defaults match above →
screenshot sidebar before running.

---

## Screenshot 6 — Variant Analysis REF vs ALT Plot
**File name:** `06_variant_ref_alt_plot.png`
**What to show:**
- Green status bar (variant info)
- "REF vs ALT plot" tab active
- Overlaid grey (REF) and red (ALT) tracks
- Red vertical line at the variant position
- Transcript annotation at top

**How to get it:** After Screenshot 5, click **Run Analysis** → wait → ensure
"REF vs ALT plot" tab is active → screenshot.

---

## Screenshot 7 — Variant Scores Table
**File name:** `07_variant_scores_table.png`
**What to show:** The "Variant scores" tab with the sorted table of top 50 scores
(columns: track name, tissue, raw score, quantile score, etc.)

**How to get it:** Same run as Screenshot 6 → click **Variant scores** tab →
screenshot.

---

## Screenshot 8 — ISM Sidebar
**File name:** `08_ism_sidebar.png`
**What to show:** ISM sidebar with:
- Chromosome = chr20
- Centre position = 3753200
- Context window = 16 KB (recommended)
- ISM width = 256
- Output type = DNASE
- K562 (EFO:0002067) selected
- Aggregation = Diff mean (ALT − REF)
- Center mask width = 501

**How to get it:** Click **ISM Analysis** tab → verify/set defaults → screenshot
before running.

---

## Screenshot 9 — ISM Sequence Logo Result
**File name:** `09_ism_sequence_logo.png`
**What to show:**
- Green status bar (e.g. "768 variants scored | Region: chr20:… | Output: DNASE …")
- Sequence logo plot (tall coloured letters marking functionally important positions)
- Top 20 positions table below

**How to get it:** After Screenshot 8, click **Run ISM** → wait (several minutes) →
screenshot when complete.

---

## Screenshot 10 — Guide Page: Output Types
**File name:** `10_guide_output_types.png`
**What to show:** Guide page with "Output Types" tab active, showing the grid of coloured
cards (ATAC, CAGE, DNASE, etc.) with their Scoreable / Plot-only badges.

**How to get it:** Click **Guide** tab → "Output Types" tab selected → scroll to show
most cards → screenshot.

---

## Screenshot 11 — Guide Page: Tissues & Cell Types
**File name:** `11_guide_tissues.png`
**What to show:** Guide page with "Tissues & Cell Types" tab active, showing the full
table of 16 ontology terms with Tissue/Cell type/Cell line badges.

**How to get it:** Click **Guide** tab → click "Tissues & Cell Types" tab → screenshot.

---

## Screenshot 12 — Sequence Prediction (Optional / Intro slide)
**File name:** `12_sequence_prediction_gattaca.png`
**What to show:** Sequence Prediction module with "GATTACA" in the sequence box,
DNASE selected, Lung selected — either just the sidebar or a completed result.

**How to get it:** Click **Sequence Prediction** tab → defaults already show GATTACA →
run if you want a result, or just screenshot the empty sidebar for a conceptual intro.

---

## Folder structure suggestion

Place all screenshots in:
```
lesson_context/screenshots/
  01_home_page.png
  02_settings_api_key.png
  03_interval_sidebar.png
  04_interval_result_cyp2b6.png
  05_variant_sidebar.png
  06_variant_ref_alt_plot.png
  07_variant_scores_table.png
  08_ism_sidebar.png
  09_ism_sequence_logo.png
  10_guide_output_types.png
  11_guide_tissues.png
  12_sequence_prediction_gattaca.png (optional)
```

Then upload `app_context_for_claude.md` + all screenshots to Claude at the start of your
lesson session. Claude will use the context doc for conceptual questions and the
screenshots for visual/navigational questions.
