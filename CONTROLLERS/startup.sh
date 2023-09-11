#!/bin/bash

exec python3 /app/feeding_control.py &
exec python3 /app/light_control.py &
exec python3 /app/statisticalanalysis_control.py &
exec python3 /app/temperature_control.py &
exec python3 /app/water_level_control.py