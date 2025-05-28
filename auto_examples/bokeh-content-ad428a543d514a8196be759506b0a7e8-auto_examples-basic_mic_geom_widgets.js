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
    
    
    const element = document.getElementById("aa50ab1b-56a0-4cac-aaa3-06a2a964ff15");
        if (element == null) {
          console.warn("Bokeh: autoload.js configured with elementid 'aa50ab1b-56a0-4cac-aaa3-06a2a964ff15' but no matching script tag was found.")
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
                  const docs_json = '{"af53e623-372b-4be6-8e58-eb475e41e9d5":{"version":"3.7.3","title":"Bokeh Application","roots":[{"type":"object","name":"Row","id":"p1167","attributes":{"children":[{"type":"object","name":"Figure","id":"p1107","attributes":{"x_range":{"type":"object","name":"DataRange1d","id":"p1108"},"y_range":{"type":"object","name":"DataRange1d","id":"p1109"},"x_scale":{"type":"object","name":"LinearScale","id":"p1117"},"y_scale":{"type":"object","name":"LinearScale","id":"p1118"},"title":{"type":"object","name":"Title","id":"p1110","attributes":{"text":"Microphone Geometry"}},"renderers":[{"type":"object","name":"GlyphRenderer","id":"p1144","attributes":{"data_source":{"type":"object","name":"ColumnDataSource","id":"p1135","attributes":{"selected":{"type":"object","name":"Selection","id":"p1136","attributes":{"indices":[],"line_indices":[]}},"selection_policy":{"type":"object","name":"UnionRenderers","id":"p1137"},"data":{"type":"map","entries":[["x",{"type":"ndarray","array":{"type":"bytes","data":"RBuFxkH5xT/lgIMUQV7RP1dHW4Nhets/aEmjqW6z4T+GOPyMEJDmP7Zue2knZuI/7MT0ozJc2z+e+tVWy4HRPzA5WHmu4b4/DMO80QuasT9bk7BntojIP3zvb9Be/dU/FPRW3gdQ4D8FP1ZiMbnWP28FpUyQL8c/6cnU26GMoz8kHsVDXFymvzveJtS6KsW/EQTctJjm2L8sJ8ICbyPjv3RzrZpA4dq/ZE9WmgEfzr9D5s9ZlEmvv+5xiLOA27i/xMDGNwwNz7+BE4MgPS7Zvzq7KaOZkOK/Ph5Tp57d5b+Wcc3J/XHgvwIksdyGPNO/9MvPKaLIw79CLUC6XO1Wv3DSsO/1e7m/DVMKoyEvzr9qrIPXvLfZv+PT+XZmYOK/qJcQWqyE5r+yc9CuDbjhv1sEKSXCDty/799hf34k0r9+EotX2lu7vwc/bEdDVoe/zIbwwORsv7+qweXFSgvPv9McMHo0Vtm/ZRd5Suhd3L9sq7fYfV/Rv2cTb4MrN7O/VUG+5Hw6rj+UGsNk9u7FPzciYd1Nt9E/5iaV6crZ3z+P+I8x6fLlP65BZ+tDK+A/q6R2COEG1T8VPiNdqIbCP1e4H8+yV8U/eV4dDOR11D/fF2dxnmjdP9kZqW5jgOQ/8mvk7Rrq1j/xHj/S4rfNP2ZLD3AsG6Q/NVDKuGodrj8="},"shape":[64,1],"dtype":"float64","order":"little"}],["y",{"type":"ndarray","array":{"type":"bytes","data":"TplKKEV3kT+lidI5mr7AP9rIlmGzDro/jnCXU7uMgj/0lvT1UU27P34s9vdPQMw/RTazPUoK0j+sy3WPdgDSPzZvXbCi5sg/sPO9Jm4s1T+llkjKX1/bP4rkBbrxrN0/9lik0Exs3D9BfBQ5OprkPwyC0yoWmeM/yvubxN4j4T+3SHdjg03mPwmC+qgceeI/WUKfEWob4T/7PvsVW7bZP7sTIbKe09c/6q8GEXHf2z990CWv3bzaP7olYt+IbdA/1sEV3lL/0T+IhTQMGhjMPz4QgWxXPc0/NKU0HEh3kT/F5nGFaA61Pz7eXce1Krc/aOSiQ6ievT/XN7byICq/P662ftQIeLy/+q8OqID5sL/BTVh4HcWXv/hlF6mDfry/ltVszIhezr8N4paez1HVvzSkMSoOP8i/rAu8tl4jyr9nypMTCSDRv3D5KT28b9i/rWX9Kf9B379BhPIdgN3Wv68iyco0/Ne/QUUNWtOS4b9DvuHEq2rhvx/uPlXyQuW/vXMytcgd4r9mx7AE/qLmv610+B0jJuK/RtpbBKWs3r9f2HEui2rTv4lkb/mt1dO/wN4qc+aD2r8qB6bfLezbvx2ytmaB79G/0ocVC8+t0L+rmU0xG2XEv4BsXy5MoMC/9OQ8kZedpb/cn0lqugG+v/+DcE7qoMq/lBvLD+oPsL8="},"shape":[64,1],"dtype":"float64","order":"little"}],["z",{"type":"ndarray","array":{"type":"bytes","data":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="},"shape":[64,1],"dtype":"float64","order":"little"}]]}}},"view":{"type":"object","name":"CDSView","id":"p1145","attributes":{"filter":{"type":"object","name":"AllIndices","id":"p1146"}}},"glyph":{"type":"object","name":"Circle","id":"p1141","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"radius":{"type":"value","value":0.02},"fill_color":{"type":"value","value":"#1F77B4"},"fill_alpha":{"type":"value","value":0.4}}},"nonselection_glyph":{"type":"object","name":"Circle","id":"p1142","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"radius":{"type":"value","value":0.02},"line_alpha":{"type":"value","value":0.1},"fill_color":{"type":"value","value":"#1F77B4"},"fill_alpha":{"type":"value","value":0.1},"hatch_alpha":{"type":"value","value":0.1}}},"muted_glyph":{"type":"object","name":"Circle","id":"p1143","attributes":{"x":{"type":"field","field":"x"},"y":{"type":"field","field":"y"},"radius":{"type":"value","value":0.02},"line_alpha":{"type":"value","value":0.2},"fill_color":{"type":"value","value":"#1F77B4"},"fill_alpha":{"type":"value","value":0.2},"hatch_alpha":{"type":"value","value":0.2}}}}}],"toolbar":{"type":"object","name":"Toolbar","id":"p1116","attributes":{"tools":[{"type":"object","name":"HoverTool","id":"p1129","attributes":{"renderers":"auto"}},{"type":"object","name":"ZoomInTool","id":"p1130","attributes":{"renderers":"auto"}},{"type":"object","name":"ZoomOutTool","id":"p1131","attributes":{"renderers":"auto"}},{"type":"object","name":"ResetTool","id":"p1132"},{"type":"object","name":"LassoSelectTool","id":"p1133","attributes":{"renderers":"auto","overlay":{"type":"object","name":"PolyAnnotation","id":"p1134","attributes":{"syncable":false,"level":"overlay","visible":false,"xs":[],"ys":[],"editable":true,"line_color":"black","line_alpha":1.0,"line_width":2,"line_dash":[4,4],"fill_color":"lightgrey","fill_alpha":0.5}}}},{"type":"object","name":"PointDrawTool","id":"p1165","attributes":{"renderers":[{"id":"p1144"}]}}],"active_tap":{"id":"p1165"}}},"left":[{"type":"object","name":"LinearAxis","id":"p1124","attributes":{"ticker":{"type":"object","name":"BasicTicker","id":"p1125","attributes":{"mantissas":[1,2,5]}},"formatter":{"type":"object","name":"BasicTickFormatter","id":"p1126"},"major_label_policy":{"type":"object","name":"AllLabels","id":"p1127"}}}],"below":[{"type":"object","name":"LinearAxis","id":"p1119","attributes":{"ticker":{"type":"object","name":"BasicTicker","id":"p1120","attributes":{"mantissas":[1,2,5]}},"formatter":{"type":"object","name":"BasicTickFormatter","id":"p1121"},"major_label_policy":{"type":"object","name":"AllLabels","id":"p1122"}}}],"center":[{"type":"object","name":"Grid","id":"p1123","attributes":{"axis":{"id":"p1119"}}},{"type":"object","name":"Grid","id":"p1128","attributes":{"dimension":1,"axis":{"id":"p1124"}}}],"match_aspect":true}},{"type":"object","name":"Column","id":"p1166","attributes":{"width":400,"children":[{"type":"object","name":"NumericInput","id":"p1147","attributes":{"disabled":true,"title":"Aperture/m","description":"array aperture","value":1.4648587220804408}},{"type":"object","name":"NumericInput","id":"p1148","attributes":{"disabled":true,"title":"Number of Mics","description":"number of microphones in the geometry","value":64}},{"type":"object","name":"DataTable","id":"p1159","attributes":{"height":450,"source":{"id":"p1135"},"view":{"type":"object","name":"CDSView","id":"p1163","attributes":{"filter":{"type":"object","name":"AllIndices","id":"p1164"}}},"columns":[{"type":"object","name":"TableColumn","id":"p1150","attributes":{"field":"x","title":"x/m","formatter":{"type":"object","name":"StringFormatter","id":"p1152"},"editor":{"type":"object","name":"NumberEditor","id":"p1149"}}},{"type":"object","name":"TableColumn","id":"p1153","attributes":{"field":"y","title":"y/m","formatter":{"type":"object","name":"StringFormatter","id":"p1155"},"editor":{"id":"p1149"}}},{"type":"object","name":"TableColumn","id":"p1156","attributes":{"field":"z","title":"z/m","formatter":{"type":"object","name":"StringFormatter","id":"p1158"},"editor":{"id":"p1149"}}}],"editable":true}}]}}]}}]}}';
                  const render_items = [{"docid":"af53e623-372b-4be6-8e58-eb475e41e9d5","roots":{"p1167":"aa50ab1b-56a0-4cac-aaa3-06a2a964ff15"},"root_ids":["p1167"]}];
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