"""Toggle widget for showing/hiding UI sections."""

from bokeh.models import Toggle


class VisibilitySwitch:
    """Toggle button that changes color when active/inactive.

    Used to show/hide UI sections like the FFT plot, table, etc.

    Attributes
    ----------
        widget: The underlying Toggle widget.
    """

    def __init__(self, label="",* , active=True):
        """Initialize the visibility toggle.

        Args:
            label: Text label for the toggle button.
            active: Initial state (True = visible).
        """
        self.widget = Toggle(
            label=label,
            active=active,
            button_type="primary" if active else "default",
            sizing_mode="stretch_width"
        )
        self.widget.on_change("active", self._on_toggle)

    def _on_toggle(self, _attr, _old, new):
        """Update button style when toggle state changes."""
        self.widget.button_type = "primary" if new else "default"
