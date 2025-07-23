from abc import ABC, abstractmethod

class SecretBackend(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> str:
        """Retrieve a secret by name. Should raise KeyError if not found."""
        pass
    
    @abstractmethod
    def has_secret(self, key: str) -> bool:
        """Check if a secret exists without retrieving its value."""
        pass
