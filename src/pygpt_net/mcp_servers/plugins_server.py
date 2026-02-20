#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2026.02.20 00:00:00                  #
# ================================================== #

"""PyGPT Plugins MCP server.

This module exposes a subset of PyGPT plugin capabilities as MCP tools so that
external MCP clients (including PyGPT's own MCP client plugin) can call them.

Supported tool groups (mirrors existing plugin IDs):
- audio_input: OpenAI audio transcription (file -> text)
- audio_output: OpenAI TTS (text -> audio file)
- cmd_mouse_control: desktop mouse/keyboard operations (PyAutoGUI)
- openai_dalle: OpenAI image generation
- openai_vision: OpenAI vision chat on a single image
- real_time: current date/time
- telegram: Telegram Bot API (send/get updates)
- voice_control: list/recognize voice actions (OpenAI classifier)

Security note:
Many tools here can be destructive (mouse/keyboard control, sending messages).
Run this server only in trusted environments.
"""

import argparse
import base64
import datetime as _dt
import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


# ---------------------------
# Errors / optional imports
# ---------------------------


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


class DependencyError(RuntimeError):
    """Raised when an optional runtime dependency is missing."""


def _require_env(name: str, help_text: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise ConfigError(f"Missing env var {name}. {help_text}")
    return value


def _optional_import(module: str, install_hint: str):
    try:
        return __import__(module, fromlist=["*"])
    except Exception as e:
        raise DependencyError(f"Missing dependency '{module}'. {install_hint} (error: {e})")


def _now_local() -> _dt.datetime:
    # The app/plugin uses local time (datetime.now()), so keep parity.
    return _dt.datetime.now()


# ---------------------------
# OpenAI helpers
# ---------------------------


def _openai_client():
    """Create an OpenAI client.

    Reads:
    - OPENAI_API_KEY (required)
    - OPENAI_BASE_URL (optional)

    Note: `openai` SDK also reads env vars, but we validate OPENAI_API_KEY to
    provide actionable errors.
    """

    _optional_import("openai", "Install with: pip install openai")
    from openai import OpenAI  # type: ignore

    api_key = _require_env("OPENAI_API_KEY", "Set your OpenAI API key.")
    base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None

    # OpenAI() accepts base_url in modern SDKs.
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _encode_image_to_data_url(path: Union[str, Path]) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {p}")

    suffix = p.suffix.lower().lstrip(".")
    mime = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }.get(suffix, "application/octet-stream")

    data = base64.b64encode(p.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"


# ---------------------------
# Telegram helpers (Bot API)
# ---------------------------


def _telegram_token() -> str:
    return _require_env(
        "TELEGRAM_BOT_TOKEN",
        "Create a Telegram bot via @BotFather and set TELEGRAM_BOT_TOKEN.",
    )


def _telegram_api_url(method: str) -> str:
    token = _telegram_token()
    return f"https://api.telegram.org/bot{token}/{method}"


def _telegram_request(method: str, *, data: Optional[dict] = None, files: Optional[dict] = None) -> Dict[str, Any]:
    requests = _optional_import("requests", "Install with: pip install requests")

    url = _telegram_api_url(method)
    res = requests.post(url, data=data, files=files, timeout=60)
    try:
        payload = res.json()
    except Exception:
        payload = {"ok": False, "error": f"Non-JSON response: HTTP {res.status_code}", "text": res.text}

    if not payload.get("ok", False):
        desc = payload.get("description") or payload.get("error") or "Unknown Telegram error"
        raise RuntimeError(f"Telegram API error ({method}): {desc}")

    return payload


# ---------------------------
# Voice control (standalone)
# ---------------------------


VOICE_ACTIONS: Dict[str, str] = {
    # A pragmatic subset of `pygpt_net.core.access.voice.Voice.commands`.
    # Keeping it smaller makes prompts/tool outputs more manageable.
    "app_status": "Get the current application status (if integrated)",
    "app_exit": "Exit the application (if integrated)",
    "audio_output_enable": "Enable audio output",
    "audio_output_disable": "Disable audio output",
    "audio_input_enable": "Enable audio input",
    "audio_input_disable": "Disable audio input",
    "ctx_new": "Create a new context",
    "ctx_prev": "Go to the previous context",
    "ctx_next": "Go to the next context",
    "ctx_last": "Go to the latest context",
    "ctx_input_send": "Send the input",
    "ctx_input_clear": "Clear the input",
    "mode_chat": "Switch to Chat mode",
    "mode_llama_index": "Switch to Chat with Files (LlamaIndex) mode",
    "mode_next": "Switch to the next mode",
    "mode_prev": "Switch to the previous mode",
    "model_next": "Switch to the next model",
    "model_prev": "Switch to the previous model",
    "voice_message_start": "Start listening for voice input",
    "voice_message_stop": "Stop listening for voice input",
    "voice_message_toggle": "Toggle listening for voice input",
}


def _voice_control_prompt(text: str) -> str:
    cmds = "\n".join([f"- {k}: {v}" for k, v in VOICE_ACTIONS.items()])
    return (
        "Recognize the user's voice action and choose exactly one action id from the list.\n"
        "Return ONLY valid JSON in this schema: {\"action\": \"action_id\", \"args\": \"optional args\"}.\n"
        "If no action matches, return {\"action\": \"unknown\", \"args\": \"\"}.\n\n"
        f"Available actions:\n{cmds}\n\n"
        f"User input:\n{text}\n"
    )


def _extract_first_json_object(text: str) -> Optional[dict]:
    # Best-effort extraction (model should return JSON-only, but keep robust).
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return None


# ---------------------------
# MCP server
# ---------------------------


@dataclass(frozen=True)
class ServerArgs:
    transport: str
    host: str
    port: int
    mount_path: str


def create_server(*, host: str = "127.0.0.1", port: int = 8000, mount_path: str = "/"):
    """Create the FastMCP server and register all tools."""

    mcp = _optional_import(
        "mcp.server.fastmcp",
        "Install with: pip install \"mcp[cli]\"",
    )
    types = _optional_import(
        "mcp.types",
        "Install with: pip install \"mcp[cli]\"",
    )

    from mcp.server.fastmcp import FastMCP  # type: ignore

    server = FastMCP(
        name="pygpt-plugins",
        instructions=(
            "PyGPT plugins MCP server. Tools are prefixed by plugin id. "
            "Some tools are destructive (mouse/keyboard, Telegram sends)."
        ),
        host=host,
        port=port,
        mount_path=mount_path,
        stateless_http=True,
    )

    # ---------------------------
    # real_time
    # ---------------------------

    @server.tool(
        name="real_time_get_time",
        description="Return current local date/time formatted with strftime.",
        annotations=types.ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def real_time_get_time(fmt: str = "%A, %Y-%m-%d %H:%M:%S") -> Dict[str, Any]:
        now = _now_local().strftime(fmt)
        return {"time": now, "format": fmt}

    # ---------------------------
    # audio_input
    # ---------------------------

    @server.tool(
        name="audio_input_transcribe_file",
        description="Transcribe an audio file to text using OpenAI audio transcription.",
        annotations=types.ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
        structured_output=True,
    )
    def audio_input_transcribe_file(
        path: str,
        model: str = "whisper-1",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = _openai_client()
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Audio file not found: {p}")

        with p.open("rb") as f:
            kwargs: Dict[str, Any] = {"model": model, "file": f}
            if language:
                kwargs["language"] = language
            if prompt:
                kwargs["prompt"] = prompt
            resp = client.audio.transcriptions.create(**kwargs)

        text = getattr(resp, "text", None) or (resp.get("text") if isinstance(resp, dict) else None)
        return {"text": text or "", "model": model}

    # ---------------------------
    # audio_output
    # ---------------------------

    @server.tool(
        name="audio_output_speech_to_file",
        description="Convert text to speech using OpenAI TTS and save it to a local audio file.",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=True,
        ),
        structured_output=True,
    )
    def audio_output_speech_to_file(
        text: str,
        model: str = "tts-1",
        voice: str = "alloy",
        audio_format: str = "mp3",
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = _openai_client()
        if not text or not text.strip():
            raise ValueError("'text' must be non-empty")

        if output_path:
            out = Path(output_path)
        else:
            out = Path(tempfile.gettempdir()) / f"pygpt_tts_{int(time.time())}.{audio_format}"

        out.parent.mkdir(parents=True, exist_ok=True)

        # openai SDK returns a response object with `.write_to_file`.
        resp = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            format=audio_format,
        )

        if hasattr(resp, "write_to_file"):
            resp.write_to_file(str(out))
        else:
            # Fallback: some versions return bytes-like content.
            data = getattr(resp, "content", None)
            if data is None and isinstance(resp, dict):
                data = resp.get("content")
            if data is None:
                raise RuntimeError("Unexpected OpenAI TTS response type (missing write_to_file/content).")
            out.write_bytes(data)

        return {"path": str(out), "model": model, "voice": voice, "format": audio_format}

    # ---------------------------
    # cmd_mouse_control (PyAutoGUI)
    # ---------------------------

    def _pyautogui():
        return _optional_import("pyautogui", "Install with: pip install PyAutoGUI")

    @server.tool(
        name="cmd_mouse_control_get_mouse_position",
        description="Get the current mouse cursor position.",
        annotations=types.ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def cmd_mouse_control_get_mouse_position() -> Dict[str, Any]:
        pag = _pyautogui()
        x, y = pag.position()
        return {"x": int(x), "y": int(y)}

    @server.tool(
        name="cmd_mouse_control_mouse_move",
        description="Move the mouse to an absolute screen position.",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def cmd_mouse_control_mouse_move(x: int, y: int, duration: float = 0.0) -> Dict[str, Any]:
        pag = _pyautogui()
        pag.moveTo(int(x), int(y), duration=float(duration))
        return {"ok": True, "x": int(x), "y": int(y), "duration": float(duration)}

    @server.tool(
        name="cmd_mouse_control_mouse_click",
        description="Click the mouse (optionally at x,y).",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def cmd_mouse_control_mouse_click(
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        clicks: int = 1,
        interval: float = 0.0,
    ) -> Dict[str, Any]:
        pag = _pyautogui()
        pag.click(x=x, y=y, button=button, clicks=int(clicks), interval=float(interval))
        return {"ok": True}

    @server.tool(
        name="cmd_mouse_control_mouse_scroll",
        description="Scroll the mouse wheel by the given amount (positive=up, negative=down).",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def cmd_mouse_control_mouse_scroll(clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        pag = _pyautogui()
        pag.scroll(int(clicks), x=x, y=y)
        return {"ok": True}

    @server.tool(
        name="cmd_mouse_control_mouse_drag",
        description="Drag the mouse to x,y.",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def cmd_mouse_control_mouse_drag(
        x: int,
        y: int,
        duration: float = 0.0,
        button: str = "left",
    ) -> Dict[str, Any]:
        pag = _pyautogui()
        pag.dragTo(int(x), int(y), duration=float(duration), button=button)
        return {"ok": True}

    @server.tool(
        name="cmd_mouse_control_keyboard_key",
        description="Press a single keyboard key.",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def cmd_mouse_control_keyboard_key(key: str) -> Dict[str, Any]:
        pag = _pyautogui()
        pag.press(str(key))
        return {"ok": True}

    @server.tool(
        name="cmd_mouse_control_keyboard_keys",
        description="Press a hotkey combination (e.g. ['ctrl','c']).",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def cmd_mouse_control_keyboard_keys(keys: List[str]) -> Dict[str, Any]:
        pag = _pyautogui()
        if not keys:
            raise ValueError("'keys' must be non-empty")
        pag.hotkey(*[str(k) for k in keys])
        return {"ok": True}

    @server.tool(
        name="cmd_mouse_control_keyboard_type",
        description="Type the given text.",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def cmd_mouse_control_keyboard_type(text: str, interval: float = 0.0) -> Dict[str, Any]:
        pag = _pyautogui()
        pag.typewrite(str(text), interval=float(interval))
        return {"ok": True}

    @server.tool(
        name="cmd_mouse_control_get_screenshot",
        description="Take a screenshot and save it to a file.",
        annotations=types.ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def cmd_mouse_control_get_screenshot(
        output_path: Optional[str] = None,
        region: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        pag = _pyautogui()
        if output_path:
            out = Path(output_path)
        else:
            out = Path(tempfile.gettempdir()) / f"pygpt_screenshot_{int(time.time())}.png"
        out.parent.mkdir(parents=True, exist_ok=True)

        r: Optional[Tuple[int, int, int, int]] = None
        if region:
            if len(region) != 4:
                raise ValueError("'region' must have 4 integers: [x, y, width, height]")
            r = (int(region[0]), int(region[1]), int(region[2]), int(region[3]))

        img = pag.screenshot(region=r)
        img.save(str(out))
        w, h = img.size
        return {"path": str(out), "width": int(w), "height": int(h), "region": r}

    @server.tool(
        name="cmd_mouse_control_wait",
        description="Wait/sleep for the given number of seconds.",
        annotations=types.ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def cmd_mouse_control_wait(seconds: float) -> Dict[str, Any]:
        time.sleep(float(seconds))
        return {"ok": True, "seconds": float(seconds)}

    # ---------------------------
    # openai_dalle
    # ---------------------------

    @server.tool(
        name="openai_dalle_generate_image",
        description="Generate image(s) from a text prompt using OpenAI images API.",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=True,
        ),
        structured_output=True,
    )
    def openai_dalle_generate_image(
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: Optional[str] = None,
        n: int = 1,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = _openai_client()
        if not prompt or not prompt.strip():
            raise ValueError("'prompt' must be non-empty")

        out_dir = Path(output_dir) if output_dir else (Path(tempfile.gettempdir()) / "pygpt_images")
        out_dir.mkdir(parents=True, exist_ok=True)

        kwargs: Dict[str, Any] = {"model": model, "prompt": prompt, "n": int(n), "size": size}
        if quality:
            kwargs["quality"] = quality

        resp = client.images.generate(**kwargs)

        # The SDK response is typically an object with `.data`.
        data_list = getattr(resp, "data", None) or (resp.get("data") if isinstance(resp, dict) else None) or []
        revised_prompt = getattr(resp, "revised_prompt", None)

        paths: List[str] = []
        for i, item in enumerate(data_list):
            url = getattr(item, "url", None) or (item.get("url") if isinstance(item, dict) else None)
            b64_json = getattr(item, "b64_json", None) or (item.get("b64_json") if isinstance(item, dict) else None)

            filename = f"openai_image_{int(time.time())}_{i + 1}.png"
            out = out_dir / filename

            if url:
                requests = _optional_import("requests", "Install with: pip install requests")
                r = requests.get(url, timeout=60)
                r.raise_for_status()
                out.write_bytes(r.content)
            elif b64_json:
                out.write_bytes(base64.b64decode(b64_json))
            else:
                raise RuntimeError("OpenAI images response item missing url/b64_json")

            paths.append(str(out))

        return {"paths": paths, "model": model, "size": size, "quality": quality, "revised_prompt": revised_prompt}

    # ---------------------------
    # openai_vision
    # ---------------------------

    @server.tool(
        name="openai_vision_analyze_image",
        description="Analyze an image (local path or URL) with an OpenAI vision-capable chat model.",
        annotations=types.ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        ),
        structured_output=True,
    )
    def openai_vision_analyze_image(
        prompt: str,
        model: str = "gpt-4o-mini",
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        max_tokens: int = 512,
    ) -> Dict[str, Any]:
        if not image_path and not image_url:
            raise ValueError("Provide either 'image_path' or 'image_url'")
        if image_path and image_url:
            raise ValueError("Provide only one of 'image_path' or 'image_url'")

        client = _openai_client()

        if image_path:
            url = _encode_image_to_data_url(image_path)
        else:
            url = str(image_url)

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": url}},
                ],
            }
        ]

        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=int(max_tokens),
        )

        # Extract text
        choices = getattr(resp, "choices", None) or (resp.get("choices") if isinstance(resp, dict) else [])
        text_out = ""
        if choices:
            msg = getattr(choices[0], "message", None) or (choices[0].get("message") if isinstance(choices[0], dict) else None)
            if msg is not None:
                text_out = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")

        return {"text": text_out, "model": model}

    # ---------------------------
    # telegram
    # ---------------------------

    @server.tool(
        name="telegram_get_me",
        description="Get the Telegram bot information (Bot API getMe).",
        annotations=types.ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
        structured_output=True,
    )
    def telegram_get_me() -> Dict[str, Any]:
        return _telegram_request("getMe")

    @server.tool(
        name="telegram_send_message",
        description="Send a Telegram message (Bot API sendMessage).",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=True,
        ),
        structured_output=True,
    )
    def telegram_send_message(chat_id: str, text: str, parse_mode: Optional[str] = None) -> Dict[str, Any]:
        data: Dict[str, Any] = {"chat_id": chat_id, "text": text}
        if parse_mode:
            data["parse_mode"] = parse_mode
        return _telegram_request("sendMessage", data=data)

    @server.tool(
        name="telegram_send_photo",
        description="Send a photo to a Telegram chat (Bot API sendPhoto).",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=True,
        ),
        structured_output=True,
    )
    def telegram_send_photo(chat_id: str, photo_path: str, caption: Optional[str] = None) -> Dict[str, Any]:
        p = Path(photo_path)
        if not p.exists():
            raise FileNotFoundError(f"Photo not found: {p}")
        data: Dict[str, Any] = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        with p.open("rb") as f:
            return _telegram_request("sendPhoto", data=data, files={"photo": f})

    @server.tool(
        name="telegram_send_document",
        description="Send a document to a Telegram chat (Bot API sendDocument).",
        annotations=types.ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=True,
        ),
        structured_output=True,
    )
    def telegram_send_document(chat_id: str, document_path: str, caption: Optional[str] = None) -> Dict[str, Any]:
        p = Path(document_path)
        if not p.exists():
            raise FileNotFoundError(f"Document not found: {p}")
        data: Dict[str, Any] = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        with p.open("rb") as f:
            return _telegram_request("sendDocument", data=data, files={"document": f})

    @server.tool(
        name="telegram_get_updates",
        description="Fetch updates for the bot (Bot API getUpdates).",
        annotations=types.ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        ),
        structured_output=True,
    )
    def telegram_get_updates(offset: Optional[int] = None, limit: int = 100, timeout: int = 0) -> Dict[str, Any]:
        data: Dict[str, Any] = {"limit": int(limit), "timeout": int(timeout)}
        if offset is not None:
            data["offset"] = int(offset)
        return _telegram_request("getUpdates", data=data)

    # ---------------------------
    # voice_control
    # ---------------------------

    @server.tool(
        name="voice_control_list_actions",
        description="List available voice actions and their descriptions.",
        annotations=types.ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        structured_output=True,
    )
    def voice_control_list_actions() -> Dict[str, Any]:
        return {"actions": VOICE_ACTIONS}

    @server.tool(
        name="voice_control_recognize",
        description="Recognize the best matching voice action for input text using OpenAI.",
        annotations=types.ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        ),
        structured_output=True,
    )
    def voice_control_recognize(text: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        client = _openai_client()
        prompt = _voice_control_prompt(text)

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a strict JSON generator."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        choices = getattr(resp, "choices", None) or (resp.get("choices") if isinstance(resp, dict) else [])
        content = ""
        if choices:
            msg = getattr(choices[0], "message", None) or (choices[0].get("message") if isinstance(choices[0], dict) else None)
            if msg is not None:
                content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")

        data = _extract_first_json_object(content) or {"action": "unknown", "args": ""}
        action = data.get("action")
        args = data.get("args", "")
        if action not in VOICE_ACTIONS and action != "unknown":
            action = "unknown"
            args = ""

        return {"action": action, "args": args, "model": model}

    return server


def _parse_args(argv: Optional[List[str]] = None) -> ServerArgs:
    parser = argparse.ArgumentParser(description="PyGPT Plugins MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport to use.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host for HTTP/SSE.")
    parser.add_argument("--port", type=int, default=8000, help="Bind port for HTTP/SSE.")
    parser.add_argument("--mount-path", default="/", help="Mount path for HTTP/SSE servers.")

    args = parser.parse_args(argv)
    return ServerArgs(
        transport=str(args.transport),
        host=str(args.host),
        port=int(args.port),
        mount_path=str(args.mount_path),
    )


def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)
    server = create_server(host=args.host, port=args.port, mount_path=args.mount_path)

    # FastMCP.run is synchronous.
    server.run(transport=args.transport, mount_path=args.mount_path)


if __name__ == "__main__":
    main()
