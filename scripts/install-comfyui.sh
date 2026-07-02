#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMFY="$ROOT/comfyui"
[[ -d "$COMFY/.git" ]] || git clone https://github.com/Comfy-Org/ComfyUI.git "$COMFY"
[[ -x "$COMFY/.venv/bin/python" ]] || python3 -m venv "$COMFY/.venv"
PYTHON="$COMFY/.venv/bin/python"
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
"$PYTHON" -m pip install -r "$COMFY/requirements.txt"
mkdir -p "$COMFY/models/checkpoints" "$COMFY/models/controlnet"
download() {
  local url=$1 target=$2 partial="$2.part"
  [[ -s "$target" ]] && return
  curl --fail --location --show-error --retry 3 --continue-at - --output "$partial" "$url"
  mv "$partial" "$target"
}
download \
  https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive/resolve/main/v1-5-pruned-emaonly-fp16.safetensors \
  "$COMFY/models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors"
download \
  https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_v11f1p_sd15_depth_fp16.safetensors \
  "$COMFY/models/controlnet/control_v11f1p_sd15_depth_fp16.safetensors"
"$PYTHON" -c "import torch; assert torch.cuda.is_available(); print('ComfyUI CUDA ready:', torch.__version__, torch.cuda.get_device_name(0))"
echo "ComfyUI is installed. Start it with scripts/start-comfyui.sh"
