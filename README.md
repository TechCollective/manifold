⚠️ Project Notice
This project is currently undergoing a major rewrite to modernize the architecture and development experience.

✅ Active Development
The active version of Manifold is now being rebuilt using modern tools:

CLI: Typer – a friendly, intuitive CLI framework built on Click.

Web Interface: Flask-based with enhancements planned to move toward FastAPI in future phases.

Database Migrations: Managed with Alembic.

The rewrite lives in the next branch. All new features (e.g. UniFi integration, device lookups, sync tools) are being built there.

🏛 Legacy Version
The original Cement-based Manifold CLI is preserved in the legacy/cement-version branch for archival and backward compatibility.



# Setup

cd /opt
git clone https://github.com/TechCollective/manifold.git
cd manifold
git checkout next


# After cloning the repo and installing dependencies
alembic upgrade head  # Applies all DB migrations

Bitwarden Secerts Plugin
If you are going to use the bitwarden secerts plugin.
wget https://github.com/bitwarden/sdk-sm/releases/download/bws-v1.0.0/bws-x86_64-unknown-linux-gnu-1.0.0.zip
unzip and put the file in /usr/local/bin
