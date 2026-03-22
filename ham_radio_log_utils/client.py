from __future__ import annotations

from typing import Any, Final, Iterable
from urllib.parse import unquote_plus

import requests
from requests import Response, Session

BASE_URL: Final[str] = "https://logbook.qrz.com/api"
DEFAULT_USER_AGENT: Final[str] = "QRZPythonClient/0.1.0"


class QRZAPIError(RuntimeError):
    pass


class QRZClient:
    def __init__(
        self,
        api_key: str,
        user_agent: str = DEFAULT_USER_AGENT,
        base_url: str = BASE_URL,
        timeout: int = 30,
        session: Session | None = None,
    ) -> None:
        self._validate_api_key(api_key)
        _validate_user_agent(user_agent)

        self.api_key = api_key.strip()
        self.user_agent = user_agent.strip()
        self.base_url = base_url
        self.timeout = timeout
        self.session = session or requests.Session()

    def fetch_records(
        self,
        limit: int = 100,
        offset: int = 0,
        options: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        if limit < 0:
            raise ValueError("limit must be greater than or equal to 0")

        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0")

        if options is None:
            option_parts = ["ALL", f"MAX:{limit}", f"AFTERLOGID:{offset}"]
        else:
            option_parts = [part.strip() for part in options if part and part.strip()]
            if not option_parts:
                raise ValueError("options cannot be empty when provided")

        params = {
            "ACTION": "FETCH",
            "OPTION": ",".join(option_parts),
        }
        return self._send_request(action="FETCH", params=params)

    def insert_record(self, adif_data: str, replace_duplicates: bool = False) -> dict[str, Any]:
        if not adif_data or not adif_data.strip():
            raise ValueError("adif_data must be a non-empty string")

        params = {
            "ACTION": "INSERT",
            "ADIF": adif_data.strip(),
        }

        if replace_duplicates:
            params["OPTION"] = "REPLACE"

        return self._send_request(action="INSERT", params=params)

    def status(self, log_ids: Iterable[int] | None = None) -> dict[str, Any]:
        params: dict[str, str] = {"ACTION": "STATUS"}

        if log_ids is not None:
            params["LOGIDS"] = _serialize_log_ids(log_ids)

        response = self._send_request(action="STATUS", params=params)
        data_value = response.get("DATA")

        if isinstance(data_value, str) and data_value:
            response["DATA"] = _parse_nested_pairs(data_value)

        return response

    def delete_record(self, log_ids: Iterable[int]) -> dict[str, Any]:
        params = {
            "ACTION": "DELETE",
            "LOGIDS": _serialize_log_ids(log_ids),
        }
        return self._send_request(action="DELETE", params=params)

    def send_request(self, action: str, params: dict[str, str]) -> Response:
        headers = {"User-Agent": self.user_agent}
        data = {"KEY": self.api_key, **params}
        return self.session.post(self.base_url, data=data, headers=headers, timeout=self.timeout)

    def _send_request(self, action: str, params: dict[str, str]) -> dict[str, Any]:
        response = self.send_request(action=action, params=params)
        response.raise_for_status()
        parsed = _parse_response_text(response.text)
        parsed.setdefault("ACTION", action)

        result = str(parsed.get("RESULT", "")).upper()
        if result in {"FAIL", "AUTH"}:
            reason = parsed.get("REASON")
            if reason:
                raise QRZAPIError(f"QRZ API {result}: {reason}")
            raise QRZAPIError(f"QRZ API {result}")

        return parsed

    @staticmethod
    def _validate_api_key(api_key: str) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key must be a non-empty string")


_default_client: QRZClient | None = None


def setup(api_key: str, user_agent: str | None = None) -> None:
    global _default_client
    if user_agent is None:
        _default_client = QRZClient(api_key=api_key)
        return

    _default_client = QRZClient(api_key=api_key, user_agent=user_agent)


def fetch_records(limit: int = 100, offset: int = 0, options: Iterable[str] | None = None) -> dict[str, Any]:
    return _require_default_client().fetch_records(limit=limit, offset=offset, options=options)


def fetchRecords(limit: int = 100, offset: int = 0, options: Iterable[str] | None = None) -> dict[str, Any]:
    return fetch_records(limit=limit, offset=offset, options=options)


def insert_record(adif_data: str, replace_duplicates: bool = False) -> dict[str, Any]:
    return _require_default_client().insert_record(adif_data=adif_data, replace_duplicates=replace_duplicates)


def status(log_ids: Iterable[int] | None = None) -> dict[str, Any]:
    return _require_default_client().status(log_ids=log_ids)


def delete_record(log_ids: Iterable[int]) -> dict[str, Any]:
    return _require_default_client().delete_record(log_ids=log_ids)


def send_request(action: str, params: dict[str, str]) -> Response:
    return _require_default_client().send_request(action=action, params=params)


def _require_default_client() -> QRZClient:
    if _default_client is None:
        raise QRZAPIError("Default client is not configured. Call setup(api_key, user_agent=...) first.")
    return _default_client


def _parse_response_text(raw_text: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    known_keys = {"RESULT", "REASON", "LOGIDS", "LOGID", "COUNT", "DATA", "ADIF"}

    for token in raw_text.split("&"):
        if "=" not in token:
            continue

        key, value = token.split("=", 1)
        key = unquote_plus(key)
        value = unquote_plus(value)

        if key in known_keys:
            parsed[key] = value
            continue

        if "DATA" in parsed:
            parsed["DATA"] = f"{parsed['DATA']}&{key}={value}"
        else:
            parsed[key] = value

    if "COUNT" in parsed:
        try:
            parsed["COUNT"] = int(parsed["COUNT"])
        except (TypeError, ValueError):
            pass

    if "LOGID" in parsed:
        try:
            parsed["LOGID"] = int(parsed["LOGID"])
        except (TypeError, ValueError):
            pass

    if "LOGIDS" in parsed:
        parsed["LOGIDS"] = _parse_log_ids(parsed["LOGIDS"])

    return parsed


def _parse_log_ids(log_ids_raw: str) -> list[int]:
    ids: list[int] = []
    for value in log_ids_raw.split(","):
        value = value.strip()
        if not value:
            continue
        try:
            ids.append(int(value))
        except ValueError:
            continue
    return ids


def _parse_nested_pairs(raw_data: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for token in raw_data.split("&"):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        parsed[key] = value
    return parsed


def _serialize_log_ids(log_ids: Iterable[int]) -> str:
    normalized: list[str] = []

    for value in log_ids:
        if isinstance(value, bool):
            raise ValueError("log_ids must contain only integer values")
        if not isinstance(value, int):
            raise ValueError("log_ids must contain only integer values")
        if value < 1:
            raise ValueError("log_ids must contain positive integers")
        normalized.append(str(value))

    if not normalized:
        raise ValueError("log_ids cannot be empty")

    return ",".join(normalized)


def _validate_user_agent(user_agent: str) -> None:
    ua = user_agent.strip()
    if not ua:
        raise ValueError("user_agent must be a non-empty string")
    if len(ua) > 128:
        raise ValueError("user_agent must be 128 characters or fewer")
    lowered = ua.lower()
    if lowered.startswith("python-requests") or lowered.startswith("node-fetch"):
        raise ValueError("user_agent must identify your script/application")
