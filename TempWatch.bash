while true; do
find /home/llm/otherhome/llm/comfy/ComfyUI/temp -type f -mmin +10 -delete
find /home/llm/otherhome/llm/comfy/ComfyUI/output -type f -mmin +10 -delete
find /home/llm/otherhome/llm/comfy/ComfyUI/input -type f -mmin +10 -delete
find /home/llm/otherhome/llm/DiscordAIBot/out -type f -mmin +10 -delete
find /home/llm/.cache/thumbnails -type f -mmin +10 -delete
date
echo temp files cleared
sleep 60
done
