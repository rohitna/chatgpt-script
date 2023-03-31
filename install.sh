#!/bin/sh

## Requires:
# - `espanso`
# - `python3`

# Set default branch to 'main'
BRANCH="main"

# Check if an argument for branch is provided
if [ $# -eq 1 ]; then
  BRANCH=$1
fi


echo "Checking whether Espanso is installed..."
if command -v espanso > /dev/null; then
    echo "Espanso is installed"
else
    echo "Error: Espanso is not installed"
    exit 1
fi

echo "Checking whether Python 3 is installed..."
if command -v python3 > /dev/null; then
    echo "Python 3 is installed"
else
    echo "Error: Python 3 is not installed"
    exit 1
fi

# both espanso and python3 should be installed now
echo "espanso and python3 are installed"

# Repo url
url="https://raw.githubusercontent.com/rohitna/chatgpt-script/$BRANCH"

# Install python dependencies
pip3 install -r "$url/requirements.txt"

# Get the espanso config path
ESPANSO_CONFIG_PATH="$(espanso path config)"

# Check if the current shell is zsh
if [ -n "$ZSH_VERSION" ]; then
    echo "Detected zsh shell"
    # Add espanso path to .zshrc
    echo "export CONFIG=\"$ESPANSO_CONFIG_PATH\"" >> ~/.zshrc
# Otherwise, assume it's bash
else
    echo "Detected bash shell"
    # Add espanso path to .bashrc file
    echo "export CONFIG=\"$ESPANSO_CONFIG_PATH\"" >> ~/.bashrc
fi

# Create the openai_chatgpt folder in the home directory
mkdir ~/openai_chatgpt

# Create and populate the config.ini file
cat <<EOF > ~/openai_chatgpt/config.ini
[default]
model = gpt-3.5-turbo
temperature = 1.0
system_role = A helpful assistant
address = https://api.openai.com/v1/chat/completions
api_key = REPLACE_WITH_YOUR_OPENAI_API_KEY
conversation_timeout_minutes = 15
db_file = ~/openai_chatgpt/chats.db
allow_clipboard = True
transcription_model = whisper-1
record_duration = 10
record = False
recording_path = ~/openai_chatgpt/prompt.wav
sound_effect = ~/openai_chatgpt/bell.wav
EOF

# Create an Espanso package called openai
mkdir "$ESPANSO_CONFIG_PATH/match/packages/openai"

# Files to download
script="openai_chatgpt.py"
espanso="package.yml"
sound_effect="bell.wav"


# destination directory
dest_dir="$ESPANSO_CONFIG_PATH/match/packages/openai"

# create the destination directory if it doesn't exist
mkdir -p "$dest_dir"

# download the files using curl
curl -L -o "$dest_dir/$script" "$url/$script"
curl -L -o "$dest_dir/$espanso" "$url/$espanso"
curl -L -o "~/openai_chatgpt" "$url/$sound_effect"

# Get the path to the Python executable
python_path=$(which python3)

# Replace the PYTHON_ENV line in the package.yml with the new path
default_path="~/.virtualenvs/openai/bin/python3"
sed -i '' "s|$default_path|$python_path|g" "$dest_dir/$espanso"

# restart espanso
espanso restart

# Check if the current shell is zsh
if [ -n "$ZSH_VERSION" ]; then
    source ~/.zshrc
# Otherwise, assume it's bash
else
    source ~/.bashrc
fi