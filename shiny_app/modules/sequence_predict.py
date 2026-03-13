"""
Sequence Prediction module – predict genomic tracks from a raw DNA sequence.
"""
from shiny import module, ui, render, reactive
import matplotlib.pyplot as plt

from shared import (
    ONTOLOGY_CHOICES,
    ALL_OUTPUT_TYPES,
    SEQUENCE_LENGTH_OPTIONS,
    get_model,
    help_icon,
)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

@module.ui
def sequence_predict_ui():
    return ui.div(
        ui.h2("Sequence Prediction", class_="mb-1"),
        ui.p(
            "Predict genomic track values for a custom DNA sequence. "
            "The sequence is centre-padded with N's to the chosen length.",
            class_="text-muted mb-3",
        ),
        ui.layout_sidebar(
            # ── Sidebar ────────────────────────────────────────────────────
            ui.sidebar(
                ui.h5("Sequence"),
                ui.input_text_area(
                    "sequence",
                    ui.span("DNA Sequence", help_icon(
                        "Enter a raw DNA sequence using A, T, G, C, or N characters. "
                        "It will be centre-padded with N's to reach the chosen length."
                    )),
                    value="GATTACA",
                    rows=4,
                    placeholder="A, T, G, C, N …",
                ),
                ui.input_select(
                    "seq_length",
                    ui.span("Pad to length", help_icon(
                        "The model always operates on a fixed-length sequence. "
                        "Your input is centred and flanked with N's to fill this window. "
                        "Larger windows capture more distal regulatory context but cost more API time."
                    )),
                    choices={v: k for k, v in SEQUENCE_LENGTH_OPTIONS.items()},
                    selected="SEQUENCE_LENGTH_1MB",
                ),
                ui.input_select(
                    "organism",
                    ui.span("Organism", help_icon(
                        "The species whose regulatory grammar the model was trained on. "
                        "Choose Human for hg38-based sequences, Mouse for mm10."
                    )),
                    choices={
                        "HOMO_SAPIENS": "Human (Homo sapiens)",
                        "MUS_MUSCULUS": "Mouse (Mus musculus)",
                    },
                ),
                ui.hr(),
                ui.h5("Output types", help_icon(
                    "Select which genomic assay tracks to predict. "
                    "Each type measures a different aspect of gene regulation. "
                    "See the Guide page for full descriptions."
                )),
                ui.input_checkbox_group(
                    "output_types",
                    None,
                    choices={t: t.replace("_", " ").title() for t in ALL_OUTPUT_TYPES},
                    selected=["DNASE"],
                ),
                ui.hr(),
                ui.h5("Tissues / cell types", help_icon(
                    "Filter predictions to specific biological contexts. "
                    "Each term is an ontology identifier (UBERON, CL, or EFO) "
                    "representing a tissue or cell type. See the Guide page for the full list."
                )),
                ui.input_selectize(
                    "ontology_terms",
                    None,
                    choices=ONTOLOGY_CHOICES,
                    multiple=True,
                    selected=["UBERON:0002048"],
                    options={"placeholder": "Select ontology terms…"},
                ),
                ui.input_text(
                    "custom_ontology",
                    ui.span("Custom ontology term", help_icon(
                        "Enter any valid ontology CURIE not in the list above, "
                        "e.g. UBERON:0001114. It will be added to the selected terms."
                    )),
                    placeholder="e.g. UBERON:0001114",
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
                ui.output_plot("prediction_plot", height="500px"),
                ui.output_ui("metadata_ui"),
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

@module.server
def sequence_predict_server(input, output, session, api_key_rv):

    _result = reactive.Value(None)
    _error = reactive.Value(None)

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

            seq = input.sequence().strip().upper()
            if not seq:
                _error.set("Please enter a DNA sequence.")
                return

            seq_length = getattr(dna_client, input.seq_length())
            padded = seq.center(seq_length, "N")

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

            ui.notification_show("Running prediction… this may take a moment.", duration=None, id="pred_notif")
            model = get_model(key)
            output_obj = model.predict_sequence(
                sequence=padded,
                requested_outputs=requested,
                ontology_terms=ont_terms,
                organism=organism,
            )
            _result.set((output_obj, out_types, seq_length))
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
                "Configure parameters in the sidebar, then click ",
                ui.tags.strong("Run Prediction"),
                ".",
                class_="alert alert-info",
            )
        return ui.div()

    # ── Plot ────────────────────────────────────────────────────────────────
    @render.plot
    def prediction_plot():
        data = _result()
        if data is None:
            return

        output_obj, out_types, seq_length = data
        from alphagenome.visualization import plot_components
        from alphagenome.data import genome

        # Raw sequence predictions have no genomic coordinates – build a
        # synthetic interval so plot_components.plot() has something to anchor on.
        synthetic_interval = genome.Interval(
            chromosome="sequence", start=0, end=seq_length
        )

        components = []
        for ot_name in out_types:
            track_data = getattr(output_obj, ot_name.lower(), None)
            if track_data is None:
                continue
            # Set interval on track_data if absent (required by plot_components)
            if getattr(track_data, "interval", None) is None:
                try:
                    track_data.interval = synthetic_interval
                except (AttributeError, TypeError):
                    object.__setattr__(track_data, "interval", synthetic_interval)
            components.append(plot_components.Tracks(track_data))

        if not components:
            return

        interval = getattr(
            getattr(output_obj, out_types[0].lower(), None), "interval", None
        ) or synthetic_interval

        fig = plot_components.plot(components=components, interval=interval)
        return fig if fig is not None else plt.gcf()

    # ── Metadata tables ─────────────────────────────────────────────────────
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
