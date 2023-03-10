# ChatGPT script for usage with Espanso

This repository maintains a python script that can be used together with [Espanso](https://espanso.org) to interact with chatGPT anywhere from your computer.

## Standalone usage of the python script

The script `openai_chatgpt.py` returns the chatGPT chat completion using the prompt from the clipboard and previous prompts from the database as context.

### Options:

| Option                                      | Description                                           | Default Value                |
| ------------------------------------------- | ----------------------------------------------------- | ----------------------------|
| `-h, --help`                                | Show help message and exit                            | -                           |
| `--model MODEL`                             | Model name                                            | `gpt-3.5-turbo`             |
| `--temperature TEMPERATURE`                 | Temperature value                                     | `1.0`                       |
| `--system_role SYSTEM_ROLE`                 | System role                                           | `A helpful assistant`           |
| `--address ADDRESS`                         | API address                                           | `https://api.openai.com/v1/chat/completions` |
| `--api_key API_KEY`                         | API key                                               | `<Your default key in `config.ini`>` |
| `--conversation_timeout_minutes CONVERSATION_TIMEOUT_MINUTES` | Conversation timeout in minutes  | `15`                        |
| `--db_file DB_FILE`                         | The chat history database file                        | `~/openai_chatgpt/chats.db` |
| `--clipboard_action`                        | Action that AI model must perform on the clipboard    | -                           |

### Description:

You can run the script with command-line arguments to override the default configuration values. If you don't pass any command-line arguments, the script will use the default configuration values specified in the `config.ini` file.

### Examples:

Run the script with the default configuration:

```sh
python openai_chatgpt.py
```

Run the script with custom configuration:

```bash
$ python openai_chatgpt.py --model gpt-3.5-turbo --temperature 0.5 --system_role "A helpful assistant" --address https://my-api-endpoint.com --api_key my-api-key --conversation_timeout_minutes 30 --db_file ~/openai_chatgpt/chats.db --clipboard_action "Explain like I am five"
```

This command prompts chatGPT to clarify whatever text you've copied onto your clipboard in a way that a 5-year-old can understand. ChatGPT here assumes the role of "a helpful assistant", leverage your prior 30 minutes of interaction with it to provide relevant context, and crafts its response with a randomness of 0.5 on a scale of 0 to 2.0.

## Usage as an Espanso package

### Clipboard Based Triggers

ChatGPT can be interacted with by copying your query to the clipboard and then typing a trigger phrase anywhere on your computer. The following clipboard based triggers are available:

Command | Description
--- | ---
`;clear-db` | Clear the chat history database.
`;ask` | Ask a question to ChatGPT.
`;debug` | Debug a code snippet.
`;respond` | Write a response.
`;code` | Write a code snippet with docs and examples.
`;snippet` | Return only the code without explanation (but include code docs).
`;previous-explain` | Explain the previous output in detail with examples.
`;explain` | Explain in detail a given topic or concept.
`;eli5` | Explain a given topic or concept like I'm 5 years old.
`;summarize` | Summarize a given text.
`;write` | Write an article on a given topic.
`;usage` | Generate usage documentation in markdown format.
`;grade` | Grade a given part of an essay on writing skills and suggest improvements.
`;rephrase` | Rephrase a given text.
`;correct` | Correct grammatical errors in a given text.
`;fact-check` | Check a given fact.
`;rhyme` | Make the given text rhyme.


### Regex Based Triggers
In addition to the clipboard based commands, there is one regex based command available:

Command | Description
--- | ---
`;q/{query}//` | Ask a query to ChatGPT.

To use this command, replace {query} with your query in the ;q/{query}// command.

## Installation instructions (as an Espanso package):

### Prerequisites
- Make sure you have Espanso installed on your system. If not, follow these [instructions](https://espanso.org/install/) to install it.

- Install `python3` if it's not already installed. If you'd like, create a new python environment - the installation script adds new python packages, namely `pyperclip` and `requests` to the current python environment.

- Create an account with [OpenAI](https://openai.com/) and generate an API key.

### Installation

1. Download the installation script by running the following command in your terminal:
    ```sh
    curl -o chatgpt.sh https://raw.githubusercontent.com/rohitna/chatgpt-script/main/install.sh
    ```

2. Run the installation script
    ```sh
    bash chatgpt.sh
    ```
    The installation script will install the necessary dependencies and create a config file.

3. Once the installation is complete, store your OpenAI API key in `~/openai_chatgpt/config.ini`.

4. That's it, happy chatting with ChatGPT!