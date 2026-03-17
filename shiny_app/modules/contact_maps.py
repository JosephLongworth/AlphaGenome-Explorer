"""
Contact Maps module – predict Hi-C style chromatin contact maps from a
reference-genome interval using AlphaGenome's CONTACT_MAPS output type.

Contact maps are 2D matrices that capture the 3D organisation of chromatin –
how different regions of the genome physically interact with each other.
Unlike 1D genomic tracks, they do not vary by tissue/cell-type ontology term,
so no tissue selection is required.
"""
from shiny import module, ui, render, reactive
import matplotlib.pyplot as plt

from shared import (
    SEQUENCE_LENGTH_OPTIONS,
    get_model,
    get_gtf,
    help_icon,
)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

@module.ui
def contact_maps_ui():
    return ui.div(
        ui.h2("Contact Maps", class_="mb-1"),
        ui.p(
            "Predict Hi-C style chromatin contact maps for a genomic interval. "
            "Contact maps capture the 3D organisation of the genome – which regions "
            "physically interact – and are predicted directly from DNA sequence without "
            "requiring a tissue or cell-type selection.",
            class_="text-muted mb-3",
        ),
        ui.layout_sidebar(
            # ── Sidebar ────────────────────────────────────────────────────
            ui.sidebar(
                ui.h5("Interval definition"),
                ui.input_radio_buttons(
                    "interval_mode",
                    ui.span("Input mode", help_icon(
                        "Gene symbol: look up the MANE-select transcript for a gene and use its "
                        "genomic span. Manual: enter chromosome, start, and end coordinates directly."
                    )),
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
                        value="MYC",
                        placeholder="e.g. BRCA1, MYC …",
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
                        value="chr8",
                        placeholder="e.g. chr1",
                    ),
                    ui.input_numeric("start", "Start (bp)", value=127_700_000, min=1),
                    ui.input_numeric("end", "End (bp)", value=127_800_000, min=1),
                ),
                ui.hr(),
                ui.input_select(
                    "seq_length",
                    ui.span("Sequence window", help_icon(
                        "The genomic window used for prediction, centred on the interval midpoint. "
                        "Larger windows reveal long-range interactions (TADs, compartments) but "
                        "require more compute. 1 MB is recommended for contact maps."
                    )),
                    choices={v: k for k, v in SEQUENCE_LENGTH_OPTIONS.items()},
                    selected="SEQUENCE_LENGTH_1MB",
                ),
                ui.input_select(
                    "organism",
                    ui.span("Organism", help_icon(
                        "The species whose regulatory grammar the model was trained on. "
                        "Coordinates must match the reference genome (hg38 for Human, mm10 for Mouse)."
                    )),
                    choices={
                        "HOMO_SAPIENS": "Human (Homo sapiens)",
                        "MUS_MUSCULUS": "Mouse (Mus musculus)",
                    },
                ),
                ui.hr(),
                ui.h5("Display options"),
                ui.input_checkbox(
                    "show_transcripts",
                    ui.span("Overlay transcript annotations", help_icon(
                        "Draw MANE-select transcripts above the contact map. "
                        "Requires clicking 'Load gene annotations' first."
                    )),
                    value=True,
                ),
                ui.input_slider(
                    "vmax",
                    ui.span("Colour scale max", help_icon(
                        "Upper bound for the contact map colour scale (log-scale values). "
                        "Lower values increase sensitivity to weak interactions."
                    )),
                    min=0.5,
                    max=5.0,
                    value=2.0,
                    step=0.5,
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
                ui.output_ui("info_card_ui"),
                ui.output_ui("contact_plot_container"),
                ui.output_ui("metadata_ui"),
                ui.output_data_frame("metadata_table"),
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

@module.server
def contact_maps_server(input, output, session, api_key_rv):

    _gtf_loaded      = reactive.Value(False)
    _gtf_data        = reactive.Value(None)   # (gtf, transcript_extractor)
    _result          = reactive.Value(None)   # (output_obj, interval, transcripts)
    _error           = reactive.Value(None)
    _selected_track  = reactive.Value(0)      # index of track shown in plot

    # ── Load GTF ────────────────────────────────────────────────────────────
    @reactive.effect
    @reactive.event(input.load_gtf_btn)
    def _load_gtf():
        _gtf_loaded.set(False)
        _error.set(None)
        try:
            ui.notification_show(
                "Loading GENCODE annotation (~100 MB, first run only)…",
                duration=None, id="cm_gtf_notif",
            )
            gtf, tx_extractor = get_gtf()
            _gtf_data.set((gtf, tx_extractor))
            _gtf_loaded.set(True)
            ui.notification_remove("cm_gtf_notif")
            ui.notification_show("Gene annotations loaded.", type="message", duration=4)
        except Exception as exc:
            ui.notification_remove("cm_gtf_notif")
            _error.set(f"Failed to load GTF: {exc}")

    @render.ui
    def gtf_status_ui():
        if _gtf_loaded():
            return ui.div(ui.tags.small("Gene annotations loaded.", class_="text-success"))
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
        _selected_track.set(0)

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
            organism = getattr(dna_client.Organism, input.organism())

            ui.notification_show(
                "Running contact map prediction…", duration=None, id="cm_pred_notif"
            )
            model = get_model(key)
            output_obj = model.predict_interval(
                interval=interval,
                requested_outputs=[dna_client.OutputType.CONTACT_MAPS],
                ontology_terms=None,
                organism=organism,
            )

            # Extract transcripts if requested and GTF is available
            transcripts = None
            if input.show_transcripts() and _gtf_loaded():
                _, tx_extractor = _gtf_data()
                transcripts = tx_extractor.extract(interval)

            _result.set((output_obj, interval, transcripts))
            ui.notification_remove("cm_pred_notif")
            ui.notification_show("Prediction complete.", type="message", duration=4)

        except Exception as exc:
            ui.notification_remove("cm_pred_notif")
            _error.set(str(exc))

    # ── Status banner ────────────────────────────────────────────────────────
    @render.ui
    def status_ui():
        if _error() is not None:
            return ui.div(
                ui.tags.strong("Error: "), _error(),
                class_="alert alert-danger",
            )
        if _result() is None:
            return ui.div(
                "Configure an interval and click ",
                ui.tags.strong("Run Prediction"),
                ". Contact maps do not require a tissue/cell-type selection.",
                class_="alert alert-info",
            )
        output_obj, interval, transcripts = _result()
        cm = getattr(output_obj, "contact_maps", None)
        n_tracks = cm.num_tracks if cm is not None else 0
        n_tx = len(transcripts) if transcripts else 0
        return ui.div(
            f"Interval: {interval} | "
            f"{n_tracks} contact map track(s) | "
            f"{n_tx} transcript(s) extracted.",
            class_="alert alert-success",
        )

    # ── Info card (shown before first run) ──────────────────────────────────
    @render.ui
    def info_card_ui():
        if _result() is not None or _error() is not None:
            return ui.div()
        return ui.div(
            ui.card(
                ui.card_header(
                    ui.tags.span(
                        ui.tags.span("", class_="badge bg-dark me-2"),
                        "About Contact Maps",
                    )
                ),
                ui.card_body(
                    ui.tags.ul(
                        ui.tags.li(
                            "Contact maps capture genome 3D organisation — which genomic "
                            "loci physically interact with each other (Hi-C style predictions)."
                        ),
                        ui.tags.li(
                            "Unlike 1D genomic tracks, contact maps are predicted directly "
                            "from DNA sequence and do not require tissue/cell-type selection."
                        ),
                        ui.tags.li(
                            "Larger sequence windows (500 KB – 1 MB) are recommended to "
                            "visualise topologically associating domains (TADs) and compartments."
                        ),
                        ui.tags.li(
                            "The colour scale uses log-scale contact frequency values. "
                            "Adjust the colour scale max slider to tune contrast."
                        ),
                    ),
                ),
            ),
            class_="mb-3",
        )

    # ── Dynamic plot container height ────────────────────────────────────────
    @render.ui
    def contact_plot_container():
        data = _result()
        transcript_extra = 0
        if data is not None:
            _, _, transcripts = data
            transcript_extra = 80 if transcripts else 0
        height_px = 520 + transcript_extra
        return ui.output_plot("contact_plot", height=f"{height_px}px", width="100%")

    # ── Plot ────────────────────────────────────────────────────────────────
    @render.plot
    def contact_plot():
        data = _result()
        if data is None:
            return

        output_obj, interval, transcripts = data
        cm = getattr(output_obj, "contact_maps", None)
        if cm is None:
            return

        from alphagenome.visualization import plot_components

        # Clamp selected index to valid range
        idx = min(_selected_track(), cm.num_tracks - 1)
        cm_plot = cm.select_tracks_by_index([idx])

        components = []
        if transcripts is not None:
            components.append(
                plot_components.TranscriptAnnotation(transcripts, fig_height=0.15)
            )

        components.append(
            plot_components.ContactMaps(
                tdata=cm_plot,
                vmin=-1.0,
                vmax=float(input.vmax()),
            )
        )

        plot_interval = cm.interval if cm.interval is not None else interval
        fig = plot_components.plot(components=components, interval=plot_interval)
        if fig is None:
            fig = plt.gcf()

        transcript_height = 1.5 if transcripts is not None else 0.0
        fig.set_size_inches(fig.get_figwidth(), 10.0 + transcript_height + 1.0)
        return fig

    # ── Metadata heading ─────────────────────────────────────────────────────
    @render.ui
    def metadata_ui():
        data = _result()
        if data is None:
            return ui.div()
        output_obj, *_ = data
        cm = getattr(output_obj, "contact_maps", None)
        if cm is None or not hasattr(cm, "metadata") or cm.metadata is None:
            return ui.div()
        idx = min(_selected_track(), cm.num_tracks - 1)
        return ui.div(
            ui.tags.h5("Contact map tracks", class_="mt-4"),
            ui.tags.p(
                f"Showing track {idx}. Click a row below to switch tracks.",
                class_="text-muted mb-1",
            ),
        )

    # ── Selectable metadata table ─────────────────────────────────────────────
    @render.data_frame
    def metadata_table():
        data = _result()
        if data is None:
            return None
        output_obj, *_ = data
        cm = getattr(output_obj, "contact_maps", None)
        if cm is None or not hasattr(cm, "metadata") or cm.metadata is None:
            return None
        return render.DataGrid(cm.metadata, selection_mode="row", width="100%")

    # ── Update selected track when a row is clicked ───────────────────────────
    @reactive.effect
    def _on_track_select():
        sel = metadata_table.cell_selection()
        rows = sel.get("rows", ())
        if rows:
            _selected_track.set(int(rows[0]))
