"""
In Silico Mutagenesis (ISM) module – score all single nucleotide variants in a
target region and visualise the results as a sequence logo.
"""
from shiny import module, ui, render, reactive
import matplotlib.pyplot as plt

from shared import ONTOLOGY_CHOICES, SCOREABLE_OUTPUT_TYPES, get_model


# Aggregation type choices (subset of AggregationType)
AGG_CHOICES = {
    "DIFF_MEAN": "Diff mean (ALT – REF)",
    "LOG_FOLD_CHANGE": "Log fold change",
    "ABS_DIFF_MEAN": "Absolute diff mean",
}


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

@module.ui
def ism_analysis_ui():
    return ui.div(
        ui.h2("In Silico Mutagenesis (ISM)", class_="mb-1"),
        ui.p(
            "Score every possible single-base substitution within a target region to identify "
            "functionally important positions. Results are displayed as a sequence logo. "
            "Use a 16 KB context window for best performance.",
            class_="text-muted mb-3",
        ),
        ui.div(
            ui.tags.strong("Note: "),
            "ISM can be slow – each batch of ~32 variants requires a separate API call. "
            "Keep the ISM region small (≤ 256 bp) and context window short (16 KB) to "
            "minimise run time.",
            class_="alert alert-warning",
        ),
        ui.layout_sidebar(
            # ── Sidebar ────────────────────────────────────────────────────
            ui.sidebar(
                ui.h5("Context interval"),
                ui.input_text(
                    "chromosome",
                    "Chromosome",
                    value="chr20",
                    placeholder="e.g. chr1",
                ),
                ui.input_numeric(
                    "centre_position",
                    "Centre position (bp)",
                    value=3_753_200,
                    min=1,
                ),
                ui.input_select(
                    "context_length",
                    "Context window",
                    choices={
                        "SEQUENCE_LENGTH_16KB": "16 KB (recommended)",
                        "SEQUENCE_LENGTH_100KB": "100 KB",
                    },
                    selected="SEQUENCE_LENGTH_16KB",
                ),
                ui.hr(),
                ui.h5("ISM target region"),
                ui.input_numeric(
                    "ism_width",
                    "Width (bp, centred on interval)",
                    value=256,
                    min=1,
                    max=1000,
                    step=16,
                ),
                ui.hr(),
                ui.h5("Scoring"),
                ui.input_select(
                    "output_type",
                    "Output type",
                    choices={t: t.replace("_", " ").title() for t in SCOREABLE_OUTPUT_TYPES},
                    selected="DNASE",
                ),
                ui.input_selectize(
                    "ontology_term",
                    "Tissue / cell type (single)",
                    choices=ONTOLOGY_CHOICES,
                    multiple=False,
                    selected="EFO:0002067",
                    options={"placeholder": "Select an ontology term…"},
                ),
                ui.input_text(
                    "custom_ontology",
                    "Custom ontology term",
                    placeholder="e.g. EFO:0002067",
                ),
                ui.input_select(
                    "aggregation_type",
                    "Aggregation",
                    choices=AGG_CHOICES,
                    selected="DIFF_MEAN",
                ),
                ui.input_numeric(
                    "mask_width",
                    "Center mask width (bp)",
                    value=501,
                    min=1,
                    step=10,
                ),
                ui.hr(),
                ui.input_action_button(
                    "run_btn",
                    "Run ISM",
                    class_="btn btn-primary w-100",
                ),
                width=320,
                bg="#f8f9fa",
            ),
            # ── Main panel ─────────────────────────────────────────────────
            ui.div(
                ui.output_ui("status_ui"),
                ui.output_plot("ism_plot", height="300px"),
                ui.output_ui("top_positions_ui"),
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

@module.server
def ism_analysis_server(input, output, session, api_key_rv):

    _result = reactive.Value(None)
    _error = reactive.Value(None)

    # ── Run ISM ──────────────────────────────────────────────────────────────
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
            from alphagenome.models import dna_client, variant_scorers
            from alphagenome.data import genome
            from alphagenome.interpretation import ism

            # Build context interval centred on the chosen position
            centre = int(input.centre_position())
            half = 1  # genome.Interval needs start < end
            raw_interval = genome.Interval(
                chromosome=input.chromosome().strip(),
                start=centre - half,
                end=centre + half,
            )
            ctx_length = getattr(dna_client, input.context_length())
            sequence_interval = raw_interval.resize(ctx_length)
            ism_interval = sequence_interval.resize(int(input.ism_width()))

            # Build scorer
            ot_name = input.output_type()
            agg_type = getattr(variant_scorers.AggregationType, input.aggregation_type())
            scorer = variant_scorers.CenterMaskScorer(
                requested_output=getattr(dna_client.OutputType, ot_name),
                width=int(input.mask_width()),
                aggregation_type=agg_type,
            )

            # Ontology term for filtering results
            ont_term = input.custom_ontology().strip() or input.ontology_term()
            if not ont_term:
                _error.set("Select an ontology term.")
                return

            ui.notification_show(
                "Running ISM… this may take several minutes.", duration=None, id="ism_notif"
            )
            model = get_model(key)
            raw_scores = model.score_ism_variants(
                interval=sequence_interval,
                ism_interval=ism_interval,
                variant_scorers=[scorer],
            )

            # Extract scalar per variant matching the chosen ontology term
            def _extract_score(adata):
                mask = adata.var["ontology_curie"] == ont_term
                vals = adata.X[:, mask]
                if vals.size == 0:
                    # Fallback: use mean across all tracks
                    vals = adata.X.mean(axis=1, keepdims=True)
                return float(vals.mean())

            scalars = [_extract_score(pair[0]) for pair in raw_scores]
            variants_list = [pair[0].uns["variant"] for pair in raw_scores]

            ism_matrix = ism.ism_matrix(scalars, variants=variants_list)

            _result.set((ism_matrix, ism_interval, ot_name, ont_term, scalars))
            ui.notification_remove("ism_notif")
            ui.notification_show("ISM complete.", type="message", duration=4)

        except Exception as exc:
            ui.notification_remove("ism_notif")
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
                ui.tags.strong("Run ISM"),
                ".",
                class_="alert alert-info",
            )
        _, ism_interval, ot_name, ont_term, scalars = _result()
        return ui.div(
            f"{len(scalars)} variants scored | Region: {ism_interval} | "
            f"Output: {ot_name} | Ontology: {ont_term}",
            class_="alert alert-success",
        )

    # ── Sequence logo plot ───────────────────────────────────────────────────
    @render.plot
    def ism_plot():
        data = _result()
        if data is None:
            return

        ism_matrix, ism_interval, ot_name, ont_term, _ = data
        from alphagenome.visualization import plot_components

        fig = plot_components.plot(
            components=[
                plot_components.SeqLogo(
                    scores=ism_matrix,
                    scores_interval=ism_interval,
                    ylabel=f"ISM {ot_name} ({ont_term})",
                )
            ],
            interval=ism_interval,
            fig_width=35,
        )
        return fig if fig is not None else plt.gcf()

    # ── Top positions table ──────────────────────────────────────────────────
    @render.ui
    def top_positions_ui():
        data = _result()
        if data is None:
            return ui.div()

        import numpy as np
        import pandas as pd

        ism_matrix, ism_interval, *_ = data
        # ism_matrix shape: (n_positions, 4)
        bases = ["A", "C", "G", "T"]
        pos_scores = np.abs(ism_matrix).max(axis=1)
        top_idx = np.argsort(pos_scores)[::-1][:20]

        rows = []
        for idx in top_idx:
            genomic_pos = ism_interval.start + int(idx)
            best_base = bases[int(np.argmax(np.abs(ism_matrix[idx])))]
            rows.append({
                "Genomic position": f"{ism_interval.chromosome}:{genomic_pos}",
                "Local index": int(idx),
                "Best base": best_base,
                "Max |score|": round(float(pos_scores[idx]), 6),
            })

        df = pd.DataFrame(rows)
        return ui.div(
            ui.tags.h5("Top 20 most influential positions", class_="mt-4"),
            ui.HTML(
                df.to_html(
                    classes="table table-sm table-striped table-bordered",
                    index=False,
                )
            ),
        )
