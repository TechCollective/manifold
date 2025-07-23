"""remove role column from unifi_admins

Revision ID: remove_role_from_unifi_admins
Revises: add_is_super_and_site_permissions
Create Date: 2024-12-19 10:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_role_from_unifi_admins'
down_revision = 'add_is_super_and_site_permissions'
branch_labels = None
depends_on = None


def upgrade():
    # Remove role column from unifi_admins table
    op.drop_column('unifi_admins', 'role')


def downgrade():
    # Add role column back to unifi_admins table
    op.add_column('unifi_admins', sa.Column('role', sa.String(), nullable=True)) 