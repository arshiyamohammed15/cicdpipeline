# R077: Migration Risk Violation
# This file demonstrates a migration without proper backout plan

def upgrade():
    """Migration upgrade without rollback plan"""
    # Add new column
    db.execute("ALTER TABLE users ADD COLUMN new_field VARCHAR(255)")
    # No downgrade function or rollback plan
    pass

# Missing downgrade function and rollback strategy
