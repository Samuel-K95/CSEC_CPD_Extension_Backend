import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

from app.models import User, Contest, RatingHistory, ContestDataSnapshot, Attendance, Rating, RefreshToken, contest_preparer_table

load_dotenv()

SQLITE_DATABASE_URL = "sqlite:///./dev.db"
POSTGRES_DATABASE_URL = os.getenv("DATABASE_URL")

if not POSTGRES_DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file or environment variables")

sqlite_engine = create_engine(SQLITE_DATABASE_URL)
postgres_engine = create_engine(POSTGRES_DATABASE_URL)

SQLiteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)
PostgresSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)

Base = declarative_base()
if hasattr(User, 'metadata'):
    Base.metadata = User.metadata

def migrate_data():
    """Reads data from SQLite and writes it to PostgreSQL."""
    sqlite_db = SQLiteSessionLocal()
    postgres_db = PostgresSessionLocal()

    models_to_migrate = [User, Contest, Rating, RatingHistory, ContestDataSnapshot, Attendance, RefreshToken]

    try:
        print("Starting data migration...")
        for model in models_to_migrate:
            table_name = model.__tablename__
            print(f"Migrating table: {table_name}...")
            records = sqlite_db.query(model).all()
            if not records:
                print(f"  No records found in {table_name}. Skipping.")
                continue
            postgres_db.bulk_insert_mappings(model, [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in records])
            print(f"  Migrated {len(records)} records to {table_name}.")

        print("Migrating table: contest_preparer_link...")
        preparer_links = sqlite_db.execute(text("SELECT contest_id, user_id, can_take_attendance FROM contest_preparer_link")).fetchall()
        if preparer_links:
            for link in preparer_links:
                insert_stmt = contest_preparer_table.insert().values(contest_id=link[0], user_id=link[1], can_take_attendance=link[2])
                postgres_db.execute(insert_stmt)
            print(f"  Migrated {len(preparer_links)} records to contest_preparer_link.")
        else:
            print("  No records found in contest_preparer_link. Skipping.")

        print("Committing changes to PostgreSQL...")
        postgres_db.commit()
        print("Data migration completed successfully!")
    except Exception as e:
        print(f"An error occurred during data migration: {e}")
        print("Rolling back changes...")
        postgres_db.rollback()
        raise
    finally:
        sqlite_db.close()
        postgres_db.close()

def sync_sequences():
    """Synchronizes PostgreSQL sequences after data migration."""
    postgres_db = PostgresSessionLocal()
    try:
        print("\nStarting sequence synchronization...")
        inspector = inspect(postgres_db.bind)
        tables_with_sequences = [
            'users', 'rating_history', 'refresh_tokens', 'contest_data_snapshots'
        ]
        
        for table_name in tables_with_sequences:
            try:
                sequence_name = f"{table_name}_id_seq"
                print(f"  Syncing sequence for table: {table_name}...")
                
                max_id_result = postgres_db.execute(text(f'SELECT MAX(id) FROM "{table_name}"')).scalar()
                max_id = max_id_result if max_id_result is not None else 0
                
                postgres_db.execute(text(f"SELECT setval('{sequence_name}', {max_id + 1}, false);"))
                print(f"    Sequence '{sequence_name}' reset to start at {max_id + 1}.")

            except Exception as table_e:
                print(f"    Could not sync sequence for table {table_name}: {table_e}")

        postgres_db.commit()
        print("Sequence synchronization completed successfully!")
    except Exception as e:
        print(f"An error occurred during sequence synchronization: {e}")
        postgres_db.rollback()
        raise
    finally:
        postgres_db.close()

if __name__ == "__main__":
    try:
        print("Dropping all existing tables in PostgreSQL...")
        with postgres_engine.connect() as connection:
            with connection.begin():
                connection.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        print("Tables dropped.")

        print("Creating tables in PostgreSQL...")
        Base.metadata.create_all(bind=postgres_engine)
        print("Tables created.")

        migrate_data()

        sync_sequences()

        print("\n--- MIGRATION PROCESS COMPLETED ---")

    except Exception as e:
        print(f"\n--- MIGRATION FAILED ---")
        print(f"An overall error occurred: {e}")
    finally:
        print("Database sessions closed.")