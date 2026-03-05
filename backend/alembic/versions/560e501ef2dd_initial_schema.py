"""Initial schema

Revision ID: 560e501ef2dd
Revises: 
Create Date: 2026-03-03 01:04:11.555083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '560e501ef2dd'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # races table
    op.create_table(
        'races',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('round', sa.Integer(), nullable=False),
        sa.Column('circuit_id', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('INGESTED', 'VERIFIED', 'PROCESSING', name='racestatus'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_races_id'), 'races', ['id'], unique=False)

    # race_states table
    op.create_table(
        'race_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('race_id', sa.Integer(), nullable=False),
        sa.Column('tick', sa.Integer(), nullable=False),
        sa.Column('lap', sa.Integer(), nullable=False),
        sa.Column('sc_status', sa.Enum('GREEN', 'SC', 'VSC', 'RED_FLAG', 'YELLOW', name='scstatus'), nullable=True),
        sa.Column('weather_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['race_id'], ['races.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_race_states_id'), 'race_states', ['id'], unique=False)

    # telemetry table
    op.create_table(
        'telemetry',
        sa.Column('time', sa.DateTime(), nullable=False),
        sa.Column('driver_id', sa.String(), nullable=False),
        sa.Column('race_id', sa.Integer(), nullable=False),
        sa.Column('lap', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('speed', sa.Float(), nullable=False),
        sa.Column('tire_compound', sa.String(), nullable=False),
        sa.Column('tire_wear', sa.Float(), nullable=False),
        sa.Column('win_probability', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['race_id'], ['races.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('time', 'driver_id')
    )

    # Turn telemetry table into TimescaleDB hypertable
    try:
        op.execute("SELECT create_hypertable('telemetry', 'time', if_not_exists => TRUE);")
    except Exception as e:
        # Ignore if not using TimescaleDB
        pass


def downgrade() -> None:
    op.drop_table('telemetry')
    op.drop_index(op.f('ix_race_states_id'), table_name='race_states')
    op.drop_table('race_states')
    op.drop_index(op.f('ix_races_id'), table_name='races')
    op.drop_table('races')
    op.execute("DROP TYPE scstatus;")
    op.execute("DROP TYPE racestatus;")
