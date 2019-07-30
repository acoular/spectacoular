#!/bin/bash
source activate ac3
bokeh serve --show Measurement_App --args --device=phantom --blocksize=256
