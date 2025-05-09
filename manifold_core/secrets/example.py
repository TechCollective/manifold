from manifold_core.secrets.base import SecretBackend

class Backend(SecretBackend):
    def get_secret(self, key: str) -> str:
        """
        Required method for all secret backends.

        Args:
            key (str): The name of the secret to retrieve.

        Returns:
            str: The secret value.

        Raises:
            KeyError: If the secret is not found.
        """
        # Replace this with your logic (e.g. call to Vault, AWS, etc.)
        if key == "EXAMPLE_SECRET":
            return "example-value"
        raise KeyError(f"Secret '{key}' not found in example backend")
