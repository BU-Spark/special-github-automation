"""Add unique constraint to IngestUserProjectCSV

Revision ID: b0a85b0a1488
Revises: 
Create Date: 2024-12-17 20:53:17.286467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b0a85b0a1488'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the unique constraint
    op.create_unique_constraint(
        'unique_project_email',
        'ingest_user_project_csv',
        ['project_name', 'project_tag', 'first_name', 'last_name', 'email', 'buid', 'github_username']
    )

def downgrade() -> None:
    # Remove the unique constraint
    op.drop_constraint('unique_project_email', 'ingest_user_project_csv', type_='unique')