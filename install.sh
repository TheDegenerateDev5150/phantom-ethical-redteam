#!/bin/bash
set -e

echo "========================================"
echo "  Phantom – Ethical RedTeam"
echo "  Installer v1.5.0"
echo "========================================"
echo ""

# ─────────────────────────────────────────
# STEP 0 — LLM Provider selection
# ─────────────────────────────────────────
echo "[ STEP 0 / 3 ] LLM Provider"
echo "-----------------------------------------"
echo "  1) Anthropic  (Claude sonnet-4-6)   — https://console.anthropic.com"
echo "  2) OpenAI     (ChatGPT 5.4)         — https://platform.openai.com"
echo "  3) xAI        (Grok 4.20 Beta)      — https://console.x.ai"
echo "  4) Google     (Gemini 3)            — https://aistudio.google.com/apikey"
echo "  5) Mistral    (mistral-large)       — https://console.mistral.ai"
echo "  6) DeepSeek   (DeepSeek 3.2)        — https://platform.deepseek.com"
echo "  7) Ollama     (local — deepseek-r1:3.2 default)"
echo ""

while true; do
    read -rp "Choose provider [1-7] : " provider_choice
    case "$provider_choice" in
        1) PROVIDER="anthropic"; ENV_VAR="ANTHROPIC_API_KEY"; KEY_PREFIX="sk-ant-" ;;
        2) PROVIDER="openai";    ENV_VAR="OPENAI_API_KEY";    KEY_PREFIX="sk-" ;;
        3) PROVIDER="grok";      ENV_VAR="XAI_API_KEY";       KEY_PREFIX="xai-" ;;
        4) PROVIDER="gemini";    ENV_VAR="GEMINI_API_KEY";    KEY_PREFIX="" ;;
        5) PROVIDER="mistral";   ENV_VAR="MISTRAL_API_KEY";   KEY_PREFIX="" ;;
        6) PROVIDER="deepseek";  ENV_VAR="DEEPSEEK_API_KEY";  KEY_PREFIX="" ;;
        7) PROVIDER="ollama";    ENV_VAR="";                  KEY_PREFIX="" ;;
        *) echo "⚠️  Invalid choice. Enter a number between 1 and 7." ; continue ;;
    esac
    break
done

echo "✅ Provider selected : $PROVIDER"
echo ""

# ─────────────────────────────────────────
# STEP 1 — API Key
# ─────────────────────────────────────────
echo "[ STEP 1 / 3 ] API Key"
echo "-----------------------------------------"

if [ "$PROVIDER" = "ollama" ]; then
    read -rp "Ollama host [http://localhost:11434] : " OLLAMA_HOST
    OLLAMA_HOST=${OLLAMA_HOST:-http://localhost:11434}
    sed -i "s|^provider:.*|provider: \"$PROVIDER\"|" config.yaml
    sed -i "s|^ollama_host:.*|ollama_host: \"$OLLAMA_HOST\"|" config.yaml
    > .env
    echo "✅ Ollama configured (host: $OLLAMA_HOST)"
else
    while true; do
        read -rsp "Enter your $ENV_VAR : " api_key
        echo ""
        if [ -z "$KEY_PREFIX" ] || [[ "$api_key" == ${KEY_PREFIX}* ]]; then
            if [ ${#api_key} -gt 10 ]; then
                break
            fi
        fi
        echo "⚠️  Invalid key. Try again."
    done

    echo "${ENV_VAR}=${api_key}" > .env
    sed -i "s|^provider:.*|provider: \"$PROVIDER\"|" config.yaml
    echo "✅ API key saved to .env"
fi
echo ""

# ─────────────────────────────────────────
# STEP 2 — Authorized scope
# ─────────────────────────────────────────
echo "[ STEP 2 / 3 ] Authorized Scope"
echo "-----------------------------------------"

while true; do
    read -rp "Target URL (e.g. https://target.example.com) : " scope_url
    if [[ "$scope_url" == http* && "$scope_url" != "https://xxx" ]]; then
        break
    fi
    echo "⚠️  Invalid URL or placeholder. Enter a real authorized target."
done

read -rp "Authorization note (e.g. 'Pentest contract signed 2026-03-15') : " scope_note
read -rp "Engagement date (e.g. 2026-03-15) : " scope_date

mkdir -p scopes logs
cat > scopes/current_scope.md <<SCOPE
**Scope autorisé :** $scope_url

**Autorisation :** $scope_note

**Date :** $scope_date
SCOPE

echo "✅ Scope saved to scopes/current_scope.md"
echo ""

# ─────────────────────────────────────────
# STEP 3 — Dependencies
# ─────────────────────────────────────────
echo "[ STEP 3 / 3 ] Installing dependencies"
echo "-----------------------------------------"

# Base packages (available in apt)
sudo apt update -q
sudo apt install -y curl git nmap sqlmap bettercap golang-go python3 python3-pip python3-venv

# nuclei — not in apt, install via ProjectDiscovery official script
if ! command -v nuclei &>/dev/null; then
    echo "→ Installing nuclei..."
    curl -s https://api.github.com/repos/projectdiscovery/nuclei/releases/latest \
        | grep "browser_download_url.*linux_amd64.zip" \
        | cut -d '"' -f 4 \
        | wget -qi - -O /tmp/nuclei.zip
    unzip -q /tmp/nuclei.zip -d /tmp/nuclei_bin
    sudo mv /tmp/nuclei_bin/nuclei /usr/local/bin/nuclei
    rm -rf /tmp/nuclei.zip /tmp/nuclei_bin
    echo "✅ nuclei installed"
fi

# ffuf — not in apt, download binary from GitHub
if ! command -v ffuf &>/dev/null; then
    echo "→ Installing ffuf..."
    curl -s https://api.github.com/repos/ffuf/ffuf/releases/latest \
        | grep "browser_download_url.*linux_amd64.tar.gz" \
        | cut -d '"' -f 4 \
        | wget -qi - -O /tmp/ffuf.tar.gz
    tar -xzf /tmp/ffuf.tar.gz -C /tmp/
    sudo mv /tmp/ffuf /usr/local/bin/ffuf
    rm -f /tmp/ffuf.tar.gz
    echo "✅ ffuf installed"
fi

# Zphisher (educational phishing templates)
if [ ! -d "tools/zphisher_repo" ]; then
    git clone https://github.com/htr-tech/zphisher.git tools/zphisher_repo 2>/dev/null
    chmod +x tools/zphisher_repo/zphisher.sh
fi

# CyberStrikeAI
mkdir -p bin
if [ ! -d "tools/cyberstrike_repo" ]; then
    git clone https://github.com/Ed1s0nZ/CyberStrikeAI.git tools/cyberstrike_repo 2>/dev/null || true
fi
if [ -d "tools/cyberstrike_repo" ]; then
    (cd tools/cyberstrike_repo && go build -o ../../bin/cyberstrike ./cmd/cyberstrike 2>/dev/null) \
        && echo "✅ CyberStrikeAI built" \
        || echo "⚠️  CyberStrikeAI build failed — verify Go installation"
fi

# Python virtual environment + dependencies
# (avoids "externally managed environment" error on Ubuntu 23.04+)
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
echo "✅ Python dependencies installed in .venv"

echo ""
echo "========================================"
echo "  ✅ Installation complete !"
echo "========================================"
echo ""
echo "  Provider : $PROVIDER"
echo "  Scope    : $scope_url"
echo ""
echo "  To start Phantom :"
echo ""
echo "    source .venv/bin/activate"
if [ "$PROVIDER" != "ollama" ]; then
    echo "    export \$(cat .env)"
fi
echo "    export PATH=\$PATH:\$(pwd)/bin:/usr/local/bin"
echo "    python3 agent/main.py"
echo ""
echo "========================================"
