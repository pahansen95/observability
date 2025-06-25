"""Minimal chat client for Large Language Models.

Improved version incorporating best practices from NatLang while maintaining simplicity.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Any

from helpers.utils import HttpSession, logger
from helpers.tools import tool, SubParser


# === Core Data Models ===

class Role(str, Enum):
    """Conversation participant roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class TextPart:
    """Text content of a message."""
    text: str

    def to_dict(self) -> dict:
        return {"type": "text", "text": self.text}


@dataclass
class ImagePart:
    """Image content referenced by URL."""
    url: str
    detail: str | None = None

    def to_dict(self) -> dict:
        data = {"type": "image_url", "image_url": {"url": self.url}}
        if self.detail:
            data["image_url"]["detail"] = self.detail
        return data


Part = TextPart | ImagePart


@dataclass
class ChatMessage:
    """Single message in a chat conversation."""
    role: Role
    content: List[Part]

    def __post_init__(self):
        # Validate at construction
        assert self.role in Role.__members__.values(), f"Invalid role: {self.role}"
        assert self.content, "Message content cannot be empty"
        assert all(isinstance(p, (TextPart, ImagePart)) for p in self.content), \
            "Invalid content type"

    def to_dict(self) -> dict:
        if len(self.content) == 1 and isinstance(self.content[0], TextPart):
            return {"role": self.role.value, "content": self.content[0].text}
        return {"role": self.role.value, "content": [p.to_dict() for p in self.content]}


@dataclass
class ChatResponse:
    """Rich response with metadata."""
    content: str
    model: str | None = None
    created_at: float = field(default_factory=time.time)
    usage: dict[str, Any] | None = None
    raw_response: dict | None = None


# === Error Hierarchy ===

class ChatError(Exception):
    """Base chat error with context."""
    def __init__(self, message: str, **context):
        super().__init__(message)
        self.context = context


class ConfigError(ChatError):
    """Configuration or initialization error."""
    pass


class AuthError(ChatError):
    """Authentication failed with provider."""
    pass


class ModelError(ChatError):
    """Model-specific error (limits, availability)."""
    pass


class ProviderError(ChatError):
    """Provider API error."""
    pass


# === Configuration ===

@dataclass
class ClientConfig:
    """Unified configuration for chat clients."""
    provider: str
    base_url: str
    api_key: str
    model: str
    api_version: str | None = None
    deployment: str | None = None  # Azure-specific
    timeout: float = 30.0
    
    def __post_init__(self):
        # Validate required fields
        assert self.provider, "Provider must be specified"
        assert self.base_url, "Base URL must be specified"
        assert self.api_key, "API key must be specified"
        assert self.model, "Model must be specified"
    
    @classmethod
    def from_dict(cls, data: dict) -> ClientConfig:
        """Create config from dictionary with environment variable expansion."""
        expanded = _expand_env(data)
        return cls(**{k: v for k, v in expanded.items() 
                     if k in cls.__dataclass_fields__})


# === HTTP Utilities ===

def with_retry(func, attempts: int = 3):
    """Simple retry wrapper for HTTP operations."""
    last_error = None
    backoff = [0, 0.1, 0.5]
    
    for attempt in range(attempts):
        try:
            return func()
        except Exception as e:
            last_error = e
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                status = e.response.status_code
                # Only retry on server errors
                if status >= 500 and attempt < attempts - 1:
                    delay = backoff[min(attempt, len(backoff) - 1)]
                    logger.debug(f"Retry {attempt + 1}/{attempts} after {delay}s")
                    time.sleep(delay)
                    continue
            # Don't retry on client errors or non-HTTP errors
            raise
    
    raise last_error


# === Chat Clients ===

class ChatClient:
    """Base client for OpenAI-compatible chat APIs."""

    def __init__(self, config: ClientConfig):
        self.config = config
        self._validate_config()

    def _validate_config(self):
        """Validate provider-specific configuration."""
        # Base validation happens in ClientConfig.__post_init__
        pass

    def chat(self, messages: Iterable[ChatMessage]) -> ChatResponse:
        """Send messages and return structured response."""
        messages = list(messages)
        validate_message_size(messages, self.config.model)
        
        def _request():
            with HttpSession(self.config.base_url, timeout=self.config.timeout) as sess:
                payload = {
                    "model": self.config.model,
                    "messages": [m.to_dict() for m in messages],
                }
                headers = {
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                }
                
                with sess.post("/v1/chat/completions", 
                             body=json.dumps(payload), 
                             headers=headers) as resp:
                    if resp.status == 401:
                        raise AuthError("Invalid API key", provider=self.config.provider)
                    elif resp.status >= 400:
                        error_data = json.loads(resp.read().decode())
                        raise ProviderError(
                            f"API error: {error_data.get('error', {}).get('message', 'Unknown')}",
                            status=resp.status,
                            error=error_data
                        )
                    
                    data = json.loads(resp.read().decode())
                    return self._parse_response(data)
        
        return with_retry(_request)

    def _parse_response(self, data: dict) -> ChatResponse:
        """Parse provider response into ChatResponse."""
        choice = data["choices"][0]
        return ChatResponse(
            content=choice["message"]["content"],
            model=data.get("model"),
            usage=data.get("usage"),
            raw_response=data
        )


class AzureChatClient(ChatClient):
    """Client for Azure OpenAI chat API."""

    def _validate_config(self):
        super()._validate_config()
        if not self.config.deployment:
            # Use model name as deployment if not specified
            self.config.deployment = self.config.model
        if not self.config.api_version:
            self.config.api_version = "2023-05-15"

    def chat(self, messages: Iterable[ChatMessage]) -> ChatResponse:
        """Azure-specific chat implementation."""
        messages = list(messages)
        validate_message_size(messages, self.config.model)
        
        def _request():
            with HttpSession(self.config.base_url, timeout=self.config.timeout) as sess:
                payload = {"messages": [m.to_dict() for m in messages]}
                headers = {
                    "api-key": self.config.api_key,
                    "Content-Type": "application/json",
                }
                path = (f"/openai/deployments/{self.config.deployment}"
                       f"/chat/completions?api-version={self.config.api_version}")
                
                with sess.post(path, body=json.dumps(payload), headers=headers) as resp:
                    if resp.status == 401:
                        raise AuthError("Invalid API key", provider="azure")
                    elif resp.status >= 400:
                        error_data = json.loads(resp.read().decode())
                        raise ProviderError(
                            f"Azure API error",
                            status=resp.status,
                            error=error_data
                        )
                    
                    data = json.loads(resp.read().decode())
                    return self._parse_response(data)
        
        return with_retry(_request)


class AnthropicChatClient(ChatClient):
    """Client for Anthropic chat API."""

    def _validate_config(self):
        super()._validate_config()
        if not self.config.api_version:
            self.config.api_version = "2023-06-01"

    def chat(self, messages: Iterable[ChatMessage]) -> ChatResponse:
        """Anthropic-specific chat implementation."""
        messages = list(messages)
        validate_message_size(messages, self.config.model)
        
        # Extract system message if present
        system_messages = []
        user_messages = []
        
        for msg in messages:
            if msg.role == Role.SYSTEM:
                system_messages.extend(msg.content)
            else:
                user_messages.append(msg)
        
        def _request():
            with HttpSession(self.config.base_url, timeout=self.config.timeout) as sess:
                payload = {
                    "model": self.config.model,
                    "messages": [m.to_dict() for m in user_messages],
                    "max_tokens": MODEL_LIMITS.get(self.config.model, {}).get("output", 4096)
                }
                
                if system_messages:
                    # Anthropic expects system as a single string
                    system_text = " ".join(p.text for p in system_messages 
                                         if isinstance(p, TextPart))
                    payload["system"] = system_text
                
                headers = {
                    "x-api-key": self.config.api_key,
                    "anthropic-version": self.config.api_version,
                    "Content-Type": "application/json",
                }
                
                with sess.post("/v1/messages", body=json.dumps(payload), headers=headers) as resp:
                    if resp.status == 401:
                        raise AuthError("Invalid API key", provider="anthropic")
                    elif resp.status >= 400:
                        error_data = json.loads(resp.read().decode())
                        raise ProviderError(
                            f"Anthropic API error",
                            status=resp.status,
                            error=error_data
                        )
                    
                    data = json.loads(resp.read().decode())
                    return self._parse_anthropic_response(data)
        
        return with_retry(_request)

    def _parse_anthropic_response(self, data: dict) -> ChatResponse:
        """Parse Anthropic's response format."""
        # Anthropic returns content as an array
        content_blocks = data.get("content", [])
        text_content = " ".join(
            block["text"] for block in content_blocks 
            if block.get("type") == "text"
        )
        
        return ChatResponse(
            content=text_content,
            model=data.get("model"),
            usage=data.get("usage"),
            raw_response=data
        )


# === Factory Functions ===

def create_client(config: ClientConfig | dict) -> ChatClient:
    """Create appropriate chat client from configuration."""
    if isinstance(config, dict):
        config = ClientConfig.from_dict(config)
    
    provider = config.provider.lower()
    
    if provider == "openai":
        return ChatClient(config)
    elif provider in ["azure", "openai:azure"]:
        return AzureChatClient(config)
    elif provider == "anthropic":
        return AnthropicChatClient(config)
    else:
        raise ConfigError(f"Unknown provider: {config.provider}")


def load_config(path: str) -> ClientConfig:
    """Load configuration from JSON file."""
    try:
        data = json.loads(Path(path).read_text())
        return ClientConfig.from_dict(data)
    except (json.JSONDecodeError, IOError) as e:
        raise ConfigError(f"Failed to load config from {path}: {e}")


def _expand_env(value: Any) -> Any:
    """Recursively expand $VARNAME strings from environment."""
    if isinstance(value, str) and value.startswith("$"):
        var_name = value[1:]
        if var_name not in os.environ:
            raise ConfigError(f"Environment variable {var_name} not set")
        return os.environ[var_name]
    elif isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


# === CLI Support ===

def parse_fmt(fmt: str) -> tuple[str, str]:
    """Parse format string into (input_format, output_format)."""
    if ":" in fmt:
        in_fmt, out_fmt = fmt.split(":", 1)
    else:
        in_fmt, out_fmt = fmt, "txt"
    
    valid_formats = {"txt", "log", "json"}
    if in_fmt not in valid_formats or out_fmt not in valid_formats:
        raise ValueError(f"Format must be one of: {valid_formats}")
    
    return in_fmt, out_fmt


def parse_messages(data: str, fmt: str) -> list[ChatMessage]:
    """Parse input data into messages based on format."""
    if fmt == "txt":
        text = data.strip()
        return [ChatMessage(Role.USER, [TextPart(text)])] if text else []
    
    elif fmt == "log":
        messages = []
        for line in data.strip().splitlines():
            if not line:
                continue
            obj = json.loads(line)
            role = Role(obj["role"])
            content = obj["content"]
            
            if isinstance(content, str):
                messages.append(ChatMessage(role, [TextPart(content)]))
            else:
                parts = []
                for part in content:
                    if part["type"] == "text":
                        parts.append(TextPart(part["text"]))
                    elif part["type"] == "image_url":
                        img = part["image_url"]
                        parts.append(ImagePart(img["url"], img.get("detail")))
                messages.append(ChatMessage(role, parts))
        return messages
    
    elif fmt == "json":
        # Support JSON array of messages
        messages_data = json.loads(data)
        if not isinstance(messages_data, list):
            messages_data = [messages_data]
        
        messages = []
        for msg_data in messages_data:
            role = Role(msg_data["role"])
            content = msg_data["content"]
            
            if isinstance(content, str):
                messages.append(ChatMessage(role, [TextPart(content)]))
            else:
                # Handle structured content
                parts = []
                for item in content:
                    if isinstance(item, str):
                        parts.append(TextPart(item))
                    elif item.get("type") == "text":
                        parts.append(TextPart(item["text"]))
                    elif item.get("type") == "image_url":
                        parts.append(ImagePart(
                            item["image_url"]["url"],
                            item["image_url"].get("detail")
                        ))
                messages.append(ChatMessage(role, parts))
        
        return messages
    
    else:
        raise ValueError(f"Unknown format: {fmt}")


def format_messages(messages: list[ChatMessage], response: ChatResponse, fmt: str) -> str:
    """Format messages for output based on format."""
    if fmt == "txt":
        return response.content
    
    elif fmt == "log":
        lines = []
        # Include all messages in log format
        for msg in messages:
            lines.append(json.dumps(msg.to_dict()))
        # Add assistant response
        lines.append(json.dumps({
            "role": "assistant",
            "content": response.content,
            "model": response.model,
            "created_at": response.created_at,
        }))
        return "\n".join(lines)
    
    elif fmt == "json":
        # Return complete conversation as JSON
        return json.dumps({
            "messages": [msg.to_dict() for msg in messages],
            "response": {
                "content": response.content,
                "model": response.model,
                "created_at": response.created_at,
                "usage": response.usage,
            }
        }, indent=2)
    
    else:
        raise ValueError(f"Unknown format: {fmt}")


def run(args: argparse.Namespace, *, in_stream=sys.stdin, out_stream=sys.stdout) -> None:
    """Run chat CLI with improved error handling."""
    try:
        in_fmt, out_fmt = parse_fmt(args.fmt)
        config = load_config(args.conf)
        
        # Load optional system prompt
        system_prompt = None
        if args.prompt:
            system_prompt = Path(args.prompt).read_text().strip()
        
        # Parse input messages
        data = in_stream.read()
        messages = parse_messages(data, in_fmt)
        
        # Add system prompt if provided
        if system_prompt:
            messages.insert(0, ChatMessage(Role.SYSTEM, [TextPart(system_prompt)]))
        
        # Create client and chat
        client = create_client(config)
        response = client.chat(messages)
        
        # Format output
        output = format_messages(messages, response, out_fmt)
        out_stream.write(output)
        if out_fmt in ["log", "json"]:
            out_stream.write("\n")
            
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except AuthError as e:
        logger.error(f"Authentication failed: {e}")
        sys.exit(1)
    except ModelError as e:
        logger.error(f"Model error: {e}")
        if e.context:
            logger.debug(f"Context: {e.context}")
        sys.exit(1)
    except ProviderError as e:
        logger.error(f"Provider error: {e}")
        if e.context:
            logger.debug(f"Context: {e.context}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


@tool("chat")
def register(subparsers: SubParser) -> None:
    """Register chat tool with argument parser."""
    parser = subparsers.add_parser("chat", help="Interact with a chat model")
    parser.add_argument(
        "--fmt", 
        default="txt:txt", 
        help="Input:output format (txt, log, or json)"
    )
    parser.add_argument(
        "-p", "--prompt", 
        metavar="FILE", 
        help="System prompt file"
    )
    parser.add_argument(
        "-c", "--conf", 
        metavar="FILE", 
        required=True, 
        help="Model configuration file"
    )
    parser.set_defaults(func=run)