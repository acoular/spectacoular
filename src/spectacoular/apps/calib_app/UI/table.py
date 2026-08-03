"""Calibration channel overview table."""

from bokeh.models import DataTable, TableColumn, ColumnDataSource, StringFormatter, NumberFormatter, InlineStyleSheet, NumberEditor
from bokeh.layouts import column
from .colors import ACC, S1, S2, BD, T1, T2, T3, GRN, RED


class CalibTable:
    """Bokeh DataTable showing calibration status for all channels.
    
    Displays channel number, calibration factor, frequency, level, unit, and calibration time.
    
    Attributes:
        source: ColumnDataSource backing the table data.
        table: The DataTable widget.
        layout: Column layout containing the table.
    """

    def __init__(self):
        columns = [
            TableColumn(
                field="channel", title="Channel",
                formatter=StringFormatter(font_style="bold", text_color=ACC),
            ),
            TableColumn(
                field="factor", title="Calib. Factor",
                formatter=NumberFormatter(format="0.0000", font_style="bold", text_color=GRN),
            ),
            TableColumn(
                field="band", title="Calib. Freq.",
                formatter=NumberFormatter(format="0.0", text_color=T3),
            ),
            TableColumn(
                field="magnitude", title="Calib. Lvl.",
                formatter=NumberFormatter(format="0.0000", text_color=T1),
            ),
            TableColumn(
                field="unit", title="Calib. Lvl. Unit",
                formatter=StringFormatter(text_color=T3),
            ),
            TableColumn(
                field="calib_time", title="Calib. Time (s)",
                formatter=StringFormatter(text_color=T3),
            ),
            TableColumn(
                field="stability_tolerance", title="Stab. Tol. (dB)",
                formatter=StringFormatter(text_color=T3),
            )
        ]
        table_style = InlineStyleSheet(css=f"""
            :host {{
                font-size: .8rem;
                font-family: inherit;
                border: 1px solid {BD};
                border-radius: 12px;
                overflow: hidden;
                background-color: {S1};
                box-shadow: 0 1px 2px rgba(0,0,0,.06);
            }}

            /* Header */
            .slick-header-columns {{
                background-color: {S1};
                border-bottom: 1px solid {BD};
            }}
            .slick-header-column {{
                background-color: {S1};
                color: {T3};
                font-weight: 700;
                font-size: .66rem;
                letter-spacing: .06em;
                padding: 12px 16px;
                border-right: none;
            }}
            .slick-header-column:hover {{
                background-color: {S1};
                color: {T2};
            }}

            /* Sortier-Icons komplett ausblenden */
            .slick-sort-indicator,
            .slick-sort-indicator-asc,
            .slick-sort-indicator-desc,
            .slick-header-column .slick-sort-indicator {{
                display: none !important;
            }}

            /* Zellen */
            .slick-cell {{
                padding: 10px 16px;
                border-right: none;
                display: flex;
                align-items: center;
            }}

            /* Zeilen: keine Zebra-Streifen, dafür klare Trennlinien wie im Referenzbild */
            .slick-row {{
                background-color: {S1};
                color: {T1};
                border-bottom: 1px solid {BD}88;
                transition: background-color .12s ease;
            }}
            .slick-row.odd {{
                background-color: {S1};
            }}
            .slick-row:hover,
            .slick-row.odd:hover {{
                background-color: {ACC}0f;
            }}

            /* Auswahl */
            .slick-row.selected,
            .slick-cell.selected {{
                background-color: {ACC}22 !important;
            }}
            .slick-cell.active {{
                border: 1px solid {ACC};
            }}

            /* Scrollbar */
            ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}
            ::-webkit-scrollbar-track {{
                background: {S1};
            }}
            ::-webkit-scrollbar-thumb {{
                background: {BD};
                border-radius: 4px;
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: {ACC};
            }}
        """)
        self.source = ColumnDataSource(dict(
            channel=[], factor=[], band=[], magnitude=[], unit=[],calib_time=[],stability_tolerance=[]
        ))
        self.table = DataTable(
            source=self.source,
            columns=columns,
            sizing_mode="stretch_width",
            height=600,
            index_position=None,
            stylesheets=[table_style],
        )
        self.layout = column(self.table, sizing_mode="stretch_width")

    def refresh(self, ui_state):
        channels = ui_state.all_channels()
        if not channels:                               
            self.table.source.data = dict(
                channel=[], factor=[], band=[], magnitude=[], unit=[], calib_time = []
            )
            return
        sorted_chs = sorted(channels.keys())
        pad_len = len(str(sorted_chs[-1]))  # Auto-pad based on channel count
        self.table.source.data = dict(
            channel=["CH " + str(ch + 1).zfill(pad_len) for ch in sorted_chs],
            factor=[channels[ch]['final_factor'] for ch in sorted_chs],
            band=[channels[ch]['band'] for ch in sorted_chs],
            magnitude=[channels[ch]['magnitude'] for ch in sorted_chs],
            unit=[channels[ch]['unit'] for ch in sorted_chs],
            calib_time=[channels[ch]['calib_time'] for ch in sorted_chs],
            stability_tolerance=[channels[ch]['stability_tolerance'] for ch in sorted_chs],
        )
