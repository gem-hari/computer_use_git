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

from loop_mac import (
    PROVIDER_TO_DEFAULT_MODEL_NAME,
    APIProvider,
    sampling_loop,
)
from tools import ToolResult
import json

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
        os.makedirs("screenshots", exist_ok=True)
        image_data = result.base64_image
        with open(f"screenshots/screenshot_{tool_use_id}.png", "wb") as f:
            f.write(base64.b64decode(image_data))
        print(f"Took screenshot screenshot_{tool_use_id}.png")

def api_response_callback(response: APIResponse[BetaMessage]):
    print(
        "\n---------------\nAPI Response:\n",
        json.dumps(json.loads(response.text)["content"], indent=4),  # type: ignore
        "\n",
    )
async def main():
    provider = APIProvider.BEDROCK
    if len(sys.argv) > 1:
        instruction = " ".join(sys.argv[1:])
    else:
        instruction = "Save an image of a cat to the desktop."

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
        messages=messages,
        api_key=None,
        output_callback=output_callback,
        tool_output_callback=tool_output_callback,
        api_response_callback=api_response_callback,
        only_n_most_recent_images=3,
        max_tokens=4096,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Encountered Error:\n{e}")










