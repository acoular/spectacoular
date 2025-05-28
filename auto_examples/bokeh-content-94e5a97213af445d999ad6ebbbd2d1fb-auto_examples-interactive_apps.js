(function() {
  const fn = function() {
    'use strict';
    (function(root) {
      function now() {
        return new Date();
      }
    
      const force = false;
    
      if (typeof root._bokeh_onload_callbacks === "undefined" || force === true) {
        root._bokeh_onload_callbacks = [];
        root._bokeh_is_loading = undefined;
      }
    
    
    const element = document.getElementById("e503301c-3eac-450c-8969-1cacffb69b9f");
        if (element == null) {
          console.warn("Bokeh: autoload.js configured with elementid 'e503301c-3eac-450c-8969-1cacffb69b9f' but no matching script tag was found.")
        }
      function run_callbacks() {
        try {
          root._bokeh_onload_callbacks.forEach(function(callback) {
            if (callback != null)
              callback();
          });
        } finally {
          delete root._bokeh_onload_callbacks
        }
        console.debug("Bokeh: all callbacks have finished");
      }
    
      function load_libs(css_urls, js_urls, callback) {
        if (css_urls == null) css_urls = [];
        if (js_urls == null) js_urls = [];
    
        root._bokeh_onload_callbacks.push(callback);
        if (root._bokeh_is_loading > 0) {
          console.debug("Bokeh: BokehJS is being loaded, scheduling callback at", now());
          return null;
        }
        if (js_urls == null || js_urls.length === 0) {
          run_callbacks();
          return null;
        }
        console.debug("Bokeh: BokehJS not loaded, scheduling load and callback at", now());
        root._bokeh_is_loading = css_urls.length + js_urls.length;
    
        function on_load() {
          root._bokeh_is_loading--;
          if (root._bokeh_is_loading === 0) {
            console.debug("Bokeh: all BokehJS libraries/stylesheets loaded");
            run_callbacks()
          }
        }
    
        function on_error(url) {
          console.error("failed to load " + url);
        }
    
        for (let i = 0; i < css_urls.length; i++) {
          const url = css_urls[i];
          const element = document.createElement("link");
          element.onload = on_load;
          element.onerror = on_error.bind(null, url);
          element.rel = "stylesheet";
          element.type = "text/css";
          element.href = url;
          console.debug("Bokeh: injecting link tag for BokehJS stylesheet: ", url);
          document.body.appendChild(element);
        }
    
        for (let i = 0; i < js_urls.length; i++) {
          const url = js_urls[i];
          const element = document.createElement('script');
          element.onload = on_load;
          element.onerror = on_error.bind(null, url);
          element.async = false;
          element.src = url;
          console.debug("Bokeh: injecting script tag for BokehJS library: ", url);
          document.head.appendChild(element);
        }
      };
    
      function inject_raw_css(css) {
        const element = document.createElement("style");
        element.appendChild(document.createTextNode(css));
        document.body.appendChild(element);
      }
    
      const js_urls = ["https://cdn.bokeh.org/bokeh/release/bokeh-3.7.3.min.js", "https://cdn.bokeh.org/bokeh/release/bokeh-gl-3.7.3.min.js", "https://cdn.bokeh.org/bokeh/release/bokeh-widgets-3.7.3.min.js", "https://cdn.bokeh.org/bokeh/release/bokeh-tables-3.7.3.min.js", "https://cdn.bokeh.org/bokeh/release/bokeh-mathjax-3.7.3.min.js"];
      const css_urls = [];
    
      const inline_js = [    function(Bokeh) {
          Bokeh.set_log_level("info");
        },
        function(Bokeh) {
          (function() {
            const fn = function() {
              Bokeh.safely(function() {
                (function(root) {
                  function embed_document(root) {
                  const docs_json = '{"bb37226e-c0ab-4c2b-bd48-77defef1cc02":{"version":"3.7.3","title":"Bokeh Application","roots":[{"type":"object","name":"Row","id":"p1227","attributes":{"children":[{"type":"object","name":"Column","id":"p1226","attributes":{"children":[{"type":"object","name":"Slider","id":"p1225","attributes":{"title":"f/Hz","start":400.0,"end":25600.0,"value":4000.0,"step":400}},{"type":"object","name":"GridPlot","id":"p1181","attributes":{"rows":null,"cols":null,"toolbar":{"type":"object","name":"Toolbar","id":"p1180"},"children":[[{"type":"object","name":"NumericInput","id":"p1171","attributes":{"width":150,"title":"x_min","description":"minimum  x-value","value":-0.2,"mode":"float"}},0,0],[{"type":"object","name":"NumericInput","id":"p1172","attributes":{"width":150,"title":"x_max","description":"maximum  x-value","value":0.2,"mode":"float"}},0,1],[{"type":"object","name":"NumericInput","id":"p1173","attributes":{"width":150,"title":"y_min","description":"minimum  y-value","value":-0.2,"mode":"float"}},1,0],[{"type":"object","name":"NumericInput","id":"p1174","attributes":{"width":150,"title":"y_max","description":"maximum  y-value","value":0.2,"mode":"float"}},1,1],[{"type":"object","name":"NumericInput","id":"p1175","attributes":{"width":150,"title":"z","description":"position on z-axis","value":-0.3,"mode":"float"}},2,0],[{"type":"object","name":"NumericInput","id":"p1176","attributes":{"width":150,"title":"increment","description":"step size","value":0.01,"mode":"float"}},2,1],[{"type":"object","name":"NumericInput","id":"p1177","attributes":{"disabled":true,"width":150,"title":"nxsteps","description":"number of grid points along x-axis","value":41}},3,0],[{"type":"object","name":"NumericInput","id":"p1178","attributes":{"disabled":true,"width":150,"title":"nysteps","description":"number of grid points along y-axis","value":41}},3,1],[{"type":"object","name":"NumericInput","id":"p1179","attributes":{"disabled":true,"width":150,"title":"size","description":"overall number of grid points","value":1681}},4,0]]}}]}},{"type":"object","name":"Figure","id":"p1183","attributes":{"x_range":{"type":"object","name":"DataRange1d","id":"p1184"},"y_range":{"type":"object","name":"DataRange1d","id":"p1185"},"x_scale":{"type":"object","name":"LinearScale","id":"p1193"},"y_scale":{"type":"object","name":"LinearScale","id":"p1194"},"title":{"type":"object","name":"Title","id":"p1186","attributes":{"text":"Acoular Three Sources"}},"renderers":[{"type":"object","name":"GlyphRenderer","id":"p1222","attributes":{"data_source":{"type":"object","name":"ColumnDataSource","id":"p1209","attributes":{"selected":{"type":"object","name":"Selection","id":"p1210","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1211"},"data":{"type":"map","entries":[["bfdata",[{"type":"ndarray","array":{"type":"bytes","data":"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"},"shape":[41,41],"dtype":"float64","order":"little"}]],["x",[-0.2]],["y",[-0.2]],["dw",[0.4]],["dh",[0.4]]]}}},"view":{"type":"object","name":"CDSView","id":"p1223","attributes":{"filter":{"type":"object","name":"AllIndices","id":"p1224"}}},"glyph":{"type":"object","name":"Image","id":"p1216","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"dw":{"type":"field","field":"dw"},"dh":{"type":"field","field":"dh"},"global_alpha":{"type":"value","value":0.9},"image":{"type":"field","field":"bfdata"},"color_mapper":{"type":"object","name":"LinearColorMapper","id":"p1212","attributes":{"palette":["#440154","#440357","#45085B","#460B5E","#470F62","#471265","#471669","#481A6C","#481D6F","#482172","#482374","#472777","#472A79","#462D7C","#46317E","#45347F","#443781","#433A83","#423D84","#424085","#404387","#3F4788","#3E4989","#3D4C89","#3C4E8A","#3A528B","#39548B","#38578C","#365A8C","#355C8C","#345F8D","#33618D","#31648D","#30678D","#2F698D","#2E6C8E","#2D6E8E","#2C718E","#2B738E","#2A768E","#29798E","#287A8E","#277D8E","#267F8E","#25828E","#24848D","#23878D","#22898D","#228B8D","#218E8C","#20908C","#1F938B","#1F958B","#1E988A","#1E9A89","#1E9C89","#1E9F88","#1FA187","#20A485","#21A685","#23A883","#25AB81","#27AD80","#2AB07E","#2CB17D","#30B47A","#35B778","#38B976","#3DBB74","#40BD72","#45BF6F","#49C16D","#4FC369","#55C666","#59C764","#60C960","#64CB5D","#6BCD59","#70CE56","#77D052","#7ED24E","#83D34B","#8BD546","#90D643","#97D83E","#9DD93A","#A5DA35","#ADDC30","#B2DD2C","#BADE27","#BFDF24","#C7E01F","#CDE01D","#D4E11A","#DCE218","#E1E318","#E9E419","#EEE51B","#F6E61F","#FDE724"],"low":70.12265028597311,"high":90.12265028597311}}}},"nonselection_glyph":{"type":"object","name":"Image","id":"p1218","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"dw":{"type":"field","field":"dw"},"dh":{"type":"field","field":"dh"},"global_alpha":{"type":"value","value":0.1},"image":{"type":"field","field":"bfdata"},"color_mapper":{"id":"p1212"}}},"muted_glyph":{"type":"object","name":"Image","id":"p1220","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"dw":{"type":"field","field":"dw"},"dh":{"type":"field","field":"dh"},"global_alpha":{"type":"value","value":0.2},"image":{"type":"field","field":"bfdata"},"color_mapper":{"id":"p1212"}}}}}],"toolbar":{"type":"object","name":"Toolbar","id":"p1192","attributes":{"tools":[{"type":"object","name":"HoverTool","id":"p1205","attributes":{"renderers":"auto"}},{"type":"object","name":"ResetTool","id":"p1206"},{"type":"object","name":"PanTool","id":"p1207"},{"type":"object","name":"WheelZoomTool","id":"p1208","attributes":{"renderers":"auto"}}]}},"left":[{"type":"object","name":"LinearAxis","id":"p1200","attributes":{"ticker":{"type":"object","name":"BasicTicker","id":"p1201","attributes":{"mantissas":[1,2,5]}},"formatter":{"type":"object","name":"BasicTickFormatter","id":"p1202"},"major_label_policy":{"type":"object","name":"AllLabels","id":"p1203"}}}],"below":[{"type":"object","name":"LinearAxis","id":"p1195","attributes":{"ticker":{"type":"object","name":"BasicTicker","id":"p1196","attributes":{"mantissas":[1,2,5]}},"formatter":{"type":"object","name":"BasicTickFormatter","id":"p1197"},"major_label_policy":{"type":"object","name":"AllLabels","id":"p1198"}}}],"center":[{"type":"object","name":"Grid","id":"p1199","attributes":{"axis":{"id":"p1195"}}},{"type":"object","name":"Grid","id":"p1204","attributes":{"dimension":1,"axis":{"id":"p1200"}}}]}}]}}]}}';
                  const render_items = [{"docid":"bb37226e-c0ab-4c2b-bd48-77defef1cc02","roots":{"p1227":"e503301c-3eac-450c-8969-1cacffb69b9f"},"root_ids":["p1227"]}];
                  root.Bokeh.embed.embed_items(docs_json, render_items);
                  }
                  if (root.Bokeh !== undefined) {
                    embed_document(root);
                  } else {
                    let attempts = 0;
                    const timer = setInterval(function(root) {
                      if (root.Bokeh !== undefined) {
                        clearInterval(timer);
                        embed_document(root);
                      } else {
                        attempts++;
                        if (attempts > 100) {
                          clearInterval(timer);
                          console.log("Bokeh: ERROR: Unable to run BokehJS code because BokehJS library is missing");
                        }
                      }
                    }, 10, root)
                  }
                })(window);
              });
            };
            if (document.readyState != "loading") fn();
            else document.addEventListener("DOMContentLoaded", fn);
          })();
        },
    function(Bokeh) {
        }
      ];
    
      function run_inline_js() {
        for (let i = 0; i < inline_js.length; i++) {
          inline_js[i].call(root, root.Bokeh);
        }
      }
    
      if (root._bokeh_is_loading === 0) {
        console.debug("Bokeh: BokehJS loaded, going straight to plotting");
        run_inline_js();
      } else {
        load_libs(css_urls, js_urls, function() {
          console.debug("Bokeh: BokehJS plotting callback run at", now());
          run_inline_js();
        });
      }
    }(window));
  };
  if (document.readyState != "loading") fn();
  else document.addEventListener("DOMContentLoaded", fn);
})();