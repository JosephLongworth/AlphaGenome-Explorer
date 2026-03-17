"""
Landing page module – instructions and module overview.
"""
from shiny import module, ui


@module.ui
def landing_ui():
    return ui.div(
        # ── Hero ──────────────────────────────────────────────────────────────
        ui.div(
            ui.h1("AlphaGenome Explorer", class_="display-4 fw-bold"),
            ui.p(
                "An interactive research interface for genomic predictions powered by the ",
                ui.tags.a(
                    "AlphaGenome model",
                    href="https://www.alphagenomedocs.com",
                    target="_blank",
                ),
                " from Google DeepMind.",
                class_="lead",
            ),
            ui.p(
                ui.tags.em(
                    "Navigate to the Settings tab to enter your API key before running any predictions."
                ),
                class_="text-muted",
            ),
            class_="py-5 text-center border-bottom",
        ),
        # ── Quick-start instructions ──────────────────────────────────────────
        ui.h2("Getting started", class_="mt-4 mb-3"),
        ui.div(
            ui.div(
                ui.div(
                    ui.tags.span("1", class_="badge bg-primary me-2"),
                    ui.tags.strong("Set your API key"),
                    class_="mb-1",
                ),
                ui.p(
                    "Go to the ",
                    ui.tags.strong("Settings"),
                    " tab (top-right) and paste your AlphaGenome API key. "
                    "The key will persist for the duration of your session.",
                    class_="mb-0 text-muted",
                ),
                class_="card-body",
            ),
            class_="card mb-3",
        ),
        ui.div(
            ui.div(
                ui.div(
                    ui.tags.span("2", class_="badge bg-primary me-2"),
                    ui.tags.strong("Choose a module"),
                    class_="mb-1",
                ),
                ui.p(
                    "Select a prediction mode from the navigation bar above. "
                    "Each module corresponds to a distinct use-case described below.",
                    class_="mb-0 text-muted",
                ),
                class_="card-body",
            ),
            class_="card mb-3",
        ),
        ui.div(
            ui.div(
                ui.div(
                    ui.tags.span("3", class_="badge bg-primary me-2"),
                    ui.tags.strong("Configure and run"),
                    class_="mb-1",
                ),
                ui.p(
                    "Fill in the sidebar parameters for your chosen module, then click ",
                    ui.tags.strong("Run"),
                    ". Predictions may take 10–60 seconds depending on sequence length "
                    "and the number of requested output types.",
                    class_="mb-0 text-muted",
                ),
                class_="card-body",
            ),
            class_="card mb-4",
        ),
        # ── Module overview cards ─────────────────────────────────────────────
        ui.h2("Available modules", class_="mb-3"),
        ui.div(
            # Sequence Prediction
            ui.div(
                ui.div(
                    ui.div(
                        ui.tags.span(
                            "Sequence Prediction",
                            class_="card-title fw-semibold fs-5",
                        ),
                        class_="mb-2",
                    ),
                    ui.p(
                        "Predict genomic track values (DNase, CAGE, RNA-seq, etc.) "
                        "directly from a raw DNA sequence of your choice. "
                        "The sequence is centre-padded to a supported length before inference.",
                        class_="card-text text-muted",
                    ),
                    class_="card-body",
                ),
                class_="card h-100 border-primary",
            ),
            # Interval Prediction
            ui.div(
                ui.div(
                    ui.div(
                        ui.tags.span(
                            "Interval Prediction",
                            class_="card-title fw-semibold fs-5",
                        ),
                        class_="mb-2",
                    ),
                    ui.p(
                        "Make predictions for a genomic region from the human reference "
                        "genome (GRCh38/hg38). Specify a chromosome interval or search "
                        "by gene symbol. Predicted tracks are plotted alongside MANE-select "
                        "transcript annotations.",
                        class_="card-text text-muted",
                    ),
                    class_="card-body",
                ),
                class_="card h-100 border-primary",
            ),
            # Variant Analysis
            ui.div(
                ui.div(
                    ui.div(
                        ui.tags.span(
                            "Variant Analysis",
                            class_="card-title fw-semibold fs-5",
                        ),
                        class_="mb-2",
                    ),
                    ui.p(
                        "Predict the functional effect of a single nucleotide variant (SNV) "
                        "by comparing REF and ALT allele predictions side-by-side. "
                        "Optionally score the variant effect using recommended "
                        "quantile-calibrated scorers.",
                        class_="card-text text-muted",
                    ),
                    class_="card-body",
                ),
                class_="card h-100 border-primary",
            ),
            # ISM Analysis
            ui.div(
                ui.div(
                    ui.div(
                        ui.tags.span(
                            "In Silico Mutagenesis (ISM)",
                            class_="card-title fw-semibold fs-5",
                        ),
                        class_="mb-2",
                    ),
                    ui.p(
                        "Systematically mutate every base in a target region and score "
                        "the effect on a chosen output type. Results are displayed as a "
                        "sequence logo revealing functionally important positions. "
                        "Recommended for short context windows (16 KB).",
                        class_="card-text text-muted",
                    ),
                    class_="card-body",
                ),
                class_="card h-100 border-primary",
            ),
            # Contact Maps
            ui.div(
                ui.div(
                    ui.div(
                        ui.tags.span(
                            "Contact Maps",
                            class_="card-title fw-semibold fs-5",
                        ),
                        class_="mb-2",
                    ),
                    ui.p(
                        "Predict Hi-C style chromatin contact maps for a genomic interval. "
                        "Visualise topologically associating domains (TADs), compartments, "
                        "and long-range looping interactions directly from DNA sequence. "
                        "No tissue or cell-type selection required.",
                        class_="card-text text-muted",
                    ),
                    class_="card-body",
                ),
                class_="card h-100 border-primary",
            ),
            # Guide
            ui.div(
                ui.div(
                    ui.div(
                        ui.tags.span(
                            "Guide",
                            class_="card-title fw-semibold fs-5",
                        ),
                        class_="mb-2",
                    ),
                    ui.p(
                        "Browse the full catalogue of available tissues, cell types, and "
                        "output tracks supported by AlphaGenome. Use the searchable table "
                        "to find ontology terms for use in prediction modules.",
                        class_="card-text text-muted",
                    ),
                    class_="card-body",
                ),
                class_="card h-100 border-primary",
            ),
            class_="row row-cols-1 row-cols-md-2 g-4 mb-5",
        ),
        # ── Tips ─────────────────────────────────────────────────────────────
        ui.h2("Tips", class_="mb-3"),
        ui.tags.ul(
            ui.tags.li(
                "Use ",
                ui.tags.strong("ontology terms"),
                " (e.g. UBERON:0002048 for Lung) to filter predictions to specific "
                "tissues or cell types. Multiple terms can be selected simultaneously.",
            ),
            ui.tags.li(
                "Longer sequences (500 KB / 1 MB) capture distal regulatory elements "
                "but increase API latency. For ISM, prefer 16 KB for speed."
            ),
            ui.tags.li(
                "The ",
                ui.tags.strong("quantile score"),
                " from Variant Analysis allows direct comparison across different "
                "scoring strategies and output types."
            ),
            ui.tags.li(
                "For mouse predictions, switch the organism dropdown to ",
                ui.tags.em("Mus musculus"),
                " in the Sequence or Interval modules."
            ),
        ),
        class_="container py-4",
    )


@module.server
def landing_server(input, output, session):
    pass  # landing page is purely informational
