while true; do
find /mnt/nvme0n1p2/home/llm/comfy/ComfyUI/temp -type f -mmin +10 -delete
find /mnt/nvme0n1p2/home/llm/comfy/ComfyUI/output -type f -mmin +10 -delete
find /mnt/nvme0n1p2/home/llm/comfy/ComfyUI/input -type f -mmin +10 -delete
find /mnt/nvme0n1p2/home/llm/DiscordAIBot/out -type f -mmin +10 -delete
find /home/llm/.cache/thumbnails -type f -mmin +10 -delete
date
echo temp files cleared
sleep 60
done
