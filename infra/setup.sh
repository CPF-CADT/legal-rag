#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${app_root}"
APP_USER="${app_user}"
MOUNT_POINT="${mount_point}"
REQUESTED_DEVICE="${data_device}"
VENV_PATH="$APP_ROOT/.venv"

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y \
  ca-certificates \
  curl \
  build-essential \
  python3 \
  python3-pip \
  python3-venv \
  python3-dev \
  libnss3 \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libatspi2.0-0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libgtk-3-0 \
  libpango-1.0-0 \
  libcairo2 \
  libasound2t64

mkdir -p "$APP_ROOT" "$MOUNT_POINT"
chown -R "$APP_USER:$APP_USER" "$APP_ROOT" "$MOUNT_POINT"

# On Nitro instances /dev/sdf may appear as an NVMe device. Wait for the
# requested device, then fall back to the unattached 40 GiB data disk.
DATA_DEVICE=""
for _ in $(seq 1 60); do
  if [ -b "$REQUESTED_DEVICE" ]; then
    DATA_DEVICE="$REQUESTED_DEVICE"
    break
  fi

  DATA_DEVICE="$(lsblk -dn -o NAME,SIZE,TYPE | awk '$2 == "40G" && $3 == "disk" {print "/dev/" $1; exit}')"
  if [ -n "$DATA_DEVICE" ] && [ -b "$DATA_DEVICE" ]; then
    break
  fi
  DATA_DEVICE=""
  sleep 5
done

if [ -z "$DATA_DEVICE" ]; then
  echo "Persistent EBS device was not found" >&2
  exit 1
fi

if ! blkid "$DATA_DEVICE" >/dev/null 2>&1; then
  mkfs.ext4 -F "$DATA_DEVICE"
fi

DATA_UUID="$(blkid -s UUID -o value "$DATA_DEVICE")"
grep -q "UUID=$DATA_UUID $MOUNT_POINT" /etc/fstab || \
  echo "UUID=$DATA_UUID $MOUNT_POINT ext4 defaults,nofail 0 2" >> /etc/fstab

mountpoint -q "$MOUNT_POINT" || mount "$MOUNT_POINT"
chown -R "$APP_USER:$APP_USER" "$MOUNT_POINT"

sudo -u "$APP_USER" python3 -m venv "$VENV_PATH"
sudo -u "$APP_USER" "$VENV_PATH/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$VENV_PATH/bin/pip" install \
  requests \
  beautifulsoup4 \
  pandas \
  playwright \
  PyMuPDF \
  google-genai
sudo -u "$APP_USER" "$VENV_PATH/bin/playwright" install chromium

mkdir -p "$APP_ROOT/data-pipeline"
ln -sfn "$MOUNT_POINT" "$APP_ROOT/data-pipeline/data"
chown -h "$APP_USER:$APP_USER" "$APP_ROOT/data-pipeline/data"

mkdir -p "$APP_ROOT/react-client" "$APP_ROOT/bot" "$APP_ROOT/data-pipeline/collection" "$APP_ROOT/data-pipeline/ocr-process" "$APP_ROOT/data-pipeline/automation-process/download" "$APP_ROOT/data-pipeline/automation-process/ocr" "$APP_ROOT/data-pipeline/transformation" "$APP_ROOT/data-pipeline/cleaning" "$APP_ROOT/data-pipeline/testable" "$APP_ROOT/infra"
chown -R "$APP_USER:$APP_USER" "$APP_ROOT"

echo "LegalRAG infrastructure setup completed."
echo "Application root: $APP_ROOT"
echo "Persistent data: $MOUNT_POINT"
echo "Python environment: $VENV_PATH"
