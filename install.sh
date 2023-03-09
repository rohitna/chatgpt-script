#!/bin/sh

## Requires:
# - `espanso`
# - `python3`


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

# Install python dependencies
pip3 install pyperclip
pip3 install requests

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
model = gpt-3.5-turbo
temperature = 1.0
system_role = A helpful assistant
address = https://api.openai.com/v1/chat/completions
api_key = REPLACE_WITH_YOUR_OPENAI_API_KEY
conversation_timeout_minutes = 15
db_file = ~/openai_chatgpt/chats.db
EOF

# Create an Espanso package called openai
mkdir $CONFIG/match/packages/openai

# Repo url
url="https://raw.githubusercontent.com/rohitna/chatgpt-script/main"

# Files to download
script="openai_chatgpt.py"
espanso="package.yml"


# destination directory
dest_dir="$CONFIG/match/packages/openai"

# create the destination directory if it doesn't exist
mkdir -p "$dest_dir"

# download the files using curl
curl -L -o "$dest_dir/$script" "$url/$script"
curl -L -o "$dest_dir/$espanso" "$url/$espanso"

# Get the path to the Python executable
python_path=$(which python3)

# Replace the PYTHON_ENV line in the package.yml with the new path
default_path="~/.virtualenvs/openai/bin/python3"
sed -i '' "s|$old_path|$new_path|g" "$dest_dir/$espanso"

# restart espanso
espanso restart

