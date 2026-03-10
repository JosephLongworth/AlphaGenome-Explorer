"""
Sequence Prediction module – predict genomic tracks from a raw DNA sequence.
"""
from shiny import module, ui, render, reactive, req
import matplotlib.pyplot as plt

from shared import (
    ONTOLOGY_CHOICES,
    ALL_OUTPUT_TYPES,
    SEQUENCE_LENGTH_OPTIONS,
    get_model,
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
                    "DNA Sequence",
                    value="GATTACA",
                    rows=4,
                    placeholder="A, T, G, C, N …",
                ),
                ui.input_select(
                    "seq_length",
                    "Pad to length",
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
                    selected=["DNASE"],
                ),
                ui.hr(),
                ui.h5("Tissues / cell types"),
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
                    "Custom ontology term",
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
            _result.set((output_obj, out_types))
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

        output_obj, out_types = data
        from alphagenome.visualization import plot_components

        components = []
        for ot_name in out_types:
            track_data = getattr(output_obj, ot_name.lower(), None)
            if track_data is not None:
                components.append(
                    plot_components.Tracks(track_data, title=ot_name.replace("_", " "))
                )

        if not components:
            return

        # Derive interval from first available track (may be None for raw sequences)
        interval = getattr(components[0], "interval", None) or getattr(
            getattr(output_obj, out_types[0].lower(), None), "interval", None
        )

        fig = plot_components.plot(components=components, interval=interval)
        return fig if fig is not None else plt.gcf()

    # ── Metadata tables ─────────────────────────────────────────────────────
    @render.ui
    def metadata_ui():
        data = _result()
        if data is None:
            return ui.div()

        output_obj, out_types = data
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
