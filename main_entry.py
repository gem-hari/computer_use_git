import asyncio
import base64
import os
import subprocess
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import StrEnum
from functools import partial
from pathlib import PosixPath
from typing import cast
import sys
import httpx
import streamlit as st
from anthropic import RateLimitError
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)
from streamlit.delta_generator import DeltaGenerator
from anthropic.types.beta import BetaMessage, BetaMessageParam
from anthropic import APIResponse

from loop import (
    PROVIDER_TO_DEFAULT_MODEL_NAME,
    APIProvider,
    sampling_loop,
)
from tools import ToolResult
import json
from flask import g
import platform
from datetime import datetime
import re

from dotenv import load_dotenv
import os

load_dotenv()

last_api_response = None


SYSTEM_PROMPT_COMPUTER_USE = f"""<SYSTEM_CAPABILITY>
* You are utilising an Ubuntu virtual machine using {platform.machine()} architecture with internet access.
* If the screen is locked, use password {os.getenv("SCREEN_PASSWRD")}.
* You can feel free to install Ubuntu applications with your bash tool. Use curl instead of wget.
* Open a new bash terminal to execute your bash commands.
* Using bash tool you can start GUI applications, but you need to set export DISPLAY=:{os.getenv("DISPLAY_NUM")} and use a subshell. For example "(DISPLAY=:10 xterm &)". GUI apps run with bash tool will appear within your desktop environment, but they may take some time to appear. Take a screenshot to confirm it did.
* Get the DISPLAY value by performing echo $DISPLAY, and use this value while starting the bash and firefox.
* To open firefox, please just execute (DISPLAY=:{os.getenv("DISPLAY_NUM")} firefox &).
* When using your bash tool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your computer function calls, they may take a while to run and send back to you. Where possible and feasible, try to chain multiple of these calls into one function call request.
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
</IMPORTANT>"""


SYSTEM_PROMPT_TESTING_POC = f"""<SYSTEM_CAPABILITY>
* You are operating a secure Ubuntu virtual machine using {platform.machine()} architecture with internet access.
* If the screen is locked, use password {os.getenv("SCREEN_PASSWRD")}.
* The environment is strictly limited to non-intrusive actions. 
* Tasks involving system modifications, including sudo commands, new software installations, or changes to existing configurations, are strictly prohibited.
* Allowed actions include web searches, file downloads, viewing and analyzing web pages, and any operations that do not alter the system's state or configuration.
* Open a new bash terminal to execute your bash commands.
* Using bash tool you can start GUI applications, but you need to set export DISPLAY=:{os.getenv("DISPLAY_NUM")} and use a subshell. For example "(DISPLAY=:10 xterm &)". GUI apps run with bash tool will appear within your desktop environment, but they may take some time to appear. Take a screenshot to confirm it did.
* Get the DISPLAY value by performing echo $DISPLAY, and use this value while starting the bash and firefox.
* To open firefox, please just execute (DISPLAY=:{os.getenv("DISPLAY_NUM")} firefox &).
* If any step requires installing software, running sudo commands, or making changes to the system, STOP the process immediately and return an API response explaining the required action and the prohibition.
* Always try to prioritize using web searches instead of curl.
* Use tools like `curl` for file downloading and `grep` for text extraction without installing additional software.
* If viewing files (e.g., PDFs) is necessary, download and read them without modifying the environment.
* You may open Firefox for browsing tasks, but any operations that require new installations or configurations must not be attempted. Use `(DISPLAY=:{os.getenv("DISPLAY_NUM")} firefox &)` to launch Firefox.
* GUI tools can be launched as described, but only existing tools are permitted.

<IMPORTANT>
* If a task requires installation or uninstallation of some applications, kindly return that task could not be performed because of the found limitations Eg: "Installation of the application cannot be performed ".
* If a task encounters limitations due to the restricted environment, report the exact requirement (e.g., a specific tool or dependency) that would enable the task, and mention that it cannot be installed or executed under the current restrictions as an API response.
* Always prioritize lightweight solutions and non-invasive methods for completing tasks.
* Do not attempt or suggest any prohibited actions.
</IMPORTANT>
"""

class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"

def output_callback(content_block):
    if isinstance(content_block, dict) and content_block.get("type") == "text":
        print("Assistant:", content_block.get("text"))

def tool_output_callback(result: ToolResult, tool_use_id: str):
    if result.output:
        print(f"> Tool Output [{tool_use_id}]:", result.output)
    if result.error:
        print(f"!!! Tool Error [{tool_use_id}]:", result.error)
    if result.base64_image:
        # Save the image to a file if needed
        save_dir = os.getenv("RESUTS_DIR")
        os.makedirs(save_dir, exist_ok=True)
        os.makedirs(save_dir+"screenshots", exist_ok=True)
        image_data = result.base64_image
        with open(f"{save_dir}screenshots/screenshot_{tool_use_id}.png", "wb") as f:
            f.write(base64.b64decode(image_data))
        print(f"Took screenshot screenshot_{tool_use_id}.png")

def api_response_callback(response: APIResponse[BetaMessage], g):
    g.last_api_response = json.loads(response.text)["content"]

    print(
        "\n---------------\nAPI Response:\n",
        json.dumps(g.last_api_response, indent=4),
        # "\n----token--------",
        # (response)["usage"],
        "\n",
    )
    

async def main(g):
    provider = APIProvider.BEDROCK
    print("Command-line arguments:", sys.argv)

    if len(sys.argv) > 1:
        instruction = str(sys.argv[1])
        print("Instruction received is ,",instruction)
    else:
        instruction = "Save an image of a cat to the desktop."

    if len(sys.argv) > 2:
        testing_poc_flag = (sys.argv[2]).lower()
    else:
        testing_poc_flag = "False"

    if testing_poc_flag == "true":
        SYSTEM_PROMPT = SYSTEM_PROMPT_TESTING_POC
    else:
        SYSTEM_PROMPT = SYSTEM_PROMPT_COMPUTER_USE
    print("Argument received for doing testing poc ", testing_poc_flag) 
    print(
        f"Starting Claude 'Computer Use'.\nPress ctrl+c to stop.\nInstructions provided: '{instruction}'"
    )
    messages: list[BetaMessageParam] = [
        {
            "role": "user",
            "content": instruction,
        }
    ]

    messages = await sampling_loop(
        model = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        provider=provider,
        system_prompt_suffix="",
        SYSTEM_PROMPT = SYSTEM_PROMPT,
        messages=messages,
        api_key=None,
        output_callback=output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=partial(api_response_callback, g=g),
        only_n_most_recent_images=3,
        max_tokens=4096,
    )

"""
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Encountered Error:\n{e}")"""


# print(1)


