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
| `--system-role SYSTEM_ROLE`                 | System role                                           | `A helpful assistant`           |
| `--address ADDRESS`                         | API address                                           | `https://api.openai.com/v1/chat/completions` |
| `--api-key API_KEY`                         | API key                                               | `<Your default key in config.ini>` |
| `--conversation-timeout-minutes CONVERSATION_TIMEOUT_MINUTES` | Conversation timeout in minutes  | `15`                        |
| `--db-file DB_FILE`                         | The chat history database file                        | `~/openai_chatgpt/chats.db` |
| `--clipboard-action CLIPBOARD_ACTION`       | Action that AI model must perform on the clipboard    | -                           |
| `--allow-clipboard`                         | Allow clipboard content to be sent to openAI          | `True (set)`                |
| `--disallow-clipboard`                      | Disallow clipboard content to be sent to OpenAI       | `False (not set)`           |
| `--transcription-model TRANSCRIPTION_MODEL` | OpenAI model to use for transcriptions                | `whisper-1`                 |
| `--record-duration RECORD_DURATION`         | Recording duration for transcription                  | `10 seconds`                |
| `--record`                                  | Allow microphone recording and transcribing of actions to perform | `False (not set)` |
| `--no-recording`                            | Do not allow microphone recording                      | `True (set)`                |
| `--recording-path RECORDING_PATH`           | Path to the microphone recording .wav file             | `~/openai_chatgpt/prompt.wav`           |
| `--sound-effect SOUND_EFFECT`               | Path to the sound effect .wav file                     | `~/openai_chatgpt/bell.wav`                           |

### Description:

You can run the script with command-line arguments to override the default configuration values. If you don't pass any command-line arguments, the script will use the default configuration values specified in the `config.ini` file.

### Examples:

1. Run the script with the default configuration:

    ```sh
    python openai_chatgpt.py
    ```

2. Run the script with custom configuration:

    ```bash
    $ python openai_chatgpt.py --model gpt-3.5-turbo --temperature 0.5 --system-role "A helpful assistant" --address https://my-api-endpoint.com --api-key my-api-key --conversation-timeout-minutes 30 --db-file ~/openai_chatgpt/chats.db --clipboard-action "Explain like I am five" --allow-clipboard
    ```

    This command prompts chatGPT to clarify whatever text you have copied onto your clipboard in a way that a 5-year-old can understand. ChatGPT here assumes the role of "a helpful assistant", leverage your prior 30 minutes of interaction with it to provide relevant context, and crafts its response with a randomness of 0.5 on a scale of 0 to 2.0.

3. Talk to chatGPT:

    ```bash
    $ python openai_chatgpt.py --record
    ```

    This command will record the action you would like to perform on the text you have copied onto your clipboard and prompt chatGPT for a response.


## Usage as an Espanso package
### Clipboard Based Triggers

ChatGPT can be interacted with by copying your query to the clipboard and then typing a trigger phrase anywhere on your computer. The following clipboard based triggers are available:

Command | Description
--- | ---
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
There is one regex based trigger:

Command | Description
--- | ---
`;q/{query}//` | Ask a query to ChatGPT.

To use this command, replace `{query}` with your query in the `;q/{query}//` command. It is to be noted that Espanso has a very rigorous character limit and hence, the query should not exceed 28 characters


### Form Based Triggers
There are a few form based trigger available:

Command | Description
--- | ---
`;form` | Ask a query to ChatGPT.
`;clip-form` | Tell ChatGPT the action you would like to perform on the clipboard.

To use these command, enter one of the triggers: `;form` or `;clip-form`. This will open up a form where you can enter your query and submit it.

### Microphone based triggers
In addition to the clipboard, regex, and based triggers, the following microphone based triggers are available. (These require that you grant microphone access to Espanso which could be tricky especially on a Mac; see FAQs below.):

Command | Description
--- | ---
`;talk` | Ask a query to ChatGPT.
`;clip-talk` | Tell ChatGPT the action you would like to perform on the clipboard.

To use these command, enter one of the triggers: `;talk` or `;clip-talk`. You will hear a bell, after which, you can record your query or clibboard action for the following ten seconds (before the second bell). The record duration is customizable.

### Other Useful Triggers

Command | Description
--- | ---
`;clear-db` | Clear the chat history database.
`;clear-clip` | Clear clipboard content.
`;test-setup` | Test setup.

## Protecting Sensitive Information on the Clipboard

It is important to be aware that the contents of your clipboard can be shared among apps, which can pose a serious security risk to your passwords, credit card numbers, or other confidential information.

When you copy sensitive data to your clipboard, it remains there until it is overwritten by new content. If you do not clear your clipboard after use, any app or program that accesses your clipboard can potentially access and share your sensitive information. In fact, the functionality provided by this repo serves as an example of how this is possible - the clipboard based triggers mentioned above send your clipboard contents to OpenAI.

To prevent this from happening, it is recommended that you always clear your clipboard after copying sensitive information. You can do this either by using the provided trigger `;clear-clip`, or by using a clipboard management tool that can automatically clear your clipboard.

Protect your information by taking proactive steps to secure your clipboard contents. Please be aware of the potential security risks associated with leaving sensitive data in your clipboard.

If you are unsure about how to ensure the safety of your clipboard content, after installation, please comment out all the clipboard based trigger specifications in the `package.yml` file:

```
cd "$(espanso path config)/match/packages/openai/"
```

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


## FAQs

1. How do I grant Espanso access to microphone on a Mac?

    This could be very tricky on newer versions of MacOS. Here are full instructions:
    - Check if the SIP (System Integrity Protection) is disabled by running `csrutil status`. If it is enabled then you will need to disable it; see FAQ #2 below.
    - Get the bundle identifier for Espanso using the following command:
    ```bash
    mdls -name kMDItemCFBundleIdentifier /Applications/Espanso.app
    ```
    You should see something like `com.federicoterzi.espanso`.
    - The TCC (Transparency, Consent, and Control) database is a security feature on macOS that stores information about which applications are authorized to access certain sensitive resources, such as the camera, microphone, location services, and more. Enter into the TCC database by using the following command:
    ```bash
    sudo sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db
    ```
    You will be prompted for you mac password. You can now see how authorizations you have given so far to your applications by running:
    ```bash
    select * from access;
    ```
    - Grant microphone access to Espanso by running the following in the TCC database:
    ```sqlite
    insert into access
    values
    ('kTCCServiceMicrophone','com.federicoterzi.espanso', 0, 2, 2, 1, null, null, null, 'UNUSED', null, 0, 1671466672);
    ```
    - Verify that the permission has been successfully granted.
      - Click on the Apple menu in the top left corner of your screen and select "System Preferences".
      - Click on the "Security & Privacy" icon.
      - Click on the "Privacy" tab.
      - In the left sidebar, select "Microphone".
      - Verify that Espanso is listed as an authorized app.
   -  Re-enable SIP; see FAQ #3.

2. How do I disable SIP (System Integrity Protection) on a Mac?

    - Shut down your Mac.
    - Restart your Mac in recovery mode. To do this, hold down the `Command + R` keys while your Mac starts up.
    - Once your Mac is in recovery mode, click on the Utilities menu in the top menu bar and select Terminal.
    - In the Terminal window, type the following command: `csrutil disable`.
    - Press `Enter` on your keyboard.
    - Restart your Mac normally.
    - After disabling SIP, you will have full access to system files and can make changes to them.

    However, it is important to note that disabling SIP can potentially make your Mac more vulnerable to malware and other security threats. Therefore, it is recommended that you re-enable SIP after you have completed your task that requires SIP to be disabled.

3. How do I re-enable SIP on a Mac?
 - Restart your Mac in Recovery mode by holding down the Command + R keys while your Mac is starting up.
 - When the macOS Utilities window appears, click on the "Utilities" menu and select "Terminal".
 - In the Terminal window, type the following command: csrutil enable.
 - Press enter and then restart your Mac normally.

    After your Mac restarts, SIP will be enabled again. Verify this by using `csrutil status`.