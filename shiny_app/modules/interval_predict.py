"""
Interval Prediction module – predict genomic tracks from a reference-genome interval.
Supports both manual interval entry and gene-symbol lookup (GENCODE hg38 MANE-select).
"""
from shiny import module, ui, render, reactive
import matplotlib.pyplot as plt

from shared import (
    ONTOLOGY_CHOICES,
    ALL_OUTPUT_TYPES,
    SEQUENCE_LENGTH_OPTIONS,
    get_model,
    get_gtf,
)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

@module.ui
def interval_predict_ui():
    return ui.div(
        ui.h2("Interval Prediction", class_="mb-1"),
        ui.p(
            "Make predictions for a genomic interval from the human reference genome "
            "(GRCh38/hg38). Specify an interval manually or search by gene symbol.",
            class_="text-muted mb-3",
        ),
        ui.layout_sidebar(
            # ── Sidebar ────────────────────────────────────────────────────
            ui.sidebar(
                ui.h5("Interval definition"),
                ui.input_radio_buttons(
                    "interval_mode",
                    None,
                    choices={"gene": "Gene symbol", "manual": "Manual interval"},
                    selected="gene",
                    inline=True,
                ),
                # --- Gene lookup
                ui.panel_conditional(
                    "input.interval_mode === 'gene'",
                    ui.input_text(
                        "gene_symbol",
                        "Gene symbol (HGNC)",
                        value="CYP2B6",
                        placeholder="e.g. BRCA1, TP53 …",
                    ),
                    ui.input_action_button(
                        "load_gtf_btn",
                        "Load gene annotations",
                        class_="btn btn-outline-secondary btn-sm w-100 mb-2",
                    ),
                    ui.output_ui("gtf_status_ui"),
                ),
                # --- Manual interval
                ui.panel_conditional(
                    "input.interval_mode === 'manual'",
                    ui.input_text(
                        "chromosome",
                        "Chromosome",
                        value="chr19",
                        placeholder="e.g. chr1",
                    ),
                    ui.input_numeric("start", "Start (bp)", value=40_991_281, min=1),
                    ui.input_numeric("end", "End (bp)", value=41_018_398, min=1),
                ),
                ui.hr(),
                ui.input_select(
                    "seq_length",
                    "Resize interval to",
                    choices={v: k for k, v in SEQUENCE_LENGTH_OPTIONS.items()},
                    selected="SEQUENCE_LENGTH_1MB",
                ),
                ui.input_select(
                    "organism",
                    "Organism",
                    choices={
                        "HOMO_SAPIENS": "Human (Homo sapiens)",
                        "MUS_MUSCULUS": "Mouse (Mus musculus)",
                    },
                ),
                ui.hr(),
                ui.h5("Output types"),
                ui.input_checkbox_group(
                    "output_types",
                    None,
                    choices={t: t.replace("_", " ").title() for t in ALL_OUTPUT_TYPES},
                    selected=["RNA_SEQ"],
                ),
                ui.hr(),
                ui.h5("Tissues / cell types"),
                ui.input_selectize(
                    "ontology_terms",
                    None,
                    choices=ONTOLOGY_CHOICES,
                    multiple=True,
                    selected=["UBERON:0001114"],
                    options={"placeholder": "Select ontology terms…"},
                ),
                ui.input_text(
                    "custom_ontology",
                    "Custom ontology term",
                    placeholder="e.g. UBERON:0001157",
                ),
                ui.hr(),
                ui.input_checkbox(
                    "show_transcripts",
                    "Overlay transcript annotations",
                    value=True,
                ),
                ui.hr(),
                ui.input_action_button(
                    "run_btn",
                    "Run Prediction",
                    class_="btn btn-primary w-100",
                ),
                width=320,
                bg="#f8f9fa",
            ),
            # ── Main panel ─────────────────────────────────────────────────
            ui.div(
                ui.output_ui("status_ui"),
                ui.output_plot("prediction_plot", height="550px"),
                ui.output_ui("metadata_ui"),
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

@module.server
def interval_predict_server(input, output, session, api_key_rv):

    _gtf_loaded = reactive.Value(False)
    _gtf_data = reactive.Value(None)   # (gtf, transcript_extractor)
    _result = reactive.Value(None)
    _error = reactive.Value(None)

    # ── Load GTF ────────────────────────────────────────────────────────────
    @reactive.effect
    @reactive.event(input.load_gtf_btn)
    def _load_gtf():
        _gtf_loaded.set(False)
        _error.set(None)
        try:
            ui.notification_show(
                "Loading GENCODE annotation (~100 MB, first run only)…",
                duration=None, id="gtf_notif",
            )
            gtf, tx_extractor = get_gtf()
            _gtf_data.set((gtf, tx_extractor))
            _gtf_loaded.set(True)
            ui.notification_remove("gtf_notif")
            ui.notification_show("Gene annotations loaded.", type="message", duration=4)
        except Exception as exc:
            ui.notification_remove("gtf_notif")
            _error.set(f"Failed to load GTF: {exc}")

    @render.ui
    def gtf_status_ui():
        if _gtf_loaded():
            return ui.div(
                ui.tags.small("Gene annotations loaded.", class_="text-success"),
            )
        return ui.div(
            ui.tags.small(
                "Click 'Load gene annotations' before running a gene-based prediction.",
                class_="text-muted",
            )
        )

    # ── Run prediction ──────────────────────────────────────────────────────
    @reactive.effect
    @reactive.event(input.run_btn)
    def _run():
        _result.set(None)
        _error.set(None)

        key = api_key_rv()
        if not key:
            _error.set("No API key set. Go to Settings and enter your key.")
            return

        try:
            from alphagenome.models import dna_client
            from alphagenome.data import genome, gene_annotation

            # Build interval
            if input.interval_mode() == "gene":
                if not _gtf_loaded():
                    _error.set("Load gene annotations first (click the button above).")
                    return
                gtf, tx_extractor = _gtf_data()
                interval = gene_annotation.get_gene_interval(
                    gtf, gene_symbol=input.gene_symbol().strip()
                )
            else:
                interval = genome.Interval(
                    chromosome=input.chromosome().strip(),
                    start=int(input.start()),
                    end=int(input.end()),
                )

            seq_length = getattr(dna_client, input.seq_length())
            interval = interval.resize(seq_length)

            out_types = input.output_types()
            if not out_types:
                _error.set("Select at least one output type.")
                return

            ont_terms = list(input.ontology_terms()) if input.ontology_terms() else []
            if input.custom_ontology().strip():
                ont_terms.append(input.custom_ontology().strip())
            if not ont_terms:
                _error.set("Select at least one ontology term.")
                return

            organism = getattr(dna_client.Organism, input.organism())
            requested = [getattr(dna_client.OutputType, t) for t in out_types]

            ui.notification_show("Running prediction…", duration=None, id="pred_notif")
            model = get_model(key)
            output_obj = model.predict_interval(
                interval=interval,
                requested_outputs=requested,
                ontology_terms=ont_terms,
                organism=organism,
            )

            # Extract transcripts if requested and GTF is available
            transcripts = None
            if input.show_transcripts() and _gtf_loaded():
                _, tx_extractor = _gtf_data()
                transcripts = tx_extractor.extract(interval)

            _result.set((output_obj, out_types, interval, transcripts))
            ui.notification_remove("pred_notif")
            ui.notification_show("Prediction complete.", type="message", duration=4)

        except Exception as exc:
            ui.notification_remove("pred_notif")
            _error.set(str(exc))

    # ── Status banner ───────────────────────────────────────────────────────
    @render.ui
    def status_ui():
        if _error() is not None:
            return ui.div(
                ui.tags.strong("Error: "), _error(),
                class_="alert alert-danger",
            )
        if _result() is None:
            return ui.div(
                "Configure parameters and click ",
                ui.tags.strong("Run Prediction"),
                ".",
                class_="alert alert-info",
            )
        output_obj, out_types, interval, transcripts = _result()
        n_tx = len(transcripts) if transcripts else 0
        return ui.div(
            f"Interval: {interval} | "
            f"{n_tx} transcript(s) extracted.",
            class_="alert alert-success",
        )

    # ── Plot ────────────────────────────────────────────────────────────────
    @render.plot
    def prediction_plot():
        data = _result()
        if data is None:
            return

        output_obj, out_types, interval, transcripts = data
        from alphagenome.visualization import plot_components

        components = []
        if transcripts is not None:
            components.append(plot_components.TranscriptAnnotation(transcripts))

        for ot_name in out_types:
            track_data = getattr(output_obj, ot_name.lower(), None)
            if track_data is not None:
                components.append(
                    plot_components.Tracks(track_data)
                )

        if not components:
            return

        # Use first track's interval for the plot (already resized)
        plot_interval = None
        for ot_name in out_types:
            td = getattr(output_obj, ot_name.lower(), None)
            if td is not None:
                plot_interval = td.interval
                break

        fig = plot_components.plot(components=components, interval=plot_interval or interval)
        return fig if fig is not None else plt.gcf()

    # ── Metadata table ──────────────────────────────────────────────────────
    @render.ui
    def metadata_ui():
        data = _result()
        if data is None:
            return ui.div()

        output_obj, out_types, *_ = data
        tables = []
        for ot_name in out_types:
            track_data = getattr(output_obj, ot_name.lower(), None)
            if track_data is not None and hasattr(track_data, "metadata"):
                df = track_data.metadata
                tables.append(
                    ui.div(
                        ui.tags.h5(f"{ot_name} – track metadata", class_="mt-4"),
                        ui.HTML(
                            df.to_html(
                                classes="table table-sm table-striped table-bordered",
                                index=False,
                                max_rows=20,
                            )
                        ),
                    )
                )

        return ui.div(*tables) if tables else ui.div()
