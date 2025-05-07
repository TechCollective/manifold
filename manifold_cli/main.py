# manifold_cli/main.py
import typer
from manifold_core.sync_engine import sync_all

app = typer.Typer()

@app.command()
def sync():
    sync_all()

if __name__ == "__main__":
    app()
