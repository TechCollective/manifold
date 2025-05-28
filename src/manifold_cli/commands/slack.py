# manifold_cli/plugins/slack.py

import typer
from rich import print
from rich.table import Table
from typing import Optional

from manifold_core.plugins.slack.core import (
    list_slack_integrations,
    add_slack_integration,
    edit_slack_integration,
    delete_slack_integration,
    set_slack_token,
)

slack_app = typer.Typer(help="Manage Slack integrations")

@slack_app.command("list")
def list_integrations():
    """List all Slack integrations."""
    table = Table(title="Slack Integrations")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Workspace", style="magenta")
    table.add_column("Token", justify="center")

    for s in list_slack_integrations():
        table.add_row(str(s.id), s.name, s.workspace, "✅" if s.has_token else "❌")

    print(table)

@slack_app.command("add")
def add(
    name: str = typer.Option(..., prompt=True),
    workspace: str = typer.Option(..., prompt=True),
):
    """Add a new Slack integration."""
    try:
        add_slack_integration(name=name, workspace=workspace)
        print(f"[green]Slack integration '{name}' added.[/green]")
    except Exception as e:
        print(f"[red]Failed to add integration: {e}[/red]")

@slack_app.command("edit")
def edit(
    id: str = typer.Argument(...),
    name: Optional[str] = typer.Option(None),
    workspace: Optional[str] = typer.Option(None),
):
    """Edit an existing Slack integration by ID."""
    updates = {}
    if name:
        updates["name"] = name
    if workspace:
        updates["workspace"] = workspace

    if not updates:
        print("[red]No updates provided.[/red]")
        raise typer.Exit(code=1)

    try:
        edit_slack_integration(id, updates)
        print(f"[green]Integration {id} updated.[/green]")
    except Exception as e:
        print(f"[red]Failed to update: {e}[/red]")

@slack_app.command("delete")
def delete(id: str):
    """Delete a Slack integration and its token."""
    if not typer.confirm(f"Are you sure you want to delete Slack integration {id}?"):
        raise typer.Exit()

    try:
        delete_slack_integration(id)
        print(f"[green]Deleted Slack integration {id}.[/green]")
    except Exception as e:
        print(f"[red]Failed to delete: {e}[/red]")

@slack_app.command("add-token")
def add_token(
    id: str = typer.Argument(...),
    token: str = typer.Option(..., prompt=True, hide_input=True),
):
    """Store Slack token securely."""
    try:
        set_slack_token(id, token)
        print(f"[green]Token set for Slack integration {id}.[/green]")
    except Exception as e:
        print(f"[red]Failed to set token: {e}[/red]")
