#!/bin/bash

cd /home/blamegpt/blame-gpt
git pull
sudo systemctl restart fastapi
