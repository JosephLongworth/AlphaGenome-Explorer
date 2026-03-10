"""
Shared constants, helpers, and caches for the AlphaGenome Shiny app.
"""
import os

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
# Ontology terms
# ---------------------------------------------------------------------------
ONTOLOGY_TERMS: dict[str, str] = {
    "UBERON:0002048": "Lung",
    "UBERON:0000955": "Brain",
    "UBERON:0002107": "Liver",
    "UBERON:0001114": "Right liver lobe",
    "UBERON:0001157": "Colon – Transverse",
    "UBERON:0000178": "Blood",
    "UBERON:0002367": "Prostate gland",
    "UBERON:0002113": "Kidney",
    "UBERON:0000948": "Heart muscle",
    "UBERON:0000310": "Breast",
    "UBERON:0001013": "Adipose tissue",
    "UBERON:0000945": "Stomach",
    "EFO:0002067": "K562 (leukaemia cell line)",
    "CL:0000084": "T cell",
    "CL:0000115": "Endothelial cell",
    "CL:0000047": "Neuroblast",
}

# choices dict suitable for ui.input_selectize / ui.input_checkbox_group
ONTOLOGY_CHOICES: dict[str, str] = {
    f"{term} – {name}": term for term, name in ONTOLOGY_TERMS.items()
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


def render_plot_safe(plot_fn):
    """
    Call plot_fn() which is expected to call plot_components.plot(...).
    Returns plt.gcf() so Shiny's @render.plot can capture the figure.
    """
    import matplotlib.pyplot as plt
    fig = plot_fn()
    return fig if fig is not None else plt.gcf()
