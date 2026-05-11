from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover - script entry point support
    import pathlib
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from pe_claw_gui.app.main import main
else:
    from .app.main import main


if __name__ == "__main__":
    main()
