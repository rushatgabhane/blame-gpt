#!/bin/bash

set -euo pipefail # exit on first error

cd /home/blamegpt/blame-gpt
git pull

echo "pulled latest code ✅"

bash ./migrate.sh

sudo systemctl restart fastapi
echo "restarted fastapi server ✅"
