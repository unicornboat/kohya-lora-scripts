#!/usr/bin/bash

echo "Installing torch & xformers..."

# 检查 CUDA 版本
cuda_version=$(nvidia-smi | grep -oiP 'CUDA Version: \K[\d\.]+')
if [ -z "$cuda_version" ]; then
    cuda_version=$(nvcc --version | grep -oiP ' Release \K[\d\.]+')
fi
cuda_major_version=$(echo "$cuda_version" | awk -F'.' '{print $1}')
cuda_minor_version=$(echo "$cuda_version" | awk -F'.' '{print $2}')

echo "CUDA Version: $cuda_version"

# 根据 CUDA 版本安装 torch 和 xformers
if (( cuda_major_version >= 12 )); then
    echo "Installing torch 2.6.0+cu124 (updated for torchaudio compatibility)"
    pip install torch==2.6.0+cu124 torchvision==0.21.0+cu124 torchaudio==2.6.0+cu124 --extra-index-url https://download.pytorch.org/whl/cu124
    pip install --no-deps xformers==0.0.28.post1 --extra-index-url https://download.pytorch.org/whl/cu124
elif (( cuda_major_version == 11 && cuda_minor_version >= 8 )); then
    echo "Installing torch 2.4.0+cu118"
    pip install torch==2.4.0+cu118 torchvision==0.19.0+cu118 torchaudio==2.4.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
    pip install --no-deps xformers==0.0.27.post2+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
elif (( cuda_major_version == 11 && cuda_minor_version >= 6 )); then
    echo "Installing torch 1.12.1+cu116"
    pip install torch==1.12.1+cu116 torchvision==0.13.1+cu116 torchaudio==1.12.1+cu116 --extra-index-url https://download.pytorch.org/whl/cu116
    pip install --upgrade git+https://github.com/facebookresearch/xformers.git@0bad001ddd56c080524d37c84ff58d9cd030ebfd
    pip install triton==2.0.0.dev20221202
elif (( cuda_major_version == 11 && cuda_minor_version >= 2 )); then
    echo "Installing torch 1.12.1+cu113"
    pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==1.12.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113
    pip install --upgrade git+https://github.com/facebookresearch/xformers.git@0bad001ddd56c080524d37c84ff58d9cd030ebfd
    pip install triton==2.0.0.dev20221202
else
    echo "Unsupported CUDA version: $cuda_version"
    exit 1
fi

echo "Installing dependencies from requirements.txt..."
pip install --upgrade -r requirements.txt

echo "Install completed"
