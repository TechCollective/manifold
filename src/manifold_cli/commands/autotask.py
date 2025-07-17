import typer
from rich import print
from rich.table import Table
from typing import Optional
import inspect

from manifold_core.plugins.autotask.core import (
    list_autotask_integrations,
    add_autotask_integration,
    edit_autotask_integration,
    delete_autotask_integration,
    set_autotask_credentials,
)
from manifold_core.plugins.autotask.webhooks import list_webhooks as core_list_webhooks


autotask_app = typer.Typer(help="Manage Autotask integrations")


@autotask_app.command("list")
def list_integrations():
    """List all Autotask integrations."""
    table = Table(title="Autotask Integrations")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("API URL", style="magenta")
    table.add_column("Credentials", justify="center")

    for record in list_autotask_integrations():
        table.add_row(
            str(record.id),
            record.name,
            record.api_url,
            "✅" if record.has_credentials else "❌",
        )

    print(table)


@autotask_app.command("add")
def add(
    name: str = typer.Option(..., prompt=True),
    api_url: str = typer.Option(..., prompt=True),
    username: str = typer.Option(..., prompt=True),
    integration_code: str = typer.Option(..., prompt=True),
    secret: str = typer.Option(..., prompt=True, hide_input=True),
):
    """Add a new Autotask integration."""
    try:
        record = add_autotask_integration(name=name, api_url=api_url)
        set_autotask_credentials(record.id, username=username, integration_code=integration_code, secret=secret)
        print(f"[green]Autotask integration '{name}' added.[/green]")
    except Exception as e:
        print(f"[red]Failed to add integration: {e}[/red]")


@autotask_app.command("edit")
def edit(
    id: int = typer.Argument(...),
    name: Optional[str] = typer.Option(None),
    api_url: Optional[str] = typer.Option(None),
):
    """Edit an existing Autotask integration by ID."""
    updates = {}
    if name:
        updates["name"] = name
    if api_url:
        updates["api_url"] = api_url

    if not updates:
        print("[red]No updates provided.[/red]")
        raise typer.Exit(code=1)

    try:
        edit_autotask_integration(id, updates)
        print(f"[green]Integration {id} updated.[/green]")
    except Exception as e:
        print(f"[red]Failed to update: {e}[/red]")


@autotask_app.command("delete")
def delete(id: int):
    """Delete an Autotask integration and its credentials."""
    if not typer.confirm(f"Are you sure you want to delete Autotask integration {id}?"):
        raise typer.Exit()

    try:
        delete_autotask_integration(id)
        print(f"[green]Deleted Autotask integration {id}.[/green]")
    except Exception as e:
        print(f"[red]Failed to delete: {e}[/red]")


@autotask_app.command("add-creds")
def add_credentials(
    id: int = typer.Argument(...),
    username: str = typer.Option(..., prompt=True),
    integration_code: str = typer.Option(..., prompt=True),
    secret: str = typer.Option(..., prompt=True, hide_input=True),
):
    """Store Autotask credentials securely."""
    try:
        set_autotask_credentials(id, username, integration_code, secret)
        print(f"[green]Credentials set for Autotask integration {id}.[/green]")
    except Exception as e:
        print(f"[red]Failed to set credentials: {e}[/red]")

@autotask_app.command("list-webhooks")
def list_webhooks(
    id: int = typer.Argument(..., help="Autotask integration ID")
):
    """List webhooks registered with Autotask for a specific integration."""

    # 🚨 Development safeguard: Detect accidental recursive call
    if inspect.currentframe().f_back.f_globals.get('list_webhooks') is list_webhooks:
        print("[red]Recursive call detected — you may be shadowing the core list_webhooks function.[/red]")
        raise typer.Exit(code=1)

    try:
        webhooks = core_list_webhooks(id)
    except Exception as e:
        print(f"[red]Failed to retrieve webhooks: {e}[/red]")
        raise typer.Exit(code=1)

    if not webhooks:
        print("[yellow]No webhooks found.[/yellow]")
        return

    table = Table(title=f"Webhooks for Autotask Integration {id}")
    table.add_column("ID", style="dim")
    table.add_column("Entity")
    table.add_column("Event")
    table.add_column("URL", style="magenta")
    table.add_column("Active", justify="center")

    for hook in webhooks:
        table.add_row(
            str(hook.id),
            hook.entity,
            hook.event,
            hook.url,
            "✅" if hook.is_active else "❌",
        )

    print(table)
