#!/bin/bash
bokeh serve --show Measurement_App --args --device=tornado --blocksize=4096 --syncorder 10142 10112 10125 10126
