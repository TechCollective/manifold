# manifold_cli/main.py
import typer
from manifold_core.sync_engine import sync_all
from manifold_cli.commands import unifi

app = typer.Typer()
app.add_typer(unifi.app, name="unifi")

@app.command()
def sync():
    sync_all()

if __name__ == "__main__":
    app()
