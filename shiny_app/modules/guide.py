"""
Guide page – reference for output types and supported tissues / cell types.
"""
from shiny import module, ui

from shared import GUIDE_TABLE_ROWS


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
    "Genome 3D organisation":   ("#343a40", "text-dark",    "🧬"),
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
    {
        "name": "CONTACT_MAPS",
        "full_name": "Hi-C Contact Maps",
        "category": "Genome 3D organisation",
        "tagline": "Predicted 3D chromatin contacts — which loci physically interact.",
        "bullets": [
            "2D matrix: rows and columns are genomic bins, values are contact frequency",
            "Reveals TADs, loop anchors, and A/B compartments from sequence alone",
            "Does not require a tissue/cell-type selection — predicted from DNA sequence",
            "Use 500 KB or 1 MB windows for TAD-scale interpretation",
        ],
        "scoreable": False,
    },
]

_ONTOLOGY_CATEGORY = {
    "UBERON": "Tissue / organ",
    "CL":     "Cell type",
    "EFO":    "Cell line / experimental factor",
    "CLO":    "Cell line",
    "NTR":    "New term request",
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
# Tissue table (static, powered by DataTables.js)
# ---------------------------------------------------------------------------

# Output type → Bootstrap badge class
_OT_BADGE: dict[str, str] = {
    "ATAC":              "bg-primary",
    "DNASE":             "bg-primary",
    "CAGE":              "bg-warning text-dark",
    "PROCAP":            "bg-warning text-dark",
    "RNA_SEQ":           "bg-success",
    "CHIP_HISTONE":      "bg-purple",
    "CHIP_TF":           "bg-purple",
    "SPLICE_SITES":      "bg-danger",
    "SPLICE_SITE_USAGE": "bg-danger",
    "SPLICE_JUNCTIONS":  "bg-danger",
    "CONTACT_MAPS":      "bg-dark",
}

_CAT_BADGE: dict[str, str] = {
    "Tissue / organ":                  "bg-primary",
    "Cell type":                       "bg-success",
    "Cell line / experimental factor": "bg-warning text-dark",
    "Cell line":                       "bg-warning text-dark",
    "New term request":                "bg-secondary",
}

_ORG_BADGE: dict[str, str] = {
    "Human": "bg-info text-dark",
    "Mouse": "bg-secondary",
}


def _tissue_table_widget():
    """Build the full static DataTables widget for the Tissues & Cell Types tab."""

    # ── Build table body rows ────────────────────────────────────────────────
    body_rows = []
    for row in GUIDE_TABLE_ROWS:
        curie    = row["curie"]
        name     = row["name"]
        prefix   = curie.split(":")[0]
        category = _ONTOLOGY_CATEGORY.get(prefix, prefix)

        org_badges = ui.tags.span(
            *[
                ui.tags.span(
                    org,
                    class_=f"badge {_ORG_BADGE.get(org, 'bg-secondary')} me-1",
                    style="font-size:0.75em;",
                )
                for org in row["organisms"]
            ]
        )

        ot_badges = (
            ui.tags.span(
                *[
                    ui.tags.span(
                        ot,
                        class_=f"badge {_OT_BADGE.get(ot, 'bg-secondary')} me-1",
                        style="font-size:0.7em;",
                    )
                    for ot in row["output_types"]
                ]
            )
            if row["output_types"]
            else ui.tags.span("—", class_="text-muted small")
        )

        body_rows.append(
            ui.tags.tr(
                ui.tags.td(ui.tags.code(curie)),
                ui.tags.td(name),
                ui.tags.td(
                    ui.tags.span(
                        category,
                        class_=f"badge {_CAT_BADGE.get(category, 'bg-secondary')}",
                    )
                ),
                ui.tags.td(org_badges),
                ui.tags.td(ot_badges),
            )
        )

    # ── Column headers & footer filter inputs ────────────────────────────────
    col_names = ["Ontology ID", "Name", "Category", "Organism", "Available output types"]

    thead = ui.tags.thead(
        ui.tags.tr(*[ui.tags.th(c) for c in col_names])
    )
    tfoot = ui.tags.tfoot(
        ui.tags.tr(
            *[
                ui.tags.th(
                    ui.tags.input(
                        type="text",
                        placeholder=f"Filter…",
                        style="width:100%; font-size:0.78em; padding:2px 4px;",
                    )
                )
                for _ in col_names
            ]
        )
    )

    table = ui.tags.table(
        thead,
        ui.tags.tbody(*body_rows),
        tfoot,
        id="tissue-dt",
        class_="table table-sm table-hover table-bordered w-100",
    )

    # ── DataTables initialisation script ─────────────────────────────────────
    init_js = ui.tags.script(
        """
        $(function () {
            var tbl = $('#tissue-dt');
            if (!tbl.length) return;

            var dt = tbl.DataTable({
                pageLength: 25,
                scrollX: true,
                autoWidth: false,
                order: [[0, 'asc']],
                columnDefs: [
                    { orderable: true,  targets: '_all' },
                    { width: '130px',   targets: 0 },
                    { width: '220px',   targets: 1 },
                    { width: '140px',   targets: 2 },
                    { width: '100px',   targets: 3 },
                ],
                initComplete: function () {
                    this.api().columns().every(function (i) {
                        var col = this;
                        $('input', col.footer()).on('keyup change clear', function () {
                            if (col.search() !== this.value) {
                                col.search(this.value).draw();
                            }
                        });
                    });
                },
            });

            /* Re-adjust when the tab becomes visible */
            $('[data-bs-toggle="tab"]').on('shown.bs.tab', function () {
                dt.columns.adjust();
            });
        });
        """
    )

    return ui.div(
        ui.head_content(
            ui.tags.link(
                rel="stylesheet",
                href="https://cdn.datatables.net/1.13.8/css/dataTables.bootstrap5.min.css",
            ),
            ui.tags.script(
                src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"
            ),
            ui.tags.script(
                src="https://cdn.datatables.net/1.13.8/js/dataTables.bootstrap5.min.js"
            ),
        ),
        table,
        init_js,
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
                        "Ontology terms supported by AlphaGenome. "
                        "Use ",
                        ui.tags.strong("UBERON"),
                        " for tissues/organs, ",
                        ui.tags.strong("CL"),
                        " for cell types, and ",
                        ui.tags.strong("EFO / CLO"),
                        " for cell lines. "
                        "Click any column header to sort; use the filter row to search within a column.",
                        class_="mt-3 mb-3 small text-muted",
                    ),
                    _tissue_table_widget(),
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
    pass  # tissue table is built statically in guide_ui via _tissue_table_widget()
