# manifold_cli/main.py
import typer
from manifold_core.sync_engine import sync_all
from manifold_cli.commands import unifi
from manifold_cli.commands import slack
from manifold_cli.commands import autotask

app = typer.Typer()
app.add_typer(unifi.app, name="unifi")
app.add_typer(slack.slack_app, name="slack")
app.add_typer(autotask.autotask_app, name="autotask")

@app.command()
def sync():
    sync_all()

if __name__ == "__main__":
    app()
