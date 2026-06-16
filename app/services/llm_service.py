import json
import logging
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError

from app.config.settings import Settings
from app.models.analysis import AnalysisResult

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "analysis_system.txt"
JSON_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
LOCAL_HOSTS = {"localhost", "127.0.0.1", "host.docker.internal", "::1"}
NON_RETRYABLE_STATUS = {401, 403, 404, 429}


class LLMServiceError(Exception):
    """Raised when the LLM request or response parsing fails."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    async def verify_connection(self) -> None:
        url = f"{self._settings.llm_base_url.rstrip('/')}/models"
        try:
            async with httpx.AsyncClient(
                timeout=self._settings.llm_timeout_seconds,
            ) as client:
                response = await client.get(url, headers=self._build_headers())
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise LLMServiceError(
                f"Cannot reach Ollama at {self._settings.llm_base_url}. "
                "Run: ollama serve"
            ) from exc

        model_ids = {
            item.get("id", "")
            for item in data.get("data", [])
            if isinstance(item, dict)
        }
        if self._settings.llm_model not in model_ids:
            available = ", ".join(sorted(model_ids)) or "none"
            raise LLMServiceError(
                f"Model '{self._settings.llm_model}' is not available in Ollama. "
                f"Available: {available}. Run: ollama pull {self._settings.llm_model}"
            )

        logger.info(
            "Ollama ready at %s with model %s",
            self._settings.llm_base_url,
            self._settings.llm_model,
        )

    async def analyze_lyrics(self, lyrics: str) -> AnalysisResult:
        attempts: list[tuple[str, bool, bool]] = [
            ("openai-json", True, False),
            ("openai-plain", False, False),
        ]
        if self._is_local_ollama():
            attempts.append(("ollama-native", False, True))

        last_error: LLMServiceError | None = None
        for attempt_name, json_mode, use_native in attempts:
            try:
                content = await self._request_completion(
                    lyrics,
                    json_mode=json_mode,
                    use_native=use_native,
                )
                return self._parse_result(content)
            except LLMServiceError as exc:
                last_error = exc
                if exc.status_code in NON_RETRYABLE_STATUS:
                    raise
                logger.warning("%s failed: %s", attempt_name, exc)

        if last_error is not None:
            raise last_error
        raise LLMServiceError("All LLM attempts failed")

    async def _request_completion(
        self,
        lyrics: str,
        *,
        json_mode: bool,
        use_native: bool,
    ) -> str:
        messages = self._build_messages(lyrics)
        if use_native:
            url = f"{self._ollama_root_url()}/api/chat"
            payload: dict[str, object] = {
                "model": self._settings.llm_model,
                "messages": messages,
                "stream": False,
                "format": "json",
                "options": {"temperature": self._settings.llm_temperature},
            }
        else:
            url = f"{self._settings.llm_base_url.rstrip('/')}/chat/completions"
            payload = {
                "model": self._settings.llm_model,
                "stream": False,
                "temperature": self._settings.llm_temperature,
                "messages": messages,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(
                timeout=self._settings.llm_timeout_seconds,
            ) as client:
                response = await client.post(
                    url,
                    headers=self._build_headers(),
                    json=payload,
                )
                if response.is_error:
                    self._raise_api_error(response, use_native=use_native)
                data = response.json()
        except LLMServiceError:
            raise
        except httpx.HTTPError as exc:
            logger.exception("Ollama HTTP request failed")
            raise LLMServiceError(
                "Failed to reach Ollama. Is it running? Try: ollama serve"
            ) from exc

        if use_native:
            try:
                content = data["message"]["content"]
            except (KeyError, TypeError) as exc:
                logger.error("Unexpected Ollama native response: %s", data)
                raise LLMServiceError("Invalid native response from Ollama") from exc
        else:
            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                logger.error("Unexpected Ollama OpenAI response: %s", data)
                raise LLMServiceError("Invalid OpenAI-compatible response from Ollama") from exc

        if not content or not str(content).strip():
            raise LLMServiceError("Ollama returned empty content")

        return str(content)

    def _build_messages(self, lyrics: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self._system_prompt},
            {
                "role": "user",
                "content": f"Analyze the following song lyrics:\n\n{lyrics}",
            },
        ]

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._is_local_ollama():
            return headers

        if self._settings.llm_api_key is not None:
            api_key = self._settings.llm_api_key.get_secret_value().strip()
            if api_key and api_key.lower() != "ollama":
                headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _is_local_ollama(self) -> bool:
        host = urlparse(self._settings.llm_base_url).hostname or ""
        return host in LOCAL_HOSTS

    def _ollama_root_url(self) -> str:
        base = self._settings.llm_base_url.rstrip("/")
        if base.endswith("/v1"):
            return base[:-3]
        return base

    def _raise_api_error(
        self,
        response: httpx.Response,
        *,
        use_native: bool,
    ) -> None:
        message = response.text
        try:
            body = response.json()
            error = body.get("error")
            if isinstance(error, dict):
                message = str(error.get("message") or message)
            elif isinstance(error, str):
                message = error
            else:
                message = str(body.get("message") or message)
        except json.JSONDecodeError:
            pass

        api_name = "Ollama native API" if use_native else "Ollama OpenAI API"
        logger.error(
            "%s error %s at %s: %s",
            api_name,
            response.status_code,
            response.request.url,
            message,
        )

        hint = ""
        if response.status_code == 429 and "provider" in message.lower():
            hint = (
                " This looks like a cloud/proxy rate limit, not local Ollama. "
                f"Check LLM_BASE_URL={self._settings.llm_base_url}"
            )

        raise LLMServiceError(
            f"Ollama error ({response.status_code}): {message}{hint}",
            status_code=response.status_code,
        )

    def _parse_result(self, content: str) -> AnalysisResult:
        try:
            parsed = self._extract_json(content)
            return AnalysisResult.model_validate(parsed)
        except json.JSONDecodeError as exc:
            logger.error("Ollama returned non-JSON content: %s", content[:500])
            raise LLMServiceError("Language model returned invalid JSON") from exc
        except ValidationError as exc:
            logger.error("Ollama JSON failed validation: %s", exc)
            raise LLMServiceError(
                "Language model JSON does not match expected schema"
            ) from exc

    @staticmethod
    def _extract_json(content: str) -> dict[str, object]:
        text = content.strip()
        if text.startswith("```"):
            text = JSON_FENCE_PATTERN.sub("", text).strip()
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise json.JSONDecodeError("Expected JSON object", text, 0)
        return parsed
