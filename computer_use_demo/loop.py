import platform
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, cast
from anthropic import APIResponse
import httpx
from anthropic import (
    Anthropic,
    AnthropicBedrock,
    AnthropicVertex,
    APIError,
    APIResponseValidationError,
    APIStatusError,
)
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)

from tools import BashTool, ComputerTool, EditTool, ToolCollection, ToolResult
import os

from dotenv import load_dotenv
load_dotenv()

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

BETA_FLAG = "computer-use-2024-10-22"


class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"


PROVIDER_TO_DEFAULT_MODEL_NAME: dict[APIProvider, str] = {
    APIProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    APIProvider.BEDROCK: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    APIProvider.VERTEX: "claude-3-5-sonnet-v2@20241022",
}


# This system prompt is optimized for the Docker environment in this repository and
# specific tool combinations enabled.
# We encourage modifying this system prompt to ensure the model has context for the
# environment it is running in, and to provide any additional information that may be
# helpful for the task at hand.


SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
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




async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    SYSTEM_PROMPT:str,
    messages: list[BetaMessageParam],
    output_callback: Callable[[BetaContentBlockParam], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[[APIResponse[BetaMessage]], None],
    api_key: str,
    only_n_most_recent_images: int | None = None,
    max_tokens: int = 4096,
):
    """
    Agentic sampling loop for the assistant/tool interaction of computer use.
    """
    tool_collection = ToolCollection(
        ComputerTool(),
        BashTool(),
        EditTool(),
    )
    system = (
        f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}"
    )
    total_input_tokens=0
    total_output_tokens=0

    
    while True:
        if only_n_most_recent_images:
            _maybe_filter_to_n_most_recent_images(messages, only_n_most_recent_images)

        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key)
        elif provider == APIProvider.VERTEX:
            client = AnthropicVertex()
        elif provider == APIProvider.BEDROCK:
            client = AnthropicBedrock()

        # Call the API
        # we use raw_response to provide debug information to streamlit. Your
        # implementation may be able call the SDK directly with:
        # `response = client.messages.create(...)` instead.
        raw_response = client.beta.messages.with_raw_response.create(
            max_tokens=max_tokens,
            messages=messages,
            model=model,
            system=system,
            tools=tool_collection.to_params(),
            betas=["computer-use-2024-10-22"],
        )


        api_response_callback(cast(APIResponse[BetaMessage], raw_response))

        # print("---------r---------------")
        # print(raw_response)
        # print("----------r--------------")

        response = raw_response.parse()
       
        total_input_tokens=total_input_tokens+response.usage.input_tokens
        total_output_tokens=total_output_tokens+response.usage.output_tokens

        print("---------raw---------------")
        print(response.usage.input_tokens)
        print(response.usage.output_tokens)
        print(total_input_tokens)
        print(total_output_tokens)
        print("----------raw--------------")
       

        messages.append(
            {
                "role": "assistant",
                "content": cast(list[BetaContentBlockParam], response.content),
            }
        )

        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in cast(list[BetaContentBlockParam], response.content):
            output_callback(content_block)
            if content_block.type == "tool_use":
                result = await tool_collection.run(
                    name=content_block.name,
                    tool_input=cast(dict[str, Any], content_block.input),
                )
                tool_result_content.append(
                    _make_api_tool_result(result, content_block.id)
                )
                tool_output_callback(result, content_block.id)

        if not tool_result_content:
            return messages

        messages.append({"content": tool_result_content, "role": "user"})


def _maybe_filter_to_n_most_recent_images(
    messages: list[BetaMessageParam],
    images_to_keep: int,
    min_removal_threshold: int = 10,
):
    """
    With the assumption that images are screenshots that are of diminishing value as
    the conversation progresses, remove all but the final `images_to_keep` tool_result
    images in place, with a chunk of min_removal_threshold to reduce the amount we
    break the implicit prompt cache.
    """
    if images_to_keep is None:
        return messages

    tool_result_blocks = cast(
        list[BetaToolResultBlockParam],
        [
            item
            for message in messages
            for item in (
                message["content"] if isinstance(message["content"], list) else []
            )
            if isinstance(item, dict) and item.get("type") == "tool_result"
        ],
    )

    total_images = sum(
        1
        for tool_result in tool_result_blocks
        for content in tool_result.get("content", [])
        if isinstance(content, dict) and content.get("type") == "image"
    )

    images_to_remove = total_images - images_to_keep
    # for better cache behavior, we want to remove in chunks
    images_to_remove -= images_to_remove % min_removal_threshold

    for tool_result in tool_result_blocks:
        if isinstance(tool_result.get("content"), list):
            new_content = []
            for content in tool_result.get("content", []):
                if isinstance(content, dict) and content.get("type") == "image":
                    if images_to_remove > 0:
                        images_to_remove -= 1
                        continue
                new_content.append(content)
            tool_result["content"] = new_content


def _make_api_tool_result(
    result: ToolResult, tool_use_id: str
) -> BetaToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] | str = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        if result.output:
            tool_result_content.append(
                {
                    "type": "text",
                    "text": _maybe_prepend_system_tool_result(result, result.output),
                }
            )
        if result.base64_image:
            tool_result_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result.base64_image,
                    },
                }
            )
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text