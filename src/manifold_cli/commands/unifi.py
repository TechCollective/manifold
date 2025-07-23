import typer
from rich import print
from typing import Optional, Dict, Any, List
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

from manifold_core.plugins.unifi.admins import (
    get_admins_for_server,
    get_admins_for_site,
    remove_admin_from_site,
    remove_admin_from_all_sites,
    get_admin_info,
    list_all_admins,
    sync_unifi_admins
)

from manifold_core.plugins.unifi.alerts import (
    sync_unifi_alerts
)

unifi_app = typer.Typer(help="UniFi integration")
server_app = typer.Typer(help="Manage UniFi network servers")
admin_app = typer.Typer(help="Manage UniFi admins")
unifi_app.add_typer(server_app, name="server")
unifi_app.add_typer(admin_app, name="admin")
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

@server_app.command("sync-alerts")
def sync_alerts():
    """Sync UniFi alerts from all UniFi servers into the database."""
    try:
        count = sync_unifi_alerts()
        print(f"[green]Synced {count} alerts from all servers.[/green]")
    except Exception as e:
        print(f"[red]Failed to sync alerts: {e}[/red]")

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

# Admin Management Commands
@admin_app.command("list")
def admin_list(
    server_id: Optional[int] = typer.Option(None, help="Filter by server ID")
):
    """List all admins from UniFi controllers."""
    try:
        if server_id:
            admins = get_admins_for_server(server_id)
        else:
            admins = list_all_admins()
        
        if not admins:
            print("[yellow]No admins found.[/yellow]")
            return
            
        table = Table(title="UniFi Admins")
        table.add_column("Server", style="cyan")
        table.add_column("Admin ID", style="dim")
        table.add_column("Name", style="magenta")
        table.add_column("Email", style="green")
        table.add_column("Role", style="yellow")
        
        for admin in admins:
            server_name = admin.get("server_name", "Unknown")
            if "server_host" in admin:
                server_name = f"{server_name} ({admin['server_host']})"
                
            table.add_row(
                server_name,
                admin.get("_id", "N/A"),
                admin.get("name", "N/A"),
                admin.get("email", "N/A"),
                admin.get("role", "N/A")
            )
            
        Console().print(table)
        
    except Exception as e:
        print(f"[red]Failed to list admins: {e}[/red]")

@admin_app.command("info")
def admin_info(
    server_id: int = typer.Argument(..., help="Server ID"),
    admin_id: str = typer.Argument(..., help="Admin ID"),
    exclude_sites: List[str] = typer.Option([], help="Site names to exclude from search")
):
    """Get detailed information about a specific admin across all sites."""
    try:
        admin_info = get_admin_info(server_id, admin_id, exclude_sites)
        
        if not admin_info or not admin_info.get('sites'):
            print("[yellow]Admin not found in any sites.[/yellow]")
            return
            
        print(f"[cyan]Admin ID: {admin_info['admin_id']}[/cyan]")
        print(f"[cyan]Total sites with access: {admin_info['total_sites']}[/cyan]")
        
        if admin_info['excluded_sites']:
            print(f"[yellow]Excluded sites: {', '.join(admin_info['excluded_sites'])}[/yellow]")
        
        table = Table(title=f"Admin {admin_id} Site Access")
        table.add_column("Site Name", style="cyan")
        table.add_column("Site Description", style="dim")
        table.add_column("Role", style="yellow")
        table.add_column("Email", style="green")
        
        for site_info in admin_info['sites']:
            admin_data = site_info['admin_info']
            table.add_row(
                site_info['site_name'],
                site_info['site_desc'],
                admin_data.get('role', 'Unknown'),
                admin_data.get('email', 'N/A')
            )
            
        Console().print(table)
        
    except Exception as e:
        print(f"[red]Failed to get admin info: {e}[/red]")

@admin_app.command("remove")
def admin_remove(
    server_id: int = typer.Argument(..., help="Server ID"),
    admin_id: str = typer.Argument(..., help="Admin ID to remove"),
    site_name: Optional[str] = typer.Option(None, help="Remove from specific site only"),
    exclude_sites: List[str] = typer.Option([], help="Site names to exclude from removal")
):
    """Remove an admin from UniFi sites."""
    try:
        if site_name:
            # Remove from specific site
            success = remove_admin_from_site(server_id, site_name, admin_id)
            if success:
                print(f"[green]Successfully removed admin {admin_id} from site {site_name}.[/green]")
            else:
                print(f"[red]Failed to remove admin {admin_id} from site {site_name}.[/red]")
        else:
            # Remove from all sites except excluded ones
            confirm = typer.confirm(f"Are you sure you want to remove admin {admin_id} from all sites (except {exclude_sites})?")
            if not confirm:
                raise typer.Exit()
                
            results = remove_admin_from_all_sites(server_id, admin_id, exclude_sites)
            
            print(f"[green]Admin removal completed:[/green]")
            print(f"  Total sites: {results['total_sites']}")
            print(f"  Removed from: {len(results['removed_from'])} sites")
            print(f"  Failed: {len(results['failed_sites'])} sites")
            print(f"  Skipped: {len(results['skipped_sites'])} sites")
            
            if results['removed_from']:
                print(f"\n[green]Successfully removed from:[/green]")
                for site in results['removed_from']:
                    print(f"  - {site['site_name']} ({site['site_desc']})")
                    
            if results['failed_sites']:
                print(f"\n[red]Failed to remove from:[/red]")
                for site in results['failed_sites']:
                    print(f"  - {site['site_name']} ({site['site_desc']}): {site['reason']}")
                    
            if results['skipped_sites']:
                print(f"\n[yellow]Skipped:[/yellow]")
                for site in results['skipped_sites']:
                    print(f"  - {site['site_name']} ({site['site_desc']}): {site['reason']}")
        
    except Exception as e:
        print(f"[red]Failed to remove admin: {e}[/red]")

@admin_app.command("sites")
def admin_sites(
    server_id: int = typer.Argument(..., help="Server ID"),
    admin_id: str = typer.Argument(..., help="Admin ID")
):
    """List all sites where an admin has access."""
    try:
        # Get all sites from the server
        from manifold_core.plugins.unifi.sites import get_unifi_sites
        sites = get_unifi_sites(server_id)
        
        print(f"[cyan]Checking admin {admin_id} access across {len(sites)} sites:[/cyan]")
        
        table = Table(title=f"Admin {admin_id} Site Access")
        table.add_column("Site Name", style="cyan")
        table.add_column("Site Description", style="dim")
        table.add_column("Has Access", justify="center")
        
        for site in sites:
            site_name = site.get("name", "Unknown")
            site_desc = site.get("desc", "")
            
            # Check if admin exists in this site
            try:
                site_admins = get_admins_for_site(server_id, site_name)
                has_access = any(admin.get("name") == admin_id for admin in site_admins)
                access_status = "[green]Yes[/green]" if has_access else "[red]No[/red]"
            except Exception:
                access_status = "[yellow]Error[/yellow]"
            
            table.add_row(site_name, site_desc, access_status)
            
        Console().print(table)
        
    except Exception as e:
        print(f"[red]Failed to check admin sites: {e}[/red]")

@admin_app.command("permissions")
def admin_permissions(
    admin_id: Optional[str] = typer.Option(None, help="Show permissions for specific admin ID")
):
    """List admin site permissions from the database."""
    try:
        from manifold_core.models.base import SessionLocal
        from manifold_core.plugins.unifi.models import UnifiAdmin, UnifiAdminSitePermission
        
        session = SessionLocal()
        
        if admin_id:
            # Show permissions for specific admin
            admin = session.query(UnifiAdmin).filter_by(id=admin_id).first()
            if not admin:
                print(f"[red]Admin {admin_id} not found.[/red]")
                return
                
            print(f"[cyan]Site permissions for admin: {admin.name} ({admin.email})[/cyan]")
            print(f"Super Admin: {admin.is_super}")
            
            if admin.is_super == "true":
                print("[yellow]Super admins have access to all sites.[/yellow]")
            else:
                permissions = session.query(UnifiAdminSitePermission).filter_by(admin_id=admin_id).all()
                
                if permissions:
                    table = Table(title=f"Site Permissions for {admin.name}")
                    table.add_column("Site Name", style="cyan")
                    table.add_column("Site Description", style="dim")
                    table.add_column("Role", style="green")
                    table.add_column("Permissions", style="yellow")
                    
                    for perm in permissions:
                        table.add_row(
                            perm.site_name,
                            perm.site_desc or "",
                            perm.role or "",
                            perm.permissions or ""
                        )
                    
                    Console().print(table)
                else:
                    print("[yellow]No site permissions found for this admin.[/yellow]")
        else:
            # Show all admins and their permissions
            admins = session.query(UnifiAdmin).all()
            
            table = Table(title="All Admins and Their Permissions")
            table.add_column("Name", style="cyan")
            table.add_column("Email", style="dim")
            table.add_column("Type", style="green")
            table.add_column("Site Count", justify="right")
            
            for admin in admins:
                if admin.is_super == "true":
                    admin_type = "[red]Super Admin[/red]"
                    site_count = "All"
                else:
                    admin_type = "[blue]Site Admin[/blue]"
                    site_count = str(len(admin.site_permissions))
                
                table.add_row(
                    admin.name,
                    admin.email or "",
                    admin_type,
                    site_count
                )
            
            Console().print(table)
        
        session.close()
        
    except Exception as e:
        print(f"[red]Failed to get admin permissions: {e}[/red]")

@admin_app.command("sync")
def admin_sync(
    server_id: Optional[int] = typer.Option(None, help="Sync admins from specific server only")
):
    """Sync admin users from UniFi controllers to the database."""
    try:
        print("[cyan]Starting admin sync...[/cyan]")
        
        count = sync_unifi_admins(server_id)
        
        if count > 0:
            print(f"[green]Successfully synced {count} admin(s).[/green]")
        else:
            print("[yellow]No new admins were synced.[/yellow]")
            
    except Exception as e:
        print(f"[red]Failed to sync admins: {e}[/red]")
        raise typer.Exit(1)

