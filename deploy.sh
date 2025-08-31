#!/bin/bash

set -euo pipefail # exit on first error

cd /home/blamegpt/blame-gpt
git pull
echo "pulled latest code ✅"

source venv/bin/activate && pip install -r requirements.txt
echo "installed requirements ✅"

bash ./migrate.sh
echo "ran db migrations ✅"

if [ ! -f "./bin/gosec" ]; then
    echo "installing gosec..."
    curl -sfL https://raw.githubusercontent.com/securego/gosec/master/install.sh | sh -s v2.22.8
    echo "installed gosec ✅"
else
    echo "gosec already installed ✅"
fi

sudo systemctl restart fastapi
echo "restarted fastapi server ✅"

