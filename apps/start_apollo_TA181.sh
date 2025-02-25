#!/bin/bash
bokeh serve --show Measurement_App --args --device=apollo --blocksize=4096 --inventory_no=TA181 --config_name="settings_apollo.ini"
