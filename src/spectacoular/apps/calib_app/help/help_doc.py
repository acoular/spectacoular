"""Help documentation page for the calibration application."""

from pathlib import Path
from bokeh.layouts import column
from bokeh.models import Div


def help_doc(doc, log=None):
    """Create a help document page with user guide content.
    
    Loads help.html from the help directory and displays it in a Div.
    Falls back to embedded HTML if the file cannot be loaded.
    
    Args:
        doc: Bokeh document to add the help content to.
        log: Optional logger instance for error reporting.
    """
    try:
        # Read the help HTML file
        help_path = Path(__file__).parent / "help.html"
        with open(help_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        if log:
            log.logger.warning(f"Could not load help.html: {e}. Using fallback content.")
        # Fallback content if the file is not found or there's an error
        html_content = """
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            h2 { color: #3498db; margin-top: 25px; }
        </style>
        <h1>Calibration App User Guide</h1>
        <p>Please check that the help.html file exists in the application directory.</p>
        <p>If you're seeing this message, the help content could not be loaded.</p>
        """
    
    help_content = Div(text=html_content, sizing_mode='stretch_both')
    doc.add_root(column(help_content, sizing_mode='stretch_both'))
    doc.title = "Calibration App Help"


