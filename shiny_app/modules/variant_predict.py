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
    help_icon,
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
                ui.input_numeric(
                    "position",
                    ui.span("Position (1-based)", help_icon(
                        "The genomic coordinate of the variant in 1-based notation, "
                        "matching the VCF convention. Must be within the chosen chromosome."
                    )),
                    value=36_201_698, min=1,
                ),
                ui.input_text(
                    "ref_bases",
                    ui.span("REF allele", help_icon(
                        "The reference base(s) at this position, as they appear in the "
                        "reference genome (hg38). Usually a single nucleotide for SNVs."
                    )),
                    value="A", placeholder="e.g. A",
                ),
                ui.input_text(
                    "alt_bases",
                    ui.span("ALT allele", help_icon(
                        "The alternate (mutant) base(s) to substitute at this position. "
                        "The model compares REF vs ALT predictions to measure functional impact."
                    )),
                    value="C", placeholder="e.g. C",
                ),
                ui.hr(),
                ui.h5("Interval"),
                ui.input_select(
                    "seq_length",
                    ui.span("Sequence length", help_icon(
                        "The genomic window centred on the variant that is fed to the model. "
                        "Larger windows capture more distal regulatory context. "
                        "1 MB is recommended for most variants."
                    )),
                    choices={v: k for k, v in SEQUENCE_LENGTH_OPTIONS.items()},
                    selected="SEQUENCE_LENGTH_1MB",
                ),
                ui.hr(),
                ui.h5("Prediction output"),
                ui.input_select(
                    "output_type",
                    ui.span("Output type", help_icon(
                        "The genomic assay track to compare between REF and ALT. "
                        "Only scoreable types are listed. See the Guide page for descriptions."
                    )),
                    choices={t: t.replace("_", " ").title() for t in SCOREABLE_OUTPUT_TYPES},
                    selected="RNA_SEQ",
                ),
                ui.input_selectize(
                    "ontology_terms",
                    ui.span("Tissues / cell types", help_icon(
                        "Restrict predictions to these biological contexts. "
                        "See the Guide page for the full list of supported terms."
                    )),
                    choices=ONTOLOGY_CHOICES,
                    multiple=True,
                    selected=["UBERON:0001157"],
                    options={"placeholder": "Select ontology terms…"},
                ),
                ui.input_text(
                    "custom_ontology",
                    ui.span("Custom ontology term", help_icon(
                        "Enter any valid ontology CURIE not in the list, e.g. UBERON:0001157."
                    )),
                    placeholder="e.g. UBERON:0001157",
                ),
                ui.hr(),
                ui.h5("Visualisation zoom"),
                ui.input_select(
                    "zoom_length",
                    ui.span("Plot window", help_icon(
                        "The region shown in the REF vs ALT plot. The model always uses the "
                        "full sequence length above; this only controls how much is displayed. "
                        "16 KB gives the clearest view around the variant."
                    )),
                    choices={v: k for k, v in SEQUENCE_LENGTH_OPTIONS.items()},
                    selected="SEQUENCE_LENGTH_16KB",
                ),
                ui.hr(),
                ui.input_checkbox(
                    "run_scoring",
                    ui.span("Also score the variant", help_icon(
                        "Run the recommended quantile-calibrated scorer for the chosen output type. "
                        "Produces a ranked table of effect sizes across all tracks and tissues. "
                        "Adds an extra API call."
                    )),
                    value=True,
                ),
                ui.hr(),
                ui.h5("Transcript annotations"),
                ui.input_checkbox(
                    "show_transcripts",
                    ui.span("Overlay gene annotations", help_icon(
                        "Draw MANE-select transcripts above the REF vs ALT plot so you can "
                        "see which genes are in the region. The GENCODE annotation "
                        "(~100 MB) is downloaded automatically on the first run."
                    )),
                    value=True,
                ),
                ui.output_ui("gtf_status_ui"),
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

    @render.ui
    def gtf_status_ui():
        if not input.show_transcripts():
            return ui.div()
        if _gtf_loaded():
            return ui.div(ui.tags.small("Gene annotations ready.", class_="text-success"))
        return ui.div(ui.tags.small(
            "Annotations will load automatically on first run.", class_="text-muted"
        ))

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

            # Auto-load GTF if transcript overlay is enabled and not yet loaded
            transcripts = None
            if input.show_transcripts():
                if not _gtf_loaded():
                    ui.notification_show(
                        "Loading GENCODE annotation (~100 MB, first run only)…",
                        duration=None, id="gtf_notif_v",
                    )
                    gtf, tx_extractor = get_gtf()
                    _gtf_data.set((gtf, tx_extractor))
                    _gtf_loaded.set(True)
                    ui.notification_remove("gtf_notif_v")
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
