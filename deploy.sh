#!/bin/bash

if [ ! -f "./bin/gosec" ]; then
    echo "installing gosec..."
    curl -sfL https://raw.githubusercontent.com/securego/gosec/master/install.sh | sh -s v2.22.8
    echo "installed gosec ✅"
else
    echo "gosec already installed ✅"
fi
