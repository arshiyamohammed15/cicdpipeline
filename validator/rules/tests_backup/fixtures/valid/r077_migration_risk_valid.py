# R077: Migration Risk Valid
# This file demonstrates proper migration with backout plan

def upgrade():
    """Migration upgrade with proper rollback plan"""
    # Add new column
    db.execute("ALTER TABLE users ADD COLUMN new_field VARCHAR(255)")
    pass

def downgrade():
    """Rollback plan for migration"""
    # Remove the column
    db.execute("ALTER TABLE users DROP COLUMN new_field")
    pass

# Migration includes both upgrade and downgrade functions
# Backout plan is documented and implemented
