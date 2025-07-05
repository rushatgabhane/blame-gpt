#!/bin/bash

set -e

# Predefined list of models
MODELS=("llama3" "mistral" "gemma" "codellama" "llava" "phi3" "dolphin-mixtral" "solar")

# Detect OS
OS="$(uname -s)"
echo "Detected OS: $OS"

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo "curl not found. Installing..."
    if [[ "$OS" == "Darwin" ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            echo "Homebrew not found. Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install curl
    elif [[ "$OS" == "Linux" ]]; then
        # Linux
        sudo apt update && sudo apt install -y curl
    else
        echo "Unsupported OS: $OS"
        exit 1
    fi
fi

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama is already installed."
fi

# Check if Ollama service is running
if pgrep -f "ollama serve" > /dev/null; then
    echo "Ollama service is already running."
else
    echo "Starting Ollama service..."
    nohup ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Present model choices
echo ""
echo "Available models:"
for i in "${!MODELS[@]}"; do
    echo "$((i+1)). ${MODELS[$i]}"
done

# Prompt user for choice
read -p "Select a model to run [1-${#MODELS[@]}]: " choice

if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#MODELS[@]}" ]; then
    echo "Invalid selection."
    exit 1
fi

MODEL="${MODELS[$((choice-1))]}"
echo "Pulling and running model: $MODEL",

# Pull and run the model
ollama run "$MODEL"
