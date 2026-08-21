/*
 * Browser-side theme switch callback for Spectacoular.
 *
 * This file is loaded by `themes.client_theme_switch_code()` and used as the
 * JavaScript callback for the Bokeh theme Switch in `BaseApp`.  Bokeh executes
 * it in the browser whenever the switch changes.  In Bokeh CustomJS callbacks,
 * `cb_obj` is the model that triggered the callback; here it is the Switch.
 *
 * Important design choice: Avoid replacing doc.theme during interactive switches.
 * We do NOT replace `Document.theme` when the user toggles the switch.  A
 * Bokeh `Document.theme` replacement is coordinated with the Python server and
 * patches many Bokeh models over the websocket.  In widget-heavy apps this can
 * cause a visible staggered repaint.  Instead, this callback updates ordinary
 * DOM/CSS state immediately in the browser and directly patches the few plot
 * properties that cannot be represented as CSS variables.
 */

/* The Switch is active for light mode and inactive for dark mode. */
const mode = cb_obj.active ? 'light' : 'dark';

/*
 * Set `<html data-theme="light|dark">`.
 *
 * The CSS in `page.css` is written around this attribute.  When the attribute
 * changes, the browser recalculates CSS variables such as
 * `--spectacoular-widget-color`.  Bokeh widget shadow DOMs inherit those
 * variables and update without a Python round trip.
 */
document.documentElement.setAttribute('data-theme', mode);

/*
 * Concrete plot colors injected by Python.
 *
 * `themes.client_theme_switch_code()` replaces the placeholder below with JSON
 * like `{dark: {...}, light: {...}}`.  We need real color strings here because
 * canvas/SVG plot properties are Bokeh model attributes, not normal DOM CSS.
 */
const themes = __SPECTACOULAR_PLOT_THEME_COLORS__;

/*
 * Set several Bokeh model properties only if that model supports them.
 *
 * `model.properties` contains the property names available on a BokehJS model.
 * The guard lets us call this helper on different model types safely.  The
 * `{sync: false}` option is crucial: it tells BokehJS to update the browser
 * model only and not send these cosmetic changes back to Python over the
 * websocket.
 */
function set_if_present(model, attrs) {
  const changes = {};
  for (const [name, value] of Object.entries(attrs)) {
    if (model.properties != null && name in model.properties && model[name] !== value) {
      changes[name] = value;
    }
  }
  if (Object.keys(changes).length > 0) {
    model.setv(changes, {sync: false});
  }
}

/*
 * Recolor plot-related Bokeh models that are not controlled by CSS variables.
 *
 * Widgets are HTML elements and can inherit CSS variables.  Plots are different:
 * their backgrounds, axes, grids, titles, and colorbars are stored as Bokeh
 * model properties and are rendered by BokehJS.  Therefore we walk through all
 * models in the current Bokeh document and patch the color properties locally.
 */
function apply_plot_theme(mode) {
  const colors = themes[mode];

  /*
   * Prefer the document that owns the switch.  The global fallback supports
   * older/embedded Bokeh contexts where `cb_obj.document` is unavailable.
   */
  const doc = cb_obj.document ?? (globalThis.Bokeh?.documents?.[0] ?? null);
  if (doc == null || colors == null) {
    return;
  }

  for (const model of doc.all_models) {
    if (model.type === 'Plot' || model.type === 'Figure') {
      set_if_present(model, {
        background_fill_color: colors.background,
        border_fill_color: colors.background,
        outline_line_color: colors.border,
      });
    } else if (model.type.endsWith('Axis')) {
      set_if_present(model, {
        axis_line_color: colors.border,
        major_label_text_color: colors.muted,
        axis_label_text_color: colors.text,
      });
    } else if (model.type === 'Grid') {
      set_if_present(model, {grid_line_color: colors.border});
    } else if (model.type === 'Title') {
      set_if_present(model, {text_color: colors.text});
    } else if (model.type === 'ColorBar') {
      set_if_present(model, {
        background_fill_color: colors.background,
        title_text_color: colors.text,
        major_label_text_color: colors.muted,
        major_tick_line_color: colors.border,
        border_line_color: colors.border,
      });
    } else if (model.tags != null && model.tags.includes('spectacoular-beamforming-colormap')) {
      set_if_present(model, {palette: colors.beamforming_palette});
    }
  }
}

apply_plot_theme(mode);
