"""
AlphaGenome Explorer – Shiny for Python application.

Developed by the Department of Immune and Inflammatory Diseases (DII)
Luxembourg Institute of Health (LIH)

Run with:
    shiny run shiny_app/app.py --reload
"""
import sys
import os

# Ensure the shiny_app directory is on the path so `shared` can be imported
# by the module files regardless of the working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from shiny import App, ui, render, reactive

from modules.landing import landing_ui, landing_server
from modules.sequence_predict import sequence_predict_ui, sequence_predict_server
from modules.interval_predict import interval_predict_ui, interval_predict_server
from modules.variant_predict import variant_predict_ui, variant_predict_server
from modules.ism_analysis import ism_analysis_ui, ism_analysis_server
from shared import DEFAULT_API_KEY

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

_DEV_BANNER = ui.div(
    "UNDER DEVELOPMENT  —  Department of Immune and Inflammatory Diseases (DII)  |  "
    "Luxembourg Institute of Health (LIH)",
    class_="text-center text-white py-1",
    style=(
        "background: #922b21; "
        "font-size: 0.80rem; "
        "letter-spacing: 0.06em; "
        "font-weight: 600;"
    ),
)

app_ui = ui.page_navbar(
    # ── Pages ───────────────────────────────────────────────────────────────
    ui.nav_panel("Home", landing_ui("landing")),
    ui.nav_panel("Sequence Prediction", sequence_predict_ui("seq_pred")),
    ui.nav_panel("Interval Prediction", interval_predict_ui("int_pred")),
    ui.nav_panel("Variant Analysis", variant_predict_ui("var_pred")),
    ui.nav_panel("ISM Analysis", ism_analysis_ui("ism")),

    # ── Settings (right-aligned) ─────────────────────────────────────────────
    ui.nav_spacer(),
    ui.nav_panel(
        "Settings",
        ui.div(
            ui.h2("Settings"),
            ui.card(
                ui.card_header("API Configuration"),
                ui.card_body(
                    ui.p(
                        "Enter your AlphaGenome API key. Obtain one at ",
                        ui.tags.a(
                            "alphagenomedocs.com",
                            href="https://www.alphagenomedocs.com",
                            target="_blank",
                        ),
                        ".",
                    ),
                    ui.p(
                        "The key is stored only in memory for this session. "
                        "To avoid re-entering it each time, set the ",
                        ui.tags.code("ALPHAGENOME_API_KEY"),
                        " environment variable before launching the app.",
                        class_="text-muted small",
                    ),
                    ui.input_password(
                        "api_key",
                        "API Key",
                        value=DEFAULT_API_KEY,
                        width="100%",
                        placeholder="Paste your API key here…",
                    ),
                    ui.input_action_button(
                        "save_key",
                        "Save Key",
                        class_="btn btn-primary mt-2",
                    ),
                    ui.output_ui("key_status"),
                ),
            ),
            class_="container py-4",
            style="max-width: 640px;",
        ),
    ),

    # ── Navbar appearance ────────────────────────────────────────────────────
    title=ui.tags.span(
        ui.tags.img(
            src="https://www.alphagenomedocs.com/_static/logo.png",
            height="24px",
            style="margin-right: 8px; vertical-align: middle;",
            onerror="this.style.display='none'",  # hide if logo 404s
        ),
        "AlphaGenome Explorer",
    ),
    header=_DEV_BANNER,
    bg="#1a252f",
    inverse=True,
    id="main_navbar",
)


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

def server(input, output, session):
    # Shared reactive API key – passed down into every module server
    api_key_rv = reactive.Value(DEFAULT_API_KEY)

    @reactive.effect
    @reactive.event(input.save_key)
    def _save_key():
        api_key_rv.set(input.api_key())
        ui.notification_show("API key saved for this session.", type="message", duration=4)

    @render.ui
    def key_status():
        key = api_key_rv()
        if key:
            visible = key[:4] + "•" * max(0, len(key) - 8) + key[-4:] if len(key) > 8 else "•" * len(key)
            return ui.div(
                ui.tags.span("Key set: ", class_="fw-semibold"),
                visible,
                class_="alert alert-success mt-3 mb-0",
            )
        return ui.div(
            "No API key set. Please paste your key above and click Save.",
            class_="alert alert-warning mt-3 mb-0",
        )

    # Register module servers
    landing_server("landing")
    sequence_predict_server("seq_pred", api_key_rv=api_key_rv)
    interval_predict_server("int_pred", api_key_rv=api_key_rv)
    variant_predict_server("var_pred", api_key_rv=api_key_rv)
    ism_analysis_server("ism", api_key_rv=api_key_rv)


# ---------------------------------------------------------------------------
# App object
# ---------------------------------------------------------------------------

app = App(app_ui, server)
