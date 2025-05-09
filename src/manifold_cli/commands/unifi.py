import typer
from rich import print
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table

from manifold_core.plugins.unifi.servers import (
    list_unifi_servers,
    add_unifi_server,
    edit_unifi_server,
    delete_unifi_server,
    set_unifi_credentials,
)
from manifold_core.plugins.unifi.sites import (
    get_unifi_sites,
    sync_unifi_sites,
)

from manifold_core.plugins.unifi.devices import (
    sync_unifi_devices,
    lookup_unifi_device
)

unifi_app = typer.Typer(help="UniFi integration")
server_app = typer.Typer(help="Manage UniFi network servers")
unifi_app.add_typer(server_app, name="server")
app = unifi_app

def print_sites_table(sites, server_name=""):
    console = Console()
    table = Table(title=f"Sites for {server_name}" if server_name else "UniFi Sites")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="magenta")
    table.add_column("Role", style="green")

    for site in sites:
        table.add_row(site.get("name", ""), site.get("desc", ""), site.get("role", ""))

    console.print(table)

@server_app.command("list")
def list_servers():
    """List all UniFi servers."""
    servers = list_unifi_servers()
    if not servers:
        print("[yellow]No UniFi servers found.[/yellow]")
        raise typer.Exit()

    table = Table(title="UniFi Network Servers")
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Name", style="cyan")
    table.add_column("Host", style="magenta")
    table.add_column("Port", justify="right")
    table.add_column("Credentials", justify="center")

    for s in servers:
        table.add_row(
            str(s.id),
            s.name,
            s.host,
            str(s.port),
            "[green]✔[/green]" if s.has_credentials else "[red]✘[/red]",
        )

    Console().print(table)

@server_app.command("add")
def add(
    name: str = typer.Option(..., prompt=True),
    host: str = typer.Option(..., prompt=True),
    port: int = typer.Option(443, prompt=True),
):
    """Add a new UniFi server."""
    try:
        add_unifi_server(name, host, port)
        print(f"[green]Server '{name}' added.[/green]")
    except Exception as e:
        print(f"[red]Failed to add server: {e}[/red]")

@server_app.command("edit")
def edit(
    id: int = typer.Argument(...),
    name: Optional[str] = typer.Option(None),
    host: Optional[str] = typer.Option(None),
    port: Optional[int] = typer.Option(None),
):
    """Edit an existing UniFi server by ID."""
    updates = {}
    if name: updates["name"] = name
    if host: updates["host"] = host
    if port: updates["port"] = port

    if not updates:
        print("[red]No fields provided to update.[/red]")
        raise typer.Exit(code=1)

    try:
        edit_unifi_server(id, updates)
        print(f"[green]Server {id} updated.[/green]")
    except Exception as e:
        print(f"[red]Failed to update server: {e}[/red]")

@server_app.command("delete")
def delete(id: int):
    """Delete a UniFi server by ID."""
    confirm = typer.confirm(f"Are you sure you want to delete server {id}?")
    if not confirm:
        raise typer.Exit()

    try:
        delete_unifi_server(id)
        print(f"[green]Deleted server {id}.[/green]")
    except Exception as e:
        print(f"[red]Failed to delete: {e}[/red]")

@server_app.command("add-creds")
def add_creds(
    id: int = typer.Argument(...),
    username: str = typer.Option(..., prompt=True, hide_input=False),
    password: str = typer.Option(..., prompt=True, hide_input=True),
):
    """Store UniFi server credentials securely in Bitwarden."""
    try:
        set_unifi_credentials(id, username, password)
        print(f"[green]Credentials set for server {id}.[/green]")
    except Exception as e:
        print(f"[red]Failed to set credentials: {e}[/red]")

@server_app.command("display-sites")
def display_sites(server_id: Optional[int] = typer.Argument(None)):
    """Display UniFi sites from one or all servers."""
    if server_id is not None:
        try:
            sites = get_unifi_sites(server_id)
            print_sites_table(sites, server_name="(single)")
        except Exception as e:
            print(f"[red]Failed to fetch sites: {e}[/red]")
    else:
        # Loop over all servers if needed
        from manifold_core.plugins.unifi.servers import list_unifi_servers
        servers = list_unifi_servers()
        for server in servers:
            try:
                sites = get_unifi_sites(server.id)
                print_sites_table(sites, server.name)
            except Exception as e:
                print(f"[red]Failed to fetch sites from {server.name}: {e}[/red]")

@server_app.command("sync-sites")
def sync_sites(server_id: Optional[int] = typer.Argument(None)):
    """Sync UniFi sites from all or a specific server into the database."""
    try:
        count = sync_unifi_sites(server_id)
        print(f"[green]Synced {count} sites.[/green]")
    except Exception as e:
        print(f"[red]Failed to sync sites: {e}[/red]")

@server_app.command("sync-devices")
def sync_devices():
    """Sync UniFi devices from all UniFi servers into the database."""
    try:
        count = sync_unifi_devices()  # ✅ no arguments
        print(f"[green]Synced {count} devices from all servers.[/green]")
    except Exception as e:
        print(f"[red]Failed to sync devices: {e}[/red]")

@app.command("lookup-device")
def lookup_device(
    mac: Optional[str] = typer.Option(None, help="MAC address"),
    serial: Optional[str] = typer.Option(None, help="Serial number"),
):
    """Lookup a UniFi device by MAC or serial number."""
    try:
        if not mac and not serial:
            print("[red]You must provide either a MAC or serial.[/red]")
            raise typer.Exit(code=1)

        identifier = mac or serial
        result = lookup_unifi_device(identifier)

        if not result:
            print("[yellow]Device not found.[/yellow]")
            return

        table = Table(title="UniFi Device Lookup")

        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        for key, value in result.items():
            if isinstance(value, list):
                value = ", ".join(value)
            table.add_row(key.replace("_", " ").capitalize(), str(value))

        console = Console()
        console.print(table)

    except Exception as e:
        print(f"[red]Lookup failed: {e}[/red]")

