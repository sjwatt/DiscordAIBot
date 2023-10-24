#!/bin/bash

#set an environment variable to tell everything the root directory of the bot, which is the parent directory of this script
export BOT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo "Bot root: $BOT_ROOT"


# Read the list of ports from config.properties
# the list of ports is in the format PORTS=port1,pot2,port3...
IFS='=' read -r -a ports <<< $(grep PORTS $BOT_ROOT/config.properties)
IFS=',' read -r -a comfy_ports <<< ${ports[1]}

echo "Comfy ports: ${comfy_ports[@]}"

# Function to start comfy instances
start_comfy() {
    #make sure that comfy isn't already running
    stop_comfy
    for port in "${comfy_ports[@]}"; do
        echo "Starting comfy instance on port $port"
        python3 $BOT_ROOT/../comfy/ComfyUI/main.py --cuda-device 0 --port "$port" --listen &
    done
}

# Function to stop comfy instances
stop_comfy() {
    pkill -f "python3 $BOT_ROOT/../comfy/ComfyUI/main.py"
}

# Function to restart comfy instances
restart_comfy() {
    stop_comfy
    start_comfy
}

# Function to start bot
start_bot() {
    echo "Starting bot"
    python3 $BOT_ROOT/bot.py --debug &
}

# Function to stop bot
stop_bot() {
    pkill -f "python3 $BOT_ROOT/bot.py"
}

# Function to restart bot
restart_bot() {
    stop_bot
    start_bot
}

# Function to start tempwatch
start_tempwatch() {
    ./TempWatch.bash &
}

# Function to stop tempwatch
stop_tempwatch() {
    pkill -f "$BOT_ROOT/TempWatch.bash"
}

# Function to restart tempwatch
restart_tempwatch() {
    stop_tempwatch
    start_tempwatch
}

# Start comfy instances, bot and tempwatch
start_comfy
start_bot
start_tempwatch

# Loop to listen for commands
while true; do
    read -p "Enter command (start/stop/restart) and component (comfy/bot/tempwatch/all): " command component
    case "$command" in
        start)
            case "$component" in
                comfy)
                    start_comfy
                    ;;
                bot)
                    start_bot
                    ;;
                tempwatch)
                    start_tempwatch
                    ;;
                all)
                    start_comfy
                    start_bot
                    start_tempwatch
                    ;;
                *)
                    echo "Invalid component"
                    ;;
            esac
            ;;
        stop)
            case "$component" in
                comfy)
                    stop_comfy
                    ;;
                bot)
                    stop_bot
                    ;;
                tempwatch)
                    stop_tempwatch
                    ;;
                all)
                    stop_comfy
                    stop_bot
                    stop_tempwatch
                    ;;
                *)
                    echo "Invalid component"
                    ;;
            esac
            ;;
        restart)
            case "$component" in
                comfy)
                    restart_comfy
                    ;;
                bot)
                    restart_bot
                    ;;
                tempwatch)
                    restart_tempwatch
                    ;;
                all)
                    restart_comfy
                    restart_bot
                    restart_tempwatch
                    ;;
                *)
                    echo "Invalid component"
                    ;;
            esac
            ;;
        *)
            echo "Invalid command"
            ;;
    esac
done
