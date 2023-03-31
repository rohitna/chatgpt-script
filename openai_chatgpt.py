#!/usr/bin/python

__version__ = "1.1" # talking to chatGPT enabled
__date__ = "2022-03-31"

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
import struct
import wave
import openai
from pvrecorder import PvRecorder
from typing import List, Tuple
from pprint import pprint

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - [%(levelname)s]: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

def get_clipboard_content() -> str:
    """
    Get the contents of the clipboard.

    Returns:
        str: The contents of the clipboard.
    """
    return pyperclip.paste()


def clear_clipboard():
    """
    A function to clear the contents of the clipboard.
    """

    # Get the current contents of the clipboard
    current_clipboard = pyperclip.paste()

    # Clear the clipboard by setting its contents to an empty string
    pyperclip.copy("")

    # Overwrite the contents of the clipboard with random data
    # This is done to prevent any data recovery
    pyperclip.copy(" ".join(["X" * 10] * 100))

    # Clear the clipboard again
    pyperclip.copy("")

def play_sound_effect(sound_effect: str):
    # Initialize Pygame
    pygame.mixer.init()

    # Load the sound effect WAV file
    pygame.mixer.music.load(sound_effect)

    # Play the sound effect
    pygame.mixer.music.set_volume(0.15)
    pygame.mixer.music.play()

    # Wait for the sound to finish playing
    while pygame.mixer.music.get_busy():
        pass

    pygame.mixer.quit()

def record_from_microphone(device_index: int, output_file: str, seconds: int, sound_effect: str):
    """
    Records audio from a specified device index for a specified duration of time and saves it to a WAV file.

    Args:
        device_index (int): Index of the input device to be used for recording.
        output_file (str): File name (including path) of the WAV file to save the recording to.
        seconds (int): Duration of the recording in seconds.
        sound_effect (str): Path to the sounds effect file.
    """
    recorder = PvRecorder(device_index=device_index, frame_length=512)
    start_time = time.time()

    # Start recording
    play_sound_effect(sound_effect)
    logger.info("Recording is starting now..")
    recorder.start()

    # Create a WAV file for the recording and set its parameters
    wav_file = wave.open(output_file, "w")
    wav_file.setparams((1, 2, 16000, 512, "NONE", "NONE"))

    # Record audio in a loop until the specified duration is reached or the user interrupts
    try:
        while True:
            # Read a chunk of audio data from the input stream
            pcm = recorder.read()

            # Write the audio data to the WAV file
            wav_file.writeframes(struct.pack("h" * len(pcm), *pcm))

            # break the loop if the max duration has elapsed
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time >= seconds:
                break
    except KeyboardInterrupt:
        logger.info("Early stopping prompted by the user.")
    finally:
        # Stop the recording and close the WAV file
        recorder.stop()
        recorder.delete()
        wav_file.close()
        play_sound_effect(sound_effect)

    logger.info(f"Recording saved to {output_file}")

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
    logger.info(f"Database file is {db_file}")
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

def transcribe(wav_file: str, api_key: str, transcription_model: str) -> str:
    """
    Transcribes an audio file using OpenAI's transcription API.

    Args:
    wav_file (str): The path to the input WAV file.
    api_key (str): OpenAI api key.
    transcription_model (str): OpenAI transcription model to use.

    Returns:
    str: The transcribed text from the audio file.
    """
    f = open(wav_file, "rb")
    openai.api_key = api_key
    transcript = openai.Audio.transcribe(transcription_model, f)
    parsed = json.loads(str(transcript))
    decoded_text = parsed['text'].encode().decode('unicode_escape')
    return decoded_text

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
    allow_clipboard: bool,
    transcription_model: str,
    record_duration: int,
    record: bool,
    recording_path: str,
    sound_effect: str,
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
        allow_clipboard (bool): Allow clipboard content to be sent to OpenAI.
        transcription_model (str): OpenAI model to use for transcriptions.
        record_duration (int): Recording duration for transcription.
        record (bool): Allow microphone recording and transcribing of actions to perform.
        recording_path (str): Path to the microphone recording .wav file.
        sound_effect (str): Path to the sound effect .wav file.
    """
    # Set up database
    set_up_database(db_file)

    if not allow_clipboard:
        clear_clipboard()

    # Get the new prompt from the clipboard
    clipboard_content = get_clipboard_content()

    # If record feature is on, record the action to perform.
    if record:
        record_from_microphone(
            -1,
            recording_path,
            record_duration,
            sound_effect,
        )
        clipboard_action = transcribe(
            recording_path,
            api_key,
            transcription_model,
        )
        logger.info(f"Transcribed action to perform: {clipboard_action}")
        # print(f"Transcribed action to perform: {clipboard_action}")


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
    messages = (
        [{"role": "system", "content": system_role}]
        + [
            {"role": role, "content": content}
            for role, content in zip(
                *get_conversations_after_timestamp(timestamp_cutoff, db_file)
            )
        ]
        + [{"role": "user", "content": new_prompt}]
    )
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
        "allow_clipboard": config.getboolean("default", "allow_clipboard"),
        "transcription_model": config.get("default", "transcription_model"),
        "record_duration": config.getint("default", "record_duration"),
        "record": config.getboolean("default", "record"),
        "recording_path": config.get("default", "recording_path"),
        "sound_effect": config.get("default", "sound_effect")
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
    parser.add_argument("--system-role", default=None, help="System role")
    parser.add_argument("--address", default=None, help="API address")
    parser.add_argument("--api-key", default=None, help="API key")
    parser.add_argument(
        "--conversation-timeout-minutes",
        type=int,
        default=None,
        help="Conversation timeout in minutes",
    )
    parser.add_argument(
        "--db-file",
        default=None,
        help="Path to the chat history database file",
    )
    parser.add_argument(
        "--clipboard-action",
        default="",
        help="What should the AI do with the clipboard content. Explain it?",
    )
    parser.add_argument(
        "--allow-clipboard",
        action="store_true",
        help="Allow clipboard content to be sent to openAI",
        default=True,
    )
    parser.add_argument(
        "--disallow-clipboard",
        dest="allow_clipboard",
        action="store_false",
        help="Disallow clipboard content to be sent to openAI",
    )
    parser.add_argument(
        "--transcription-model",
        default=None,
        help="OpenAI model to use for transcriptions",
    )
    parser.add_argument(
        "--record-duration", type=int, default=None, help="Recording duration for transcription"
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Allow microphone recording and transcribing of actions to perform",
        default=False,
    )
    parser.add_argument(
        "--no-recording",
        dest="record",
        action="store_false",
        help="Do not allow microphone recording",
    )
    parser.add_argument(
        "--recording-path",
        default=None,
        help="Path to the microphone recording .wav file",
    )
    parser.add_argument(
        "--sound-effect",
        default=None,
        help="Path to the sound effect .wav file",
    )
    return parser.parse_args()

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
    config["recording_path"] = expand_file_path(config["recording_path"])
    config["sound_effect"] = expand_file_path(config["sound_effect"])

    # logger.info(f"Config is: {config}")

    run_chatgpt(**config)


if __name__ == "__main__":
    main()
