#!/bin/bash

set -euo pipefail # exit on first error

cd /home/blamegpt/blame-gpt
git pull
echo "pulled latest code ✅"

pip install -r requirements.txt
echo "installed requirements ✅"

bash ./migrate.sh
echo "ran db migrations ✅"

sudo systemctl restart fastapi
echo "restarted fastapi server ✅"
