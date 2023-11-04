#!/bin/bash

#set an environment variable to tell everything the root directory of the bot, which is the parent directory of this script
export BOT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo "Bot root: $BOT_ROOT"
export CHATBOT_ROOT="/mnt/nvme0n1p2/text-generation-webui"


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

# Start the chat bot
start_chatbot() {
    echo "Starting chatbot"
    (cd $CHATBOT_ROOT; python3 $CHATBOT_ROOT/server.py --listen --extension api --model ehartford_Wizard-Vicuna-13B-Uncensored &)
}

# Stop the chat bot
stop_chatbot() {
    pkill -f "python3 $CHATBOT_ROOT/server.py"
}

# Restart the chat bot
restart_chatbot() {
    stop_chatbot
    start_chatbot
}

#redirect stdout and stderr to a log file
#exec &>> /home/llm/DiscordBot/startup.log

while true; do
    read -p "Enter command (start/stop/restart) and component (comfy/bot/tempwatch/all): " command component
    case "$command" in
        start)
            case "$component" in
                comfy)
                    echo "Starting comfy"
                    start_comfy
                    ;;
                bot)
                    echo "Starting bot"
                    start_bot
                    ;;
                tempwatch)
                    echo "Starting tempwatch"
                    start_tempwatch
                    ;;
                chatbot)
                    echo "Starting chatbot"
                    start_chatbot
                    ;;
                all)
                    echo "Starting all"
                    start_comfy
                    start_bot
                    start_tempwatch
                    start_chatbot
                    ;;
                *)
                    echo "Invalid component"
                    ;;
            esac
            ;;
        stop)
            case "$component" in
                comfy)
                    echo "Stopping comfy"
                    stop_comfy
                    ;;
                bot)
                    echo "Stopping bot"
                    stop_bot
                    ;;
                tempwatch)
                    echo "Stopping tempwatch"
                    stop_tempwatch
                    ;;
                chatbot)
                    echo "Stopping chatbot"
                    stop_chatbot
                    ;;
                all)
                    echo "Stopping all"
                    stop_comfy
                    stop_bot
                    stop_tempwatch
                    stop_chatbot
                    ;;
                *)
                    echo "Invalid component"
                    ;;
            esac
            ;;
        restart)
            case "$component" in
                comfy)
                    echo "Restarting comfy"
                    restart_comfy
                    ;;
                bot)
                    echo "Restarting bot"
                    restart_bot
                    ;;
                tempwatch)
                    echo "Restarting tempwatch"
                    restart_tempwatch
                    ;;
                chatbot)
                    echo "Restarting chatbot"
                    restart_chatbot
                    ;;
                all)
                    echo "Restarting all"
                    restart_comfy
                    restart_bot
                    restart_tempwatch
                    restart_chatbot
                    ;;
                *)
                    echo "Invalid component"
                    ;;
            esac
            ;;
        exit)
            echo "Exiting"
            stop_bot
            stop_comfy
            stop_tempwatch
            stop_chatbot
            exit 0
            ;;
        *)
            echo "Invalid command"
            ;;
    esac
done