__version__ = "1.0"
__date__ = "2022-03-06"

"""
Usage:
  openai_chatgpt.py [options]

Options:
  -h, --help                                   Show this help message and exit
  --model MODEL                                Model name [default: gpt-3.5-turbo]
  --temperature TEMPERATURE                    Temperature value [default: 1.0]
  --system_role SYSTEM_ROLE                    System role [default: A wise chat bot]
  --address ADDRESS                            API address [default: https://api.openai.com/v1/chat/completions]
  --api_key API_KEY                            API key [default: <Your default key in `config.ini`>]
  --conversation_timeout_minutes CONVERSATION_TIMEOUT_MINUTES
                                               Conversation timeout in minutes [default: 15]
  --db_file DB_FILE                            The chat history database file [default: ~/openai_chatgpt/chats.db]
  --clipboard_action                           Action that AI model must perform on the clipboard

Description:
  This script returns the chatGPT chat completion using the prompt from the clipboard and previous prompts from the database as context. The chatbot uses the OpenAI API to generate text responses to user messages.

  You can run the script with command-line arguments to override the default configuration values. The available command-line arguments are:

  --model: The name of the GPT model to use.
  --temperature: The temperature value to use.
  --system_role: The role of the system in the conversation.
  --address: The URL of the API endpoint.
  --api_key: The API key to use.
  --conversation_timeout_minutes: The conversation timeout in minutes.
  --db_file: The chat history database file path.
  --clipboard_action: What should the AI do with the clipboard content. Explain it?

  If you don't pass any command-line arguments, the script will use the default configuration values specified in the config.ini file. The config file `config.ini` should be stored at '~/openai_chatgpt/config.ini'

Examples:
  Run the script with the default configuration:
  $ python script.py

  Run the script with custom configuration:
  $ python openai_chatgpt.py --model gpt-3.5-turbo --temperature 0.5 --system_role "Funny poet" --address https://my-api-endpoint.com --api_key my-api-key --conversation_timeout_minutes 30 --db_file ~/openai_chatgpt/chats.db --clipboard_action "Explain like I am five"
"""

#!/usr/bin/python

import json
import sys
import os
import base64
import pyperclip
import sqlite3
import requests
import time
import datetime
import configparser
import argparse
import logging
from typing import List, Tuple
from pprint import pprint

logger = logging.getLogger("openai_chatgpt.py")


def get_clipboard_content() -> str:
    """
    Get the contents of the clipboard.

    Returns:
        str: The contents of the clipboard.
    """
    return pyperclip.paste()


def encode_base64(string: str) -> str:
    """
    Encode a string as base64.

    Args:
        string (str): The string to encode.

    Returns:
        str: The base64-encoded string.
    """
    string_bytes = string.encode("utf-8")
    encoded_bytes = base64.b64encode(string_bytes)
    encoded_string = encoded_bytes.decode("utf-8")
    return encoded_string


def decode_base64(encoded_string: str) -> str:
    """
    Decode a base64-encoded string.

    Args:
        encoded_string (str): The base64-encoded string to decode.

    Returns:
        str: The decoded string.
    """
    encoded_bytes = encoded_string.encode("utf-8")
    decoded_bytes = base64.b64decode(encoded_bytes)
    decoded_string = decoded_bytes.decode("utf-8")
    return decoded_string


def timestamp_n_minutes_ago(n: int) -> int:
    """
    Get the timestamp from n minutes ago.

    Args:
        n (int): The number of minutes ago.

    Returns:
        int: The timestamp from n minutes ago.
    """
    now = datetime.datetime.utcnow()
    delta = datetime.timedelta(minutes=n)
    past_time = now - delta
    return int(time.mktime(past_time.timetuple()))


def set_up_database(db_file: str) -> None:
    """
    - Set up the SQLite database called chats.db.
    - Make sure that it has the conversations table.

    Args:
        db_file (str): The chat histor database file.
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS conversations
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         timestamp INT,
                         role TEXT,
                         content TEXT)"""
    )
    conn.commit()
    cursor.close()
    conn.close()


def insert_conversation(role: str, content: str, db_file: str) -> None:
    """
    Insert a conversation into the database.
    Note: Entries are encoded in base64 before insertion.

    Args:
        role (str): The role of the speaker.
        content (str): The content of the message.
        db_file (str): The chat database file path
    """
    role = encode_base64(role)
    content = encode_base64(content)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    now = datetime.datetime.utcnow()
    timestamp = int(time.mktime(now.timetuple()))
    cursor.execute(
        "INSERT INTO conversations (timestamp, role, content) VALUES (?, ?, ?)",
        (timestamp, role, content),
    )
    conn.commit()
    conn.close()


def send_request(json_data: str, address: str, api_key: str) -> dict:
    """
    Send a request to the openAI API endpoint.

    Args:
        json_data (str): The JSON data to send.
        address (str): The address of the API endpoint.
        api_key (str): The API key to use for authorization.

    Returns:
        dict: The response from the API as a dict.
    """
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}

    try:
        response = requests.post(address, data=json_data, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        raise
    except requests.exceptions.RequestException as err:
        logging.error(f"An error occurred while sending the request: {err}")
        raise

    # Log the response text
    logger.info(f"Response received from the AI model: {response.text}")

    # Return the response
    return json.loads(response.text, strict=False)


def get_conversations_after_timestamp(
    timestamp: int, db_file: str
) -> Tuple[List[str], List[str]]:
    """
    Get recent conversations from the chat database that have occurred after the specified timestamp.

    Args:
        timestamp (int): The cutoff timestamp.
        db_file (str): The chat database file path.

    Returns:
        roles (List[str]): A list of roles for each conversation.
        contents (List[str]): A list of conversation contents.
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM conversations WHERE timestamp >= ?", (timestamp,)
    )
    rows = cursor.fetchall()
    conn.close()
    # Convert the list of tuples to two separate lists and decode
    roles = [decode_base64(row[0]) for row in rows]
    contents = [decode_base64(row[1]) for row in rows]
    return roles, contents


def run_chatgpt(
    model: str,
    temperature: float,
    system_role: str,
    address: str,
    api_key: str,
    conversation_timeout_minutes: int,
    db_file: str,
    clipboard_action: str,
):
    """
    - Prints the response from chatGPT to the clipboard prompt.
    - Inserts the new conversation into the database.

    Args:
        model (str): Name of the AI model.
        temperature (float): Temperature to use for the model.
        system_role (str): Role assumed by the AI assistant.
        address (str): POST url.
        api_key (str): openAI api key.
        conversation_timeout_minutes (int): Time cutoff to decide how many previous conversations to send to the AI model for context.
        db_file (str): Chat history database file.
        clipboard_action (str): Action to perform on the clipboard.
    """
    # Set up database
    set_up_database(db_file)

    # Get the new prompt from the clipboard
    clipboard_content = get_clipboard_content()

    # Modify the prompt according to the desired clipboard action
    if not clipboard_content and not clipboard_action:
        raise ValueError("The new prompt is empty")
    elif not clipboard_content:
        new_prompt = clipboard_action
    elif not clipboard_action:
        new_prompt = clipboard_content
    else:
        new_prompt = f"{clipboard_action}: {clipboard_content}"

    logger.info(f"Full prompt is: {new_prompt}")

    # Create json request
    timestamp_cutoff = timestamp_n_minutes_ago(conversation_timeout_minutes)
    messages = [{"role": "system", "content": system_role}] + \
           [{"role": role, "content": content} for role, content in zip(*get_conversations_after_timestamp(timestamp_cutoff, db_file))] + \
           [{"role": "user", "content": new_prompt}]
    logger.info(f"Messages to be sent to the AI model: {messages}")

    data = {"model": model, "temperature": temperature, "messages": messages}
    json_data = json.dumps(data)

    # Get the reply from the AI model
    response = send_request(json_data, address, api_key)
    reply = response["choices"][0]["message"]["content"]

    # Print the reply from the AI bot
    print(reply)

    # Insert the current conversation into the database
    insert_conversation("user", new_prompt, db_file)
    insert_conversation("assistant", reply, db_file)


def read_config(config_file):
    """
    Reads configuration from a config file.

    Args:
        config_file (str): The path to the config file.

    Returns:
        dict: A dictionary containing configuration values.
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    return {
        "model": config.get("default", "model"),
        "temperature": config.getfloat("default", "temperature"),
        "system_role": config.get("default", "system_role"),
        "address": config.get("default", "address"),
        "api_key": config.get("default", "api_key"),
        "conversation_timeout_minutes": config.getint(
            "default", "conversation_timeout_minutes"
        ),
        "db_file": config.get("default", "db_file"),
    }


def parse_args():
    """
    Parses command-line arguments.
    Default arguments can be specified in `config.ini`

    Returns:
        argparse.Namespace: An object containing the values of the command-line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="Model name")
    parser.add_argument(
        "--temperature", type=float, default=None, help="Temperature value"
    )
    parser.add_argument("--system_role", default=None, help="System role")
    parser.add_argument("--address", default=None, help="API address")
    parser.add_argument("--api_key", default=None, help="API key")
    parser.add_argument(
        "--conversation_timeout_minutes",
        type=int,
        default=None,
        help="Conversation timeout in minutes",
    )
    parser.add_argument(
        "--db_file",
        default=None,
        help="Path to the chat history database file",
    )
    parser.add_argument(
        "--clipboard_action",
        default="",
        help="What should the AI do with the clipboard content. Explain it?",
    )
    return parser.parse_args()


def configure_logging():
    """
    Configures the logging system.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()],
    )

def expand_file_path(file_path: str) -> str:
    """
    Expands a file path to an absolute path, handling the tilde character (~) and environment variables in the path.

    Args:
        file_path (str): The file path to expand.

    Returns:
        str: The expanded file path as an absolute path.
    """
    if not file_path:
        raise ValueError("File path cannot be empty or None")

    file_path = os.path.expanduser(file_path)
    file_path = os.path.expandvars(file_path)
    file_path = os.path.abspath(file_path)

    return file_path


def main():
    """
    The main function that runs the script.
    """
    try:
        config_file = expand_file_path("~/openai_chatgpt/config.ini")
        config = read_config(config_file)
    except Exception as e:
        logger.info("Error reading config file: {}".format(e))
        sys.exit(1)

    args = parse_args()

    # Override config values with command-line arguments
    for key, value in vars(args).items():
        if value is not None:
            config[key] = value

    config["db_file"] = expand_file_path(config["db_file"])

    configure_logging()

    run_chatgpt(**config)


if __name__ == "__main__":
    main()
