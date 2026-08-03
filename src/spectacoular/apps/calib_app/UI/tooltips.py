"""Info tooltip components for UI labels."""

# We might want to longterm migrate to the Bokeh build in tool tips

from .colors import ACC, T1, T2

from bokeh.models import Div


def info_label(label: str, tooltip: str, width: int = 160,
               direction: str = "down") -> Div:
    """Create a labeled Div with an info icon and tooltip.

    Args:
        label: The visible label text.
        tooltip: The tooltip text shown on hover.
        width: Width of the tooltip in pixels.
        direction: "up" or "down" - which direction the tooltip opens.

    Returns
    -------
        Div: Bokeh Div widget with embedded HTML/CSS for the tooltip.
    """
    cls = "tooltip-up" if direction == "up" else "tooltip-down"
    vpos = "bottom: -5px;" if direction == "up" else "top: -5px;"

    return Div(text=f"""
        <span style='font-size:.7rem;color:{T2};font-weight:600;'>{label}</span>
        <span class='info-icon'>ⓘ
            <span class='tooltip-text {cls}'>{tooltip}</span>
        </span>
        <style>
            .info-icon {{
                position: relative; cursor: pointer;
                color: {ACC}; font-size: .75rem;
            }}
            .tooltip-text {{
                visibility: hidden; background-color: {T1}; color: #fff;
                font-size: .68rem; border-radius: 5px; padding: 5px 8px;
                position: absolute; z-index: 100;
                left: 120%; width: {width}px; white-space: normal;
            }}
            .tooltip-up   {{ {vpos} }}
            .tooltip-down {{ {vpos} }}
            .info-icon:hover .tooltip-text {{ visibility: visible; }}
        </style>
    """, sizing_mode='stretch_width')
