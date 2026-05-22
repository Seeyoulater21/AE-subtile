from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

from aesubtitle import __version__
from aesubtitle.cli import transcribe_source
from aesubtitle.models import TranscriptError
from aesubtitle.transcriber import DEFAULT_COMPUTE_TYPE, DEFAULT_MODEL, TranscriptionError

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ae-subtitle-server")
    parser.add_argument("--host", default=os.environ.get("AESUBTITLE_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("AESUBTITLE_PORT", DEFAULT_PORT)))
    parser.add_argument("--model", default=os.environ.get("AESUBTITLE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--language", default=os.environ.get("AESUBTITLE_LANGUAGE"))
    parser.add_argument("--device", default=os.environ.get("AESUBTITLE_DEVICE", "auto"))
    parser.add_argument("--compute-type", default=os.environ.get("AESUBTITLE_COMPUTE_TYPE", DEFAULT_COMPUTE_TYPE))
    parser.add_argument("--glossary", default=os.environ.get("AESUBTITLE_GLOSSARY"))
    parser.add_argument("--condition-on-previous-text", action="store_true")
    return parser


def create_server(
    address: tuple[str, int] = (DEFAULT_HOST, DEFAULT_PORT),
    model: str = DEFAULT_MODEL,
    language: str | None = None,
    device: str = "auto",
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    glossary: str | None = None,
    condition_on_previous_text: bool = False,
    transcriber_factory: Callable[[argparse.Namespace], object] | None = None,
) -> ThreadingHTTPServer:
    config = {
        "model": model,
        "language": language,
        "device": device,
        "compute_type": compute_type,
        "glossary": glossary,
        "condition_on_previous_text": condition_on_previous_text,
        "transcriber_factory": transcriber_factory,
    }

    class Handler(BaseHTTPRequestHandler):
        server_version = "AESubtitleServer/0.1"

        def do_GET(self) -> None:
            if self.path != "/health":
                self._send_json({"ok": False, "error": "Not found"}, status=404)
                return
            self._send_json({"ok": True, "service": "AE Subtitle", "version": __version__})

        def do_POST(self) -> None:
            if self.path != "/transcribe":
                self._send_json({"ok": False, "error": "Not found"}, status=404)
                return

            try:
                request = self._read_json()
                source_path = request.get("source_path")
                if not isinstance(source_path, str) or not source_path:
                    raise ValueError("source_path is required")
                payload = transcribe_source(
                    source=source_path,
                    model=config["model"],
                    language=config["language"],
                    device=config["device"],
                    compute_type=config["compute_type"],
                    glossary=config["glossary"],
                    condition_on_previous_text=bool(config["condition_on_previous_text"]),
                    transcriber_factory=config["transcriber_factory"],
                )
            except (OSError, TranscriptionError, TranscriptError, ValueError, json.JSONDecodeError) as error:
                self._send_json({"ok": False, "error": str(error)}, status=400)
                return

            self._send_json(payload)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_json(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            return json.loads(body or "{}")

        def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return ThreadingHTTPServer(address, Handler)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    httpd = create_server(
        (args.host, args.port),
        model=args.model,
        language=args.language,
        device=args.device,
        compute_type=args.compute_type,
        glossary=args.glossary,
        condition_on_previous_text=args.condition_on_previous_text,
    )
    print(f"AE Subtitle server listening on http://{args.host}:{args.port}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
