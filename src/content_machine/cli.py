"""`cm` command-line interface."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from .config import list_series, load_series, load_settings
from .models import Topic
from .pipeline import Pipeline

app = typer.Typer(help="Content Machine: trending topics -> scripts -> Shorts/Reels.",
                  no_args_is_help=True)
series_app = typer.Typer(help="Manage series definitions.")
app.add_typer(series_app, name="series")
console = Console()


@series_app.command("list")
def series_list() -> None:
    """List configured series."""
    table = Table("id", "name", "language", "region", "sources")
    for s in list_series():
        srcs = [n for n in ("youtube", "instagram") if getattr(s.sources, n)]
        table.add_row(s.id, s.name, s.language, s.region, ", ".join(srcs))
    console.print(table)


@app.command()
def trends(series_id: str, limit: int = typer.Option(10, help="Topics to show")) -> None:
    """Fetch trends for a series and print ranked topics."""
    pipe = Pipeline(load_settings())
    _, topics = pipe.discover(load_series(series_id))
    table = Table("#", "score", "source", "topic")
    for i, t in enumerate(topics[:limit], start=1):
        table.add_row(str(i), f"{t.score:.3f}", t.supporting_trends[0].source.value, t.title)
    console.print(table)


@app.command()
def script(
    series_id: str,
    topic: str | None = typer.Option(None, help="Use this topic instead of the top trend"),
) -> None:
    """Generate a script and print it as JSON."""
    series = load_series(series_id)
    pipe = Pipeline(load_settings())
    if topic:
        chosen = Topic(title=topic)
    else:
        _, topics = pipe.discover(series)
        if not topics:
            raise typer.Exit("No topics found.")
        chosen = topics[0]
    console.print(f"[bold]Topic:[/] {chosen.title}")
    console.print_json(pipe.write_script(series, chosen).model_dump_json())


@app.command()
def make(
    series_id: str,
    topic: str | None = typer.Option(None, help="Use this topic instead of the top trend"),
    dry_run: bool = typer.Option(False, help="Stop after writing the script"),
) -> None:
    """Run the full pipeline and render a video."""
    run_dir = Pipeline(load_settings()).run(load_series(series_id), topic, dry_run=dry_run)
    console.print(f"[green]Done:[/] {run_dir}")


@app.command()
def runs() -> None:
    """List previous runs."""
    pipe = Pipeline(load_settings(), sources=[])
    table = Table("run", "stages")
    for d in pipe.storage.list_runs():
        m = json.loads((d / "manifest.json").read_text())
        table.add_row(d.name, " ".join(f"{s['name']}:{s['status']}" for s in m["stages"]))
    console.print(table)


if __name__ == "__main__":
    app()
