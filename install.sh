#!/usr/bin/env bash
set -euo pipefail

CUDA_VARIANT="cu124"
PY_VERSION="python3"
VENV_DIR="venv"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cpu)
      CUDA_VARIANT="cpu"
      shift
      ;;
    --venv)
      VENV_DIR="$2"
      shift 2
      ;;
    --py)
      PY_VERSION="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

sudo apt-get update
sudo apt-get install -y \
  ${PY_VERSION}-venv ${PY_VERSION}-dev \
  python3-gi gobject-introspection libgirepository1.0-dev \
  libgl1 \
  libaravis-0.8-0 libaravis-dev gir1.2-aravis-0.8 \
  aravis-tools \
  libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio

if [[ "${CUDA_VARIANT}" == "cu124" ]]; then
  sudo apt-get install -y nvidia-driver-550 || true
fi

${PY_VERSION} -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip

pip install -r requirements.txt

if [[ "${CUDA_VARIANT}" == "cu124" ]]; then
  pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu124
  echo "CUDA-enabled PyTorch installed. A system reboot is required to load the NVIDIA driver."
  echo "After reboot, activate and verify with:"
  echo "  source ${VENV_DIR}/bin/activate"
  echo "  python -c \"import torch; print('cuda_available=', torch.cuda.is_available()); print('device=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu')\""
else
  pip install torch==2.6.0 torchvision==0.21.0
  echo "CPU-only install complete. Activate with: source ${VENV_DIR}/bin/activate"
fi

