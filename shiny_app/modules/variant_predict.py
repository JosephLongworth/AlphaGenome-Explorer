"""
Variant Analysis module – predict variant effects (REF vs ALT) and score variants
using recommended scoring configurations.
"""
from shiny import module, ui, render, reactive
import matplotlib.pyplot as plt

from shared import (
    ONTOLOGY_CHOICES,
    SCOREABLE_OUTPUT_TYPES,
    SEQUENCE_LENGTH_OPTIONS,
    get_model,
    get_gtf,
)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

@module.ui
def variant_predict_ui():
    return ui.div(
        ui.h2("Variant Analysis", class_="mb-1"),
        ui.p(
            "Predict the functional effect of a single nucleotide variant (SNV) by comparing "
            "REF and ALT allele predictions. Optionally score the variant using recommended "
            "quantile-calibrated scorers.",
            class_="text-muted mb-3",
        ),
        ui.layout_sidebar(
            # ── Sidebar ────────────────────────────────────────────────────
            ui.sidebar(
                ui.h5("Variant"),
                ui.input_text("chromosome", "Chromosome", value="chr22", placeholder="e.g. chr1"),
                ui.input_numeric("position", "Position (1-based)", value=36_201_698, min=1),
                ui.input_text("ref_bases", "REF allele", value="A", placeholder="e.g. A"),
                ui.input_text("alt_bases", "ALT allele", value="C", placeholder="e.g. C"),
                ui.hr(),
                ui.h5("Interval"),
                ui.input_select(
                    "seq_length",
                    "Sequence length",
                    choices={v: k for k, v in SEQUENCE_LENGTH_OPTIONS.items()},
                    selected="SEQUENCE_LENGTH_1MB",
                ),
                ui.hr(),
                ui.h5("Prediction output"),
                ui.input_select(
                    "output_type",
                    "Output type",
                    choices={t: t.replace("_", " ").title() for t in SCOREABLE_OUTPUT_TYPES},
                    selected="RNA_SEQ",
                ),
                ui.input_selectize(
                    "ontology_terms",
                    "Tissues / cell types",
                    choices=ONTOLOGY_CHOICES,
                    multiple=True,
                    selected=["UBERON:0001157"],
                    options={"placeholder": "Select ontology terms…"},
                ),
                ui.input_text(
                    "custom_ontology",
                    "Custom ontology term",
                    placeholder="e.g. UBERON:0001157",
                ),
                ui.hr(),
                ui.h5("Visualisation zoom"),
                ui.input_select(
                    "zoom_length",
                    "Plot window",
                    choices={v: k for k, v in SEQUENCE_LENGTH_OPTIONS.items()},
                    selected="SEQUENCE_LENGTH_16KB",
                ),
                ui.hr(),
                ui.input_checkbox("run_scoring", "Also score the variant", value=True),
                ui.hr(),
                ui.h5("Transcript annotations"),
                ui.input_checkbox("show_transcripts", "Load GTF & overlay transcripts", value=False),
                ui.panel_conditional(
                    "input.show_transcripts",
                    ui.input_action_button(
                        "load_gtf_btn",
                        "Load gene annotations",
                        class_="btn btn-outline-secondary btn-sm w-100 mb-1",
                    ),
                    ui.output_ui("gtf_status_ui"),
                ),
                ui.hr(),
                ui.input_action_button(
                    "run_btn",
                    "Run Analysis",
                    class_="btn btn-primary w-100",
                ),
                width=320,
                bg="#f8f9fa",
            ),
            # ── Main panel ─────────────────────────────────────────────────
            ui.div(
                ui.output_ui("status_ui"),
                ui.navset_tab(
                    ui.nav_panel(
                        "REF vs ALT plot",
                        ui.output_plot("effect_plot", height="500px"),
                    ),
                    ui.nav_panel(
                        "Variant scores",
                        ui.output_ui("scores_ui"),
                    ),
                ),
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

@module.server
def variant_predict_server(input, output, session, api_key_rv):

    _gtf_loaded = reactive.Value(False)
    _gtf_data = reactive.Value(None)
    _result = reactive.Value(None)
    _error = reactive.Value(None)

    # ── Load GTF ────────────────────────────────────────────────────────────
    @reactive.effect
    @reactive.event(input.load_gtf_btn)
    def _load_gtf():
        _gtf_loaded.set(False)
        try:
            ui.notification_show(
                "Loading GENCODE annotation (~100 MB, first run only)…",
                duration=None, id="gtf_notif_v",
            )
            gtf, tx_extractor = get_gtf()
            _gtf_data.set((gtf, tx_extractor))
            _gtf_loaded.set(True)
            ui.notification_remove("gtf_notif_v")
            ui.notification_show("Gene annotations loaded.", type="message", duration=4)
        except Exception as exc:
            ui.notification_remove("gtf_notif_v")
            _error.set(f"Failed to load GTF: {exc}")

    @render.ui
    def gtf_status_ui():
        if _gtf_loaded():
            return ui.div(ui.tags.small("Annotations loaded.", class_="text-success"))
        return ui.div(ui.tags.small("Not yet loaded.", class_="text-muted"))

    # ── Run analysis ─────────────────────────────────────────────────────────
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
            from alphagenome.data import genome
            from alphagenome.models import variant_scorers

            variant = genome.Variant(
                chromosome=input.chromosome().strip(),
                position=int(input.position()),
                reference_bases=input.ref_bases().strip().upper(),
                alternate_bases=input.alt_bases().strip().upper(),
            )

            seq_length = getattr(dna_client, input.seq_length())
            interval = variant.reference_interval.resize(seq_length)

            ot_name = input.output_type()
            requested_output = getattr(dna_client.OutputType, ot_name)

            ont_terms = list(input.ontology_terms()) if input.ontology_terms() else []
            if input.custom_ontology().strip():
                ont_terms.append(input.custom_ontology().strip())
            if not ont_terms:
                _error.set("Select at least one ontology term.")
                return

            # Transcripts
            transcripts = None
            if input.show_transcripts() and _gtf_loaded():
                _, tx_extractor = _gtf_data()
                transcripts = tx_extractor.extract(interval)

            ui.notification_show("Running variant prediction…", duration=None, id="var_notif")
            model = get_model(key)

            variant_output = model.predict_variant(
                interval=interval,
                variant=variant,
                requested_outputs=[requested_output],
                ontology_terms=ont_terms,
            )

            # Optional scoring
            scores_df = None
            if input.run_scoring():
                scorer = variant_scorers.RECOMMENDED_VARIANT_SCORERS.get(ot_name)
                if scorer is not None:
                    raw_scores = model.score_variant(
                        interval=interval,
                        variant=variant,
                        variant_scorers=[scorer],
                    )
                    scores_df = variant_scorers.tidy_scores(raw_scores, match_gene_strand=True)

            _result.set(
                (variant_output, variant, interval, ot_name, transcripts, scores_df)
            )
            ui.notification_remove("var_notif")
            ui.notification_show("Analysis complete.", type="message", duration=4)

        except Exception as exc:
            ui.notification_remove("var_notif")
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
                ui.tags.strong("Run Analysis"),
                ".",
                class_="alert alert-info",
            )
        _, variant, interval, ot_name, *_ = _result()
        return ui.div(
            f"Variant: {variant} | Interval: {interval} | Output: {ot_name}",
            class_="alert alert-success",
        )

    # ── REF vs ALT plot ──────────────────────────────────────────────────────
    @render.plot
    def effect_plot():
        data = _result()
        if data is None:
            return

        variant_output, variant, interval, ot_name, transcripts, _ = data
        from alphagenome.visualization import plot_components
        from alphagenome.models import dna_client

        ref_track = getattr(variant_output.reference, ot_name.lower(), None)
        alt_track = getattr(variant_output.alternate, ot_name.lower(), None)
        if ref_track is None or alt_track is None:
            return

        seq_length_key = input.zoom_length()
        zoom_width = getattr(dna_client, seq_length_key)
        plot_interval = ref_track.interval.resize(zoom_width)

        components = []
        if transcripts is not None:
            components.append(plot_components.TranscriptAnnotation(transcripts))
        components.append(
            plot_components.OverlaidTracks(
                tdata={"REF": ref_track, "ALT": alt_track},
                colors={"REF": "dimgrey", "ALT": "#e74c3c"},
            )
        )

        fig = plot_components.plot(
            components=components,
            interval=plot_interval,
            annotations=[plot_components.VariantAnnotation([variant], alpha=0.8)],
        )
        return fig if fig is not None else plt.gcf()

    # ── Scores table ─────────────────────────────────────────────────────────
    @render.ui
    def scores_ui():
        data = _result()
        if data is None:
            return ui.div()

        *_, scores_df = data

        if scores_df is None:
            return ui.div(
                ui.tags.em("Variant scoring was not requested or scorer not available."),
                class_="text-muted mt-3",
            )

        # Show top hits sorted by absolute raw_score
        if "raw_score" in scores_df.columns:
            top = scores_df.reindex(
                scores_df["raw_score"].abs().sort_values(ascending=False).index
            ).head(50)
        else:
            top = scores_df.head(50)

        return ui.div(
            ui.tags.h5("Top 50 variant scores (sorted by |raw score|)", class_="mt-3"),
            ui.HTML(
                top.to_html(
                    classes="table table-sm table-striped table-bordered",
                    index=False,
                )
            ),
        )
