#!/bin/bash
source activate ac3
bokeh serve --show Measurement_App --args --device=uma16 --blocksize=256
