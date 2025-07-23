"""add is_super to unifi_admins and create site permissions table

Revision ID: add_is_super_and_site_permissions
Revises: b8152d6821ce
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_super_and_site_permissions'
down_revision = 'b8152d6821ce'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_super column to unifi_admins table
    op.add_column('unifi_admins', sa.Column('is_super', sa.String(), nullable=True))
    
    # Create unifi_admin_site_permissions table
    op.create_table('unifi_admin_site_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.String(), nullable=False),
        sa.Column('site_id', sa.String(), nullable=False),
        sa.Column('site_name', sa.String(), nullable=False),
        sa.Column('site_desc', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('permissions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['unifi_admins.id'], ),
        sa.ForeignKeyConstraint(['site_id'], ['unifi_sites.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('admin_id', 'site_id', name='uq_admin_site_permission')
    )


def downgrade():
    # Drop the unifi_admin_site_permissions table
    op.drop_table('unifi_admin_site_permissions')
    
    # Remove is_super column from unifi_admins table
    op.drop_column('unifi_admins', 'is_super') 