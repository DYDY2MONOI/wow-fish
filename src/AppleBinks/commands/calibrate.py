"""`AppleBinks calibrate SCREENSHOT`: measure the interact icon's on-screen size once."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Annotated

import typer

from AppleBinks import paths
from AppleBinks.commands._common import fail, load_config_or_fail
from AppleBinks.config import save_config


def calibrate(
    screenshot: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, help="Screenshot showing the gold gear icon."),
    ],
    save: bool = typer.Option(False, "--save", help="Write the result into the config file."),
) -> None:
    """Find the interact icon in a screenshot and report its size, position, and a threshold."""
    import cv2

    from AppleBinks.capture import find_window
    from AppleBinks.vision.calibrate import calibrate_icon_scale
    from AppleBinks.vision.template import load_icon_templates

    cfg = load_config_or_fail()
    frame = cv2.imread(str(screenshot))
    if frame is None:
        fail(f"cannot read image {screenshot}")
    cal = calibrate_icon_scale(frame, load_icon_templates(), match_width=cfg.vision.match_width)
    h, w = frame.shape[:2]
    typer.echo(
        f"icon_size_px={cal.icon_size_px} native={cal.native_size} score={cal.score:.3f} "
        f"at ({cal.x}, {cal.y}) in {w}x{h}"
    )
    # A Retina screenshot is twice the points the bot captures: save the size the run will see.
    window = find_window("World of Warcraft")
    if window is not None and w != window.width:
        cal = replace(cal, icon_size_px=max(1, round(cal.icon_size_px * window.width / w)))
        typer.echo(
            f"game window is {window.width} px wide, so the run will use {cal.icon_size_px} px"
        )
    threshold = cal.suggested_threshold()
    typer.echo(f"suggested icon_threshold={threshold:.2f}")
    if not cal.valid:
        typer.echo(
            "warning: no gold interact icon found in this screenshot (take it with the bobber in "
            "range, gear icon visible)",
            err=True,
        )
        if save:
            typer.echo("not saved", err=True)
            raise typer.Exit(code=1)
    if save:
        vision = replace(
            cfg.vision,
            icon_size_px=cal.icon_size_px,
            icon_native_size=cal.native_size,
            icon_threshold=threshold,
        )
        save_config(replace(cfg, vision=vision))
        typer.echo(f"saved to {paths.config_file()}")


def register(app: typer.Typer) -> None:
    app.command("calibrate")(calibrate)
