from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass

@dataclass
class ColumnConfig:
    """Configuration for a table column"""
    field: str
    label: str
    type: str = 'text'  # text, boolean, link, custom
    render: Optional[Callable] = None

@dataclass
class CustomAction:
    """Configuration for a custom action"""
    label: str
    onclick: str  # JavaScript function name

class IntegrationConfig:
    """Base class for integration configurations"""
    
    def __init__(self, name: str, title: str):
        self.name = name
        self.title = title
        self.columns: List[ColumnConfig] = []
        self.custom_actions: List[CustomAction] = []
    
    def add_column(self, field: str, label: str, type: str = 'text', render: Optional[Callable] = None):
        """Add a column configuration"""
        self.columns.append(ColumnConfig(field=field, label=label, type=type, render=render))
    
    def add_custom_action(self, label: str, onclick: str):
        """Add a custom action"""
        self.custom_actions.append(CustomAction(label=label, onclick=onclick))
    
    def get_template_context(self, integrations: List[Any]) -> Dict[str, Any]:
        """Get the template context for rendering"""
        return {
            'integration_name': self.name,
            'integration_title': self.title,
            'integrations': integrations,
            'columns': self.columns,
            'custom_actions': self.custom_actions
        }

# Configuration for each integration type
class AutotaskConfig(IntegrationConfig):
    def __init__(self):
        super().__init__('autotask', 'Autotask Integrations')
        self.add_column('name', 'Name')
        self.add_column('api_url', 'API URL', 'link')
        self.add_custom_action('Test Connection', 'testAutotaskConnection')
        self.add_custom_action('Sync Tickets', 'syncAutotaskTickets')

class SlackConfig(IntegrationConfig):
    def __init__(self):
        super().__init__('slack', 'Slack Integrations')
        self.add_column('name', 'Name')
        self.add_column('workspace', 'Workspace')
        self.add_custom_action('Test Connection', 'testSlackConnection')
        self.add_custom_action('List Channels', 'listSlackChannels')

class UnifiConfig(IntegrationConfig):
    def __init__(self):
        super().__init__('unifi', 'UniFi Servers')
        self.add_column('name', 'Name')
        self.add_column('host', 'Host')
        self.add_column('port', 'Port')
        self.add_custom_action('Display Sites', 'showUnifiSites')
        self.add_custom_action('Sync Devices', 'syncUnifiDevices')
        self.add_custom_action('Lookup Device', 'openUnifiLookup')

# Registry of integration configurations
INTEGRATION_CONFIGS = {
    'autotask': AutotaskConfig(),
    'slack': SlackConfig(),
    'unifi': UnifiConfig(),
}

def get_integration_config(integration_name: str) -> IntegrationConfig:
    """Get the configuration for an integration"""
    return INTEGRATION_CONFIGS.get(integration_name) 