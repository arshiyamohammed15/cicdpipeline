"""Initial schema for Contracts & Schema Registry

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import TIMESTAMP

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # Create schemas table
    op.create_table(
        'schemas',
        sa.Column('schema_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('namespace', sa.String(255), nullable=False),
        sa.Column('schema_type', sa.String(50), nullable=False),
        sa.Column('schema_definition', JSONB, nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('compatibility', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('metadata', JSONB, nullable=True),
    )

    # Create contracts table
    op.create_table(
        'contracts',
        sa.Column('contract_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('schema_id', UUID(as_uuid=True), nullable=True),
        sa.Column('validation_rules', JSONB, nullable=False),
        sa.Column('enforcement_level', sa.String(20), nullable=False),
        sa.Column('violation_actions', JSONB, nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
    )

    # Create schema_dependencies table
    op.create_table(
        'schema_dependencies',
        sa.Column('parent_schema_id', UUID(as_uuid=True), nullable=False),
        sa.Column('child_schema_id', UUID(as_uuid=True), nullable=False),
        sa.Column('dependency_type', sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint('parent_schema_id', 'child_schema_id'),
    )

    # Create schema_analytics table
    op.create_table(
        'schema_analytics',
        sa.Column('analytics_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('schema_id', UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('period_start', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('period_end', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('metrics', JSONB, nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    # Add foreign keys
    op.create_foreign_key('fk_contracts_schema_id', 'contracts', 'schemas', ['schema_id'], ['schema_id'])
    op.create_foreign_key('fk_schema_deps_parent', 'schema_dependencies', 'schemas', ['parent_schema_id'], ['schema_id'])
    op.create_foreign_key('fk_schema_deps_child', 'schema_dependencies', 'schemas', ['child_schema_id'], ['schema_id'])
    op.create_foreign_key('fk_schema_analytics_schema', 'schema_analytics', 'schemas', ['schema_id'], ['schema_id'])

    # Add constraints
    op.create_unique_constraint('schemas_tenant_name_version_unique', 'schemas', ['tenant_id', 'name', 'version'])
    op.create_check_constraint('schemas_schema_type_check', 'schemas', "schema_type IN ('json_schema', 'avro', 'protobuf')")
    op.create_check_constraint('schemas_compatibility_check', 'schemas', "compatibility IN ('backward', 'forward', 'full', 'none')")
    op.create_check_constraint('schemas_status_check', 'schemas', "status IN ('draft', 'published', 'deprecated')")
    op.create_check_constraint('contracts_type_check', 'contracts', "type IN ('api', 'event', 'data')")
    op.create_check_constraint('contracts_enforcement_level_check', 'contracts', "enforcement_level IN ('strict', 'warning', 'advisory')")
    op.create_unique_constraint('schema_analytics_unique', 'schema_analytics', ['schema_id', 'tenant_id', 'period', 'period_start'])
    op.create_check_constraint('schema_analytics_period_check', 'schema_analytics', "period IN ('hourly', 'daily', 'weekly', 'monthly')")

    # Create indexes
    op.create_index('idx_schemas_namespace_gin', 'schemas', ['namespace'], postgresql_using='gin', postgresql_ops={'namespace': 'gin_trgm_ops'})
    op.create_index('idx_schemas_metadata_tags', 'schemas', [sa.text("(metadata->'tags')")], postgresql_using='gin')
    op.create_index('idx_schemas_type_status', 'schemas', ['schema_type', 'status'])
    op.create_index('idx_schemas_created_at_brin', 'schemas', ['created_at'], postgresql_using='brin')
    op.create_index('idx_schemas_tenant_status', 'schemas', ['tenant_id', 'status'])
    op.create_index('idx_contracts_schema_id', 'contracts', ['schema_id'])
    op.create_index('idx_contracts_tenant_id', 'contracts', ['tenant_id'])
    op.create_index('idx_contracts_type', 'contracts', ['type'])
    op.create_index('idx_contracts_created_at', 'contracts', ['created_at'])
    op.create_index('idx_schema_deps_parent', 'schema_dependencies', ['parent_schema_id'])
    op.create_index('idx_schema_deps_child', 'schema_dependencies', ['child_schema_id'])
    op.create_index('idx_schema_analytics_schema_tenant', 'schema_analytics', ['schema_id', 'tenant_id'])
    op.create_index('idx_schema_analytics_period', 'schema_analytics', ['period', 'period_start'])
    op.create_index('idx_schema_analytics_tenant_period', 'schema_analytics', ['tenant_id', 'period', 'period_start'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_schema_analytics_tenant_period', table_name='schema_analytics')
    op.drop_index('idx_schema_analytics_period', table_name='schema_analytics')
    op.drop_index('idx_schema_analytics_schema_tenant', table_name='schema_analytics')
    op.drop_index('idx_schema_deps_child', table_name='schema_dependencies')
    op.drop_index('idx_schema_deps_parent', table_name='schema_dependencies')
    op.drop_index('idx_contracts_created_at', table_name='contracts')
    op.drop_index('idx_contracts_type', table_name='contracts')
    op.drop_index('idx_contracts_tenant_id', table_name='contracts')
    op.drop_index('idx_contracts_schema_id', table_name='contracts')
    op.drop_index('idx_schemas_tenant_status', table_name='schemas')
    op.drop_index('idx_schemas_created_at_brin', table_name='schemas')
    op.drop_index('idx_schemas_type_status', table_name='schemas')
    op.drop_index('idx_schemas_metadata_tags', table_name='schemas')
    op.drop_index('idx_schemas_namespace_gin', table_name='schemas')

    # Drop tables
    op.drop_table('schema_analytics')
    op.drop_table('schema_dependencies')
    op.drop_table('contracts')
    op.drop_table('schemas')
