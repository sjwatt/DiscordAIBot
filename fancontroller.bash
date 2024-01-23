#!/bin/bash

# Script to monitor GPU temperatures, adjust fan speeds with hysteresis at each level, and print temperatures

# Check if required commands exist
if ! command -v nvidia-smi &> /dev/null || ! command -v ./IPMICFG-Linux.x86_64 &> /dev/null; then
    echo "Required commands not found. Exiting."
    exit 1
fi

# Initialize variables
current_fan_speed="unknown"
high_temp_threshold=60
very_high_temp_threshold=80
hysteresis=10  # Hysteresis for temperature changes

# Function to set fan speed
set_fan_speed() {
    local speed=$1
    if [ "$current_fan_speed" != "$speed" ]; then
        echo "Changing fan speed to $speed"
        ./IPMICFG-Linux.x86_64 -fan "$speed"
        current_fan_speed="$speed"
    fi
}

# Main loop
while true; do
    temps=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits)
    max_temp=0

    for temp in $temps; do
        if (( temp > max_temp )); then
            max_temp=$temp
        fi
    done

    echo "Maximum GPU Temperature: $max_temp°C"

    if (( max_temp >= very_high_temp_threshold )) || { [ "$current_fan_speed" == "1" ] && (( max_temp >= very_high_temp_threshold - hysteresis )); }; then
        set_fan_speed 1
    elif (( max_temp >= high_temp_threshold )) || { [ "$current_fan_speed" == "4" ] && (( max_temp >= high_temp_threshold - hysteresis )); }; then
        set_fan_speed 4
    elif (( max_temp < high_temp_threshold - hysteresis )); then
        set_fan_speed 2
    fi

    sleep 5 # Adjust sleep time as needed
done

