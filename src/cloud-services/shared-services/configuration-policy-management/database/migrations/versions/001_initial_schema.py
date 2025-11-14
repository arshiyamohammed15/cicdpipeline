"""Initial schema for Configuration & Policy Management

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-01-14 00:00:00.000000

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

    # Create policies table (PRD lines 218-233)
    op.create_table(
        'policies',
        sa.Column('policy_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('policy_type', sa.String(50), nullable=False),
        sa.Column('policy_definition', JSONB, nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('scope', JSONB, nullable=False),
        sa.Column('enforcement_level', sa.String(20), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('metadata', JSONB, nullable=True),
    )

    # Create configurations table (PRD lines 236-247)
    op.create_table(
        'configurations',
        sa.Column('config_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('config_type', sa.String(50), nullable=False),
        sa.Column('config_definition', JSONB, nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('deployed_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('deployed_by', UUID(as_uuid=True), nullable=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('environment', sa.String(50), nullable=False),
    )

    # Create gold_standards table (PRD lines 250-259)
    op.create_table(
        'gold_standards',
        sa.Column('standard_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('control_definitions', JSONB, nullable=False),
        sa.Column('compliance_rules', JSONB, nullable=False),
        sa.Column('evidence_requirements', JSONB, nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
    )

    # Add constraints per PRD
    op.create_check_constraint('policies_policy_type_check', 'policies', "policy_type IN ('security', 'compliance', 'operational', 'governance')")
    op.create_check_constraint('policies_status_check', 'policies', "status IN ('draft', 'review', 'approved', 'active', 'deprecated')")
    op.create_check_constraint('policies_enforcement_level_check', 'policies', "enforcement_level IN ('advisory', 'warning', 'enforcement')")

    op.create_check_constraint('configurations_config_type_check', 'configurations', "config_type IN ('security', 'performance', 'feature', 'compliance')")
    op.create_check_constraint('configurations_status_check', 'configurations', "status IN ('draft', 'staging', 'active', 'deprecated')")
    op.create_check_constraint('configurations_environment_check', 'configurations', "environment IN ('production', 'staging', 'development')")

    op.create_check_constraint('gold_standards_framework_check', 'gold_standards', "framework IN ('soc2', 'gdpr', 'hipaa', 'nist', 'custom')")

    # Create primary indexes per PRD (lines 264-266)
    op.create_index('idx_policies_policy_id_tenant_id', 'policies', ['policy_id', 'tenant_id'])
    op.create_index('idx_configurations_config_id_env_tenant', 'configurations', ['config_id', 'environment', 'tenant_id'])
    op.create_index('idx_gold_standards_standard_id_framework_tenant', 'gold_standards', ['standard_id', 'framework', 'tenant_id'])

    # Create performance indexes per PRD (lines 268-270)
    op.create_index('idx_policies_type_status_tenant', 'policies', ['policy_type', 'status', 'tenant_id'])
    op.create_index('idx_configurations_type_status_env', 'configurations', ['config_type', 'status', 'environment'])
    op.create_index('idx_gold_standards_framework_version_tenant', 'gold_standards', ['framework', 'version', 'tenant_id'])

    # Create search indexes per PRD (lines 184-186) - GIN indexes for JSONB
    op.create_index('idx_policies_definition_gin', 'policies', ['policy_definition'], postgresql_using='gin')
    op.create_index('idx_configurations_definition_gin', 'configurations', ['config_definition'], postgresql_using='gin')
    op.create_index('idx_gold_standards_control_definitions_gin', 'gold_standards', ['control_definitions'], postgresql_using='gin')

    # Create function to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Create trigger to auto-update updated_at
    op.execute("""
        CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_policies_updated_at ON policies')

    # Drop function
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')

    # Drop indexes
    op.drop_index('idx_gold_standards_control_definitions_gin', table_name='gold_standards')
    op.drop_index('idx_configurations_definition_gin', table_name='configurations')
    op.drop_index('idx_policies_definition_gin', table_name='policies')
    op.drop_index('idx_gold_standards_framework_version_tenant', table_name='gold_standards')
    op.drop_index('idx_configurations_type_status_env', table_name='configurations')
    op.drop_index('idx_policies_type_status_tenant', table_name='policies')
    op.drop_index('idx_gold_standards_standard_id_framework_tenant', table_name='gold_standards')
    op.drop_index('idx_configurations_config_id_env_tenant', table_name='configurations')
    op.drop_index('idx_policies_policy_id_tenant_id', table_name='policies')

    # Drop constraints
    op.drop_constraint('gold_standards_framework_check', 'gold_standards', type_='check')
    op.drop_constraint('configurations_environment_check', 'configurations', type_='check')
    op.drop_constraint('configurations_status_check', 'configurations', type_='check')
    op.drop_constraint('configurations_config_type_check', 'configurations', type_='check')
    op.drop_constraint('policies_enforcement_level_check', 'policies', type_='check')
    op.drop_constraint('policies_status_check', 'policies', type_='check')
    op.drop_constraint('policies_policy_type_check', 'policies', type_='check')

    # Drop tables
    op.drop_table('gold_standards')
    op.drop_table('configurations')
    op.drop_table('policies')
