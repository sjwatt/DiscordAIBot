#!/bin/bash

# Check if required commands exist
if ! command -v nvidia-smi &> /dev/null || ! command -v ./IPMICFG-Linux.x86_64 &> /dev/null; then
    echo "Required commands not found. Exiting."
    exit 1
fi

prev_fan_setting="none"

while true; do
    temps=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits)
    hightemp=false

    for temp in $temps; do
        if [ "$temp" -gt 60 ]; then
            hightemp=true
            break
        fi
    done

    if $hightemp && [ "$prev_fan_setting" != "high" ]; then
        echo "Setting Fans High"
        ./IPMICFG-Linux.x86_64 -fan 1
        prev_fan_setting="high"
    elif ! $hightemp && [ "$prev_fan_setting" != "low" ]; then
        echo "Setting Fans Low"
        ./IPMICFG-Linux.x86_64 -fan 2
        prev_fan_setting="low"
    fi

    sleep 5 # Adjust sleep time as needed
done
