#!/bin/bash
bokeh serve --show Measurement_App --port 5008 --args --device=sounddevice --blocksize=256
