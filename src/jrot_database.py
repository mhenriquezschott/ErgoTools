from schema_migrations import migrate_database


JROT_TABLES = ("Job", "JobMeasurement", "RotationScheme", "RotationAssignment")


def ensure_jrot_schema(database_path):
    """Bring an ErgoTools project to the current versioned database schema."""
    if not database_path:
        raise ValueError("A project database path is required.")
    return migrate_database(database_path)
