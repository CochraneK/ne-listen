from __future__ import annotations

import argparse
import os
from pathlib import Path

from .adapters import CompatibleHttpAdapter
from .demo import synthetic_normalized
from .doctor import inspect
from .history import merge_history
from .io import read_json, write_json
from .metrics import analyze
from .normalize import normalize
from .report import render
from .security import is_local_api
from .semantic import DEFAULT_MODEL, DEFAULT_REVISION, analyze_semantic
from .snapshot import snapshot
from .textmining import select_text_corpus_song_ids


def _data_dir(value: str | None) -> Path:
    return Path(value or os.environ.get("NELISTEN_DATA_DIR") or "data").resolve()


def build_report(normalized: dict, data_dir: Path) -> Path:
    metrics = analyze(normalized)
    semantic_path = Path(os.environ.get("NELISTEN_SEMANTIC_PATH") or "public/semantic.json")
    if semantic_path.exists():
        semantic = read_json(semantic_path)
        if isinstance(semantic, dict) and semantic.get("available"):
            metrics["semantic"] = semantic
    report_dir = data_dir / "report"
    previous_path = report_dir / "history.previous.json"
    previous = read_json(previous_path) if previous_path.exists() else {}
    history = merge_history(previous, metrics, normalized.get("collectedAt"))
    metrics["history"] = history
    out = report_dir / "index.html"
    render(normalized, metrics, out)
    write_json(report_dir / "metrics.json", metrics)
    write_json(report_dir / "history.json", history)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ne-listen", description="NetEase listening archive and report generator")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_demo = sub.add_parser("demo", help="generate a synthetic demo report")
    p_demo.add_argument("--data-dir")

    p_sync = sub.add_parser("sync", help="collect a read-only snapshot from a compatible HTTP API")
    p_sync.add_argument("--base-url", default=os.environ.get("NELISTEN_API_BASE", "http://127.0.0.1:3000"))
    p_sync.add_argument("--cookie", default=os.environ.get("NELISTEN_COOKIE", ""))
    p_sync.add_argument("--uid", default=os.environ.get("NELISTEN_UID") or None)
    p_sync.add_argument("--data-dir")
    p_sync.add_argument("--text-max", type=int, default=int(os.environ.get("NELISTEN_TEXT_MAX", "180")), help="max songs for lyric text mining; 0 disables")
    p_sync.add_argument("--text-workers", type=int, default=int(os.environ.get("NELISTEN_TEXT_WORKERS", "4")), help="concurrent lyric requests, capped at 8")
    p_sync.add_argument("--allow-remote-api", action="store_true", help="explicitly allow sending credentials to a non-local API base")

    p_report = sub.add_parser("report", help="rebuild report from normalized latest.json")
    p_report.add_argument("--data-dir")
    p_report.add_argument("--input")

    p_import = sub.add_parser("import-raw", help="normalize an existing raw snapshot")
    p_import.add_argument("path")
    p_import.add_argument("--data-dir")

    p_doctor = sub.add_parser("doctor", help="inspect local state and coverage")
    p_doctor.add_argument("--data-dir")

    p_semantic = sub.add_parser("semantic", help="run multilingual embedding analysis on a private normalized archive")
    p_semantic.add_argument("--data-dir")
    p_semantic.add_argument("--input")
    p_semantic.add_argument("--output", default="public/semantic.json")
    p_semantic.add_argument("--model", default=os.environ.get("NELISTEN_SEMANTIC_MODEL", DEFAULT_MODEL))
    p_semantic.add_argument("--revision", default=os.environ.get("NELISTEN_SEMANTIC_REVISION", DEFAULT_REVISION))

    args = parser.parse_args(argv)
    data_dir = _data_dir(getattr(args, "data_dir", None))

    if args.cmd == "demo":
        normalized = synthetic_normalized()
        write_json(data_dir / "normalized" / "latest.json", normalized)
        out = build_report(normalized, data_dir)
        print(f"demo report: {out}")
        return 0

    if args.cmd == "sync":
        if args.cookie and not is_local_api(args.base_url) and not args.allow_remote_api:
            parser.error("refusing to send NELISTEN_COOKIE to a non-local API; self-host locally or pass --allow-remote-api explicitly")
        adapter = CompatibleHttpAdapter(args.base_url, cookie=args.cookie)
        raw = adapter.collect(uid=args.uid)
        normalized = normalize(raw)
        lyric_ids = select_text_corpus_song_ids(normalized, max_songs=args.text_max)
        if lyric_ids:
            raw["responses"]["lyrics"] = adapter.collect_lyrics(lyric_ids, max_workers=args.text_workers)
            normalized = normalize(raw)
        root = snapshot(raw, normalized, data_dir)
        out = build_report(normalized, data_dir)
        ok = sum(1 for v in normalized["capabilities"].values() if v)
        total = len(normalized["capabilities"])
        print(f"snapshot: {root}")
        print(f"capabilities: {ok}/{total}")
        if lyric_ids:
            text_meta = normalized.get("textCorpusMeta") or {}
            print(f"lyrics: {text_meta.get('successfulResponses', 0)}/{text_meta.get('selectedSongs', 0)}")
        print(f"report: {out}")
        return 0

    if args.cmd == "import-raw":
        raw = read_json(Path(args.path))
        normalized = normalize(raw)
        root = snapshot(raw, normalized, data_dir)
        out = build_report(normalized, data_dir)
        print(f"imported snapshot: {root}")
        print(f"report: {out}")
        return 0

    if args.cmd == "report":
        path = Path(args.input) if args.input else data_dir / "normalized" / "latest.json"
        normalized = read_json(path)
        out = build_report(normalized, data_dir)
        print(f"report: {out}")
        return 0

    if args.cmd == "doctor":
        path = data_dir / "normalized" / "latest.json"
        normalized = read_json(path) if path.exists() else None
        for name, ok, detail in inspect(data_dir, normalized):
            print(f"{'✓' if ok else '○'} {name}: {detail}")
        return 0

    if args.cmd == "semantic":
        path = Path(args.input) if args.input else data_dir / "normalized" / "latest.json"
        normalized = read_json(path)
        result = analyze_semantic(normalized, model_name=args.model, revision=args.revision)
        output = Path(args.output)
        write_json(output, result)
        print(f"semantic report: {output}")
        print(f"available: {bool(result.get('available'))}")
        return 0 if result.get("available") else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
