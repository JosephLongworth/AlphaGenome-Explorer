"""
Guide page – reference for output types and supported tissues / cell types.
"""
from shiny import module, ui, render

from shared import ONTOLOGY_TERMS


# ---------------------------------------------------------------------------
# Output type reference data
# ---------------------------------------------------------------------------

# Category → (border colour, Bootstrap text-colour class, emoji icon)
_CATEGORY_STYLE = {
    "Chromatin accessibility": ("#0d6efd", "text-primary",   "🔓"),
    "Transcription start sites": ("#fd7e14", "text-warning", "📍"),
    "Gene expression":           ("#198754", "text-success", "📈"),
    "Epigenomics":               ("#6f42c1", "text-purple",  "🏷"),
    "RNA splicing":              ("#dc3545", "text-danger",  "✂"),
}

OUTPUT_TYPE_INFO = [
    {
        "name": "ATAC",
        "full_name": "ATAC-seq",
        "category": "Chromatin accessibility",
        "tagline": "Maps open chromatin — peaks mark active regulatory elements.",
        "bullets": [
            "Uses Tn5 transposase to cut accessible (nucleosome-free) DNA",
            "Peaks at promoters, enhancers, and insulators",
            "Good first choice for identifying cis-regulatory elements",
        ],
        "scoreable": True,
    },
    {
        "name": "CAGE",
        "full_name": "Cap Analysis of Gene Expression",
        "category": "Transcription start sites",
        "tagline": "Pinpoints where transcription begins with base-pair resolution.",
        "bullets": [
            "Captures 5′ capped RNA ends → precise TSS positions",
            "Sharp peaks directly reflect promoter activity",
            "Tissue-specific TSS usage reveals alternative promoters",
        ],
        "scoreable": True,
    },
    {
        "name": "DNASE",
        "full_name": "DNase-seq",
        "category": "Chromatin accessibility",
        "tagline": "Similar to ATAC — open chromatin via DNase I sensitivity.",
        "bullets": [
            "DNase I preferentially cleaves accessible chromatin",
            "Complementary to ATAC; tracks are often concordant",
            "Widely used in ENCODE; many tissue reference datasets",
        ],
        "scoreable": True,
    },
    {
        "name": "RNA_SEQ",
        "full_name": "RNA-seq",
        "category": "Gene expression",
        "tagline": "Measures how strongly each gene is expressed.",
        "bullets": [
            "Reflects steady-state spliced mRNA abundance",
            "High signal over gene bodies = active transcription",
            "Best for tissue-specific expression comparisons",
        ],
        "scoreable": True,
    },
    {
        "name": "CHIP_HISTONE",
        "full_name": "ChIP-seq – Histone marks",
        "category": "Epigenomics",
        "tagline": "Histone modifications that label active and repressed regions.",
        "bullets": [
            "H3K27ac / H3K4me3 → active enhancers / promoters",
            "H3K27me3 → Polycomb repression; H3K9me3 → heterochromatin",
            "Multiple marks predicted simultaneously across tissues",
        ],
        "scoreable": True,
    },
    {
        "name": "CHIP_TF",
        "full_name": "ChIP-seq – Transcription factors",
        "category": "Epigenomics",
        "tagline": "Narrow peaks showing where transcription factors bind.",
        "bullets": [
            "Each track corresponds to one TF in one cell context",
            "Useful for mapping TF binding landscapes in silico",
            "Helps explain functional effects of variants in binding motifs",
        ],
        "scoreable": True,
    },
    {
        "name": "SPLICE_SITES",
        "full_name": "Splice sites",
        "category": "RNA splicing",
        "tagline": "Strength of donor and acceptor splice signals at each position.",
        "bullets": [
            "High score → strong splice signal at that base",
            "Enables detection of cryptic splice sites created by variants",
            "Separate tracks for donors (5′) and acceptors (3′)",
        ],
        "scoreable": False,
    },
    {
        "name": "SPLICE_SITE_USAGE",
        "full_name": "Splice site usage",
        "category": "RNA splicing",
        "tagline": "How often each splice site is actually used vs. competitors.",
        "bullets": [
            "Captures competitive context between nearby splice sites",
            "Better than raw strength for predicting exon-skipping",
            "Useful for modelling splicing QTL effects",
        ],
        "scoreable": False,
    },
    {
        "name": "SPLICE_JUNCTIONS",
        "full_name": "Splice junctions",
        "category": "RNA splicing",
        "tagline": "Predicted strength of exon–exon connections across the locus.",
        "bullets": [
            "Covers cassette exons, alt 5′/3′ sites, intron retention",
            "Shows the full landscape of alternative splicing",
            "Complements splice site tracks for complex locus analysis",
        ],
        "scoreable": False,
    },
    {
        "name": "PROCAP",
        "full_name": "PRO-cap",
        "category": "Transcription start sites",
        "tagline": "Higher-resolution TSS signal from nascent (engaged) RNA pol II.",
        "bullets": [
            "Captures actively elongating polymerase — lower background than CAGE",
            "Detects enhancer RNAs (eRNAs) as bidirectional peaks",
            "Best choice when precise TSS localisation matters",
        ],
        "scoreable": False,
    },
]

_ONTOLOGY_CATEGORY = {
    "UBERON": "Tissue / organ",
    "CL":     "Cell type",
    "EFO":    "Cell line / experimental factor",
}


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _output_card(ot: dict):
    color, text_cls, icon = _CATEGORY_STYLE.get(
        ot["category"], ("#6c757d", "text-secondary", "•")
    )
    scoreable_badge = (
        ui.tags.span("Scoreable", class_="badge bg-success ms-1")
        if ot["scoreable"]
        else ui.tags.span("Plot only", class_="badge bg-secondary ms-1")
    )
    bullet_items = ui.tags.ul(
        *[ui.tags.li(b, class_="small text-muted") for b in ot["bullets"]],
        class_="mb-0 ps-3",
        style="list-style-type: disc;",
    )
    return ui.tags.div(
        ui.card(
            ui.card_header(
                ui.tags.span(
                    ui.tags.span(icon, style="font-size:1.1em; margin-right:5px;"),
                    ui.tags.strong(ot["name"]),
                    ui.tags.span(
                        f" · {ot['full_name']}",
                        class_="fw-normal text-muted small",
                    ),
                    scoreable_badge,
                ),
                style=f"border-left: 4px solid {color}; background:#f8f9fa;",
            ),
            ui.card_body(
                ui.tags.span(
                    ot["category"],
                    class_=f"badge bg-light border {text_cls} small mb-2",
                    style="font-weight:500;",
                ),
                ui.p(ot["tagline"], class_="mb-2 small fw-semibold"),
                bullet_items,
                style="padding: 0.75rem;",
            ),
            class_="h-100 shadow-sm",
        ),
        class_="col-md-4 mb-3",
    )


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

@module.ui
def guide_ui():
    # Build rows of 3 cards
    cards = [_output_card(ot) for ot in OUTPUT_TYPE_INFO]
    rows = []
    for i in range(0, len(cards), 3):
        rows.append(
            ui.tags.div(*cards[i:i+3], class_="row")
        )

    return ui.div(
        ui.h2("User Guide", class_="mb-1"),
        ui.p(
            "Reference information to help you configure predictions. "
            "Use the tabs below to explore output types and supported tissues / cell types.",
            class_="text-muted mb-3",
        ),
        ui.navset_tab(
            # ── Tab 1: Output types ────────────────────────────────────────
            ui.nav_panel(
                "Output Types",
                ui.div(
                    ui.div(
                        ui.tags.span("Scoreable", class_="badge bg-success me-1"),
                        "= usable with variant scorers (Variant Analysis & ISM).  ",
                        ui.tags.span("Plot only", class_="badge bg-secondary me-1"),
                        "= predictions available but no built-in scorer.",
                        class_="alert alert-light border small mt-3 mb-3",
                    ),
                    *rows,
                ),
            ),
            # ── Tab 2: Tissues & cell types ───────────────────────────────
            ui.nav_panel(
                "Tissues & Cell Types",
                ui.div(
                    ui.p(
                        "Select ontology terms to restrict predictions to specific biological contexts. "
                        "Use ",
                        ui.tags.strong("UBERON"),
                        " for tissues/organs, ",
                        ui.tags.strong("CL"),
                        " for cell types, and ",
                        ui.tags.strong("EFO"),
                        " for cell lines.",
                        class_="mt-3 mb-3 small text-muted",
                    ),
                    ui.input_text(
                        "tissue_search",
                        None,
                        placeholder="Filter by name or ontology ID…",
                        width="320px",
                    ),
                    ui.output_ui("tissue_table"),
                    class_="pb-4",
                ),
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

@module.server
def guide_server(input, output, session):

    @render.ui
    def tissue_table():
        query = input.tissue_search().strip().lower()

        rows = []
        for curie, name in ONTOLOGY_TERMS.items():
            prefix = curie.split(":")[0]
            category = _ONTOLOGY_CATEGORY.get(prefix, prefix)
            if query and query not in curie.lower() and query not in name.lower():
                continue
            rows.append((curie, name, category))

        if not rows:
            return ui.div(
                ui.tags.em("No terms match your search."),
                class_="text-muted mt-2",
            )

        # Category → badge colour
        cat_badge = {
            "Tissue / organ":                   "bg-primary",
            "Cell type":                         "bg-success",
            "Cell line / experimental factor":   "bg-warning text-dark",
        }

        header = ui.tags.thead(
            ui.tags.tr(
                ui.tags.th("Ontology ID"),
                ui.tags.th("Name"),
                ui.tags.th("Category"),
            )
        )
        body_rows = [
            ui.tags.tr(
                ui.tags.td(ui.tags.code(curie)),
                ui.tags.td(name),
                ui.tags.td(
                    ui.tags.span(
                        category,
                        class_=f"badge {cat_badge.get(category, 'bg-secondary')}",
                    )
                ),
            )
            for curie, name, category in rows
        ]
        return ui.tags.table(
            header,
            ui.tags.tbody(*body_rows),
            class_="table table-sm table-hover table-bordered mt-2",
        )
