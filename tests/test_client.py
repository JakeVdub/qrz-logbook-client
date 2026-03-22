import unittest
from unittest.mock import patch

from qrz_logbook_client.client import (
    QRZAPIError,
    QRZClient,
    _parse_response_text,
    _serialize_log_ids,
    _validate_user_agent,
)


class DummyResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class TestClientParsing(unittest.TestCase):
    def test_parse_response_coerces_known_types(self) -> None:
        parsed = _parse_response_text("RESULT=OK&COUNT=2&LOGID=42&LOGIDS=100,101")
        self.assertEqual(parsed["RESULT"], "OK")
        self.assertEqual(parsed["COUNT"], 2)
        self.assertEqual(parsed["LOGID"], 42)
        self.assertEqual(parsed["LOGIDS"], [100, 101])

    def test_serialize_log_ids_rejects_bad_values(self) -> None:
        with self.assertRaises(ValueError):
            _serialize_log_ids([])

        with self.assertRaises(ValueError):
            _serialize_log_ids([True])

        with self.assertRaises(ValueError):
            _serialize_log_ids([0])

        self.assertEqual(_serialize_log_ids([1, 2, 3]), "1,2,3")


class TestValidation(unittest.TestCase):
    def test_user_agent_validation(self) -> None:
        with self.assertRaises(ValueError):
            _validate_user_agent(" ")

        with self.assertRaises(ValueError):
            _validate_user_agent("python-requests")

        with self.assertRaises(ValueError):
            _validate_user_agent("python-requests/2.32.3")

        with self.assertRaises(ValueError):
            _validate_user_agent("node-fetch/3.3.2")

        _validate_user_agent("MyCoolUploadScript.py/1.0.0 (VA7STV)")


class TestQRZClientMethods(unittest.TestCase):
    def setUp(self) -> None:
        self.client = QRZClient(
            api_key="ABCD-0A0B-1C1D-2E2F",
            user_agent="MyCoolUploadScript.py/1.0.0 (VA7STV)",
        )

    def test_insert_record_parses_response(self) -> None:
        with patch.object(self.client, "send_request", return_value=DummyResponse("RESULT=OK&COUNT=1&LOGID=130")):
            result = self.client.insert_record("<eor>")

        self.assertEqual(result["RESULT"], "OK")
        self.assertEqual(result["COUNT"], 1)
        self.assertEqual(result["LOGID"], 130)
        self.assertEqual(result["ACTION"], "INSERT")

    def test_fetch_records_builds_default_option(self) -> None:
        with patch.object(self.client, "send_request", return_value=DummyResponse("RESULT=OK&COUNT=0")) as mocked_send:
            self.client.fetch_records(limit=250, offset=0)

        _, kwargs = mocked_send.call_args
        self.assertEqual(kwargs["action"], "FETCH")
        self.assertEqual(kwargs["params"]["OPTION"], "ALL,MAX:250,AFTERLOGID:0")

    def test_status_parses_nested_data(self) -> None:
        with patch.object(
            self.client,
            "send_request",
            return_value=DummyResponse("RESULT=OK&DATA=bookid=1&owner=K1ABC"),
        ):
            result = self.client.status()

        self.assertEqual(result["RESULT"], "OK")
        self.assertEqual(result["DATA"], {"bookid": "1", "owner": "K1ABC"})

    def test_insert_record_raises_for_fail_result(self) -> None:
        with patch.object(
            self.client,
            "send_request",
            return_value=DummyResponse("RESULT=FAIL&REASON=DuplicateQSO"),
        ):
            with self.assertRaises(QRZAPIError):
                self.client.insert_record("<eor>")

    def test_status_raises_for_auth_result(self) -> None:
        with patch.object(
            self.client,
            "send_request",
            return_value=DummyResponse("RESULT=AUTH&REASON=InsufficientPrivileges"),
        ):
            with self.assertRaises(QRZAPIError):
                self.client.status()

    def test_error_message_includes_reason(self) -> None:
        with patch.object(
            self.client,
            "send_request",
            return_value=DummyResponse("RESULT=FAIL&REASON=DuplicateQSO"),
        ):
            with self.assertRaisesRegex(QRZAPIError, "DuplicateQSO"):
                self.client.insert_record("<eor>")


if __name__ == "__main__":
    unittest.main()
