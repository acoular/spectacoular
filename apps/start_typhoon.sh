#!/bin/bash
bokeh serve --show Measurement_App --args --device=typhoon --blocksize=4096 --config_name="settings_typhoon.ini"
