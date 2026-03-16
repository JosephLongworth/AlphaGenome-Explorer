"""
Shared constants, helpers, and caches for the AlphaGenome Shiny app.
"""
import os
from shiny import ui

# ---------------------------------------------------------------------------
# Default API key – read from environment variable if available
# ---------------------------------------------------------------------------
DEFAULT_API_KEY = os.environ.get("ALPHAGENOME_API_KEY", "")

# ---------------------------------------------------------------------------
# Module-level caches (persist for the lifetime of the Python process)
# ---------------------------------------------------------------------------
_model_cache: dict = {}
_gtf_cache: dict = {}

# ---------------------------------------------------------------------------
# Ontology terms – loaded from supplementary table at startup
# ---------------------------------------------------------------------------

def _load_ontology_data():
    """
    Parse Suppl Table 2 from the bundled Excel file and return:
      - terms:       {curie: biosample_name}  (human tracks only, for selectize)
      - output_types:{curie: [output_type, …]} (human tracks only)
      - guide_rows:  list of dicts with curie, name, organisms, output_types
                     covering both human and mouse
    Falls back to minimal hard-coded data if the file is missing.
    """
    from pathlib import Path
    import pandas as pd

    xlsx = Path(__file__).parent / "data" / "Supplementary_Tables.xlsx"
    if not xlsx.exists():
        fallback = {
            "UBERON:0002048": "Lung",
            "UBERON:0000955": "Brain",
            "UBERON:0002107": "Liver",
            "UBERON:0000178": "Blood",
            "EFO:0002067":    "K562 (leukaemia cell line)",
            "CL:0000084":     "T cell",
        }
        guide = [
            {"curie": k, "name": v, "organisms": ["Human"], "output_types": []}
            for k, v in fallback.items()
        ]
        return fallback, {k: [] for k in fallback}, guide

    df = pd.read_excel(
        xlsx,
        sheet_name="Suppl Table 2 Track metadata (f",
        usecols=["organism", "ontology_curie", "biosample_name", "output_type"],
    ).dropna(subset=["ontology_curie"])

    # ── Human-only dicts for the selectize inputs ────────────────────────────
    h = df[df["organism"] == "human"]
    terms: dict[str, str] = {}
    output_types: dict[str, list[str]] = {}
    for curie, grp in h.groupby("ontology_curie"):
        terms[curie] = grp["biosample_name"].iloc[0]
        output_types[curie] = sorted(grp["output_type"].unique().tolist())

    # ── All-organism rows for the Guide table ────────────────────────────────
    guide_rows: list[dict] = []
    for curie, grp in df.groupby("ontology_curie"):
        orgs = sorted({o.capitalize() for o in grp["organism"].unique()})
        h_grp = grp[grp["organism"] == "human"]
        name = h_grp["biosample_name"].iloc[0] if len(h_grp) else grp["biosample_name"].iloc[0]
        ots = sorted(grp["output_type"].unique().tolist())
        guide_rows.append({"curie": curie, "name": name, "organisms": orgs, "output_types": ots})

    return terms, output_types, guide_rows


ONTOLOGY_TERMS: dict[str, str]
ONTOLOGY_OUTPUT_TYPES: dict[str, list[str]]
GUIDE_TABLE_ROWS: list[dict]
ONTOLOGY_TERMS, ONTOLOGY_OUTPUT_TYPES, GUIDE_TABLE_ROWS = _load_ontology_data()

# choices dict suitable for ui.input_selectize / ui.input_checkbox_group
ONTOLOGY_CHOICES: dict[str, str] = {
    term: f"{term} – {name}" for term, name in ONTOLOGY_TERMS.items()
}

# ---------------------------------------------------------------------------
# Supported output types
# ---------------------------------------------------------------------------
ALL_OUTPUT_TYPES = [
    "ATAC",
    "CAGE",
    "DNASE",
    "RNA_SEQ",
    "CHIP_HISTONE",
    "CHIP_TF",
    "SPLICE_SITES",
    "SPLICE_SITE_USAGE",
    "SPLICE_JUNCTIONS",
    "PROCAP",
]

# Output types supported by the recommended variant scorers
SCOREABLE_OUTPUT_TYPES = ["ATAC", "CAGE", "DNASE", "RNA_SEQ", "CHIP_HISTONE", "CHIP_TF"]

# Sequence length options  {display label: dna_client attribute name}
SEQUENCE_LENGTH_OPTIONS: dict[str, str] = {
    "16 KB": "SEQUENCE_LENGTH_16KB",
    "100 KB": "SEQUENCE_LENGTH_100KB",
    "500 KB": "SEQUENCE_LENGTH_500KB",
    "1 MB": "SEQUENCE_LENGTH_1MB",
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_model(api_key: str):
    """Return a cached dna_client model for *api_key*, creating it if necessary."""
    if api_key not in _model_cache:
        from alphagenome.models import dna_client  # deferred to avoid import cost
        _model_cache[api_key] = dna_client.create(api_key)
    return _model_cache[api_key]


def get_gtf():
    """Return (gtf DataFrame, TranscriptExtractor), loading from GCS on first call."""
    if "gtf" not in _gtf_cache:
        import pandas as pd
        from alphagenome.data import gene_annotation
        from alphagenome.data import transcript as transcript_utils

        gtf = pd.read_feather(
            "https://storage.googleapis.com/alphagenome/reference/gencode/"
            "hg38/gencode.v46.annotation.gtf.gz.feather"
        )
        gtf_tx = gene_annotation.filter_protein_coding(gtf)
        gtf_tx = gene_annotation.filter_to_mane_select_transcript(gtf_tx)
        tx_extractor = transcript_utils.TranscriptExtractor(gtf_tx)
        _gtf_cache["gtf"] = gtf
        _gtf_cache["transcript_extractor"] = tx_extractor

    return _gtf_cache["gtf"], _gtf_cache["transcript_extractor"]


def get_track_data(output, output_type_name: str):
    """Return the TrackData attribute on *output* for *output_type_name* (e.g. 'RNA_SEQ')."""
    return getattr(output, output_type_name.lower(), None)


def help_icon(tooltip_text: str):
    """Return a small ℹ icon with a Shiny tooltip shown on hover."""
    return ui.tooltip(
        ui.tags.span(
            " ℹ",
            style="cursor: help; color: #6c757d; font-size: 0.8em;",
        ),
        tooltip_text,
        placement="right",
    )


def render_plot_safe(plot_fn):
    """
    Call plot_fn() which is expected to call plot_components.plot(...).
    Returns plt.gcf() so Shiny's @render.plot can capture the figure.
    """
    import matplotlib.pyplot as plt
    fig = plot_fn()
    return fig if fig is not None else plt.gcf()
