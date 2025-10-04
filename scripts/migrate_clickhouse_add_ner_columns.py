"""
Migration script to add companies and people columns to existing ClickHouse table.
Run this ONLY if you have existing data and need to add NER columns.

For fresh installations, the table will be created with these columns automatically.
"""
import clickhouse_connect
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.config import get_settings
from src.core.logging_config import log

def migrate_add_ner_columns():
    """Add companies and people columns to news_articles table"""
    settings = get_settings()
    
    try:
        # Connect to ClickHouse
        client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_db,
        )
        
        log.info("Connected to ClickHouse")
        
        # Check if columns already exist
        check_query = """
        SELECT name FROM system.columns 
        WHERE database = 'radar_clickhouse' 
        AND table = 'news_articles' 
        AND name IN ('companies', 'people')
        """
        result = client.query(check_query)
        existing_columns = [row[0] for row in result.result_rows]
        
        if 'companies' in existing_columns and 'people' in existing_columns:
            log.info("✅ Columns 'companies' and 'people' already exist. No migration needed.")
            return
        
        # Add companies column if it doesn't exist
        if 'companies' not in existing_columns:
            log.info("Adding 'companies' column...")
            client.command("""
                ALTER TABLE news_articles 
                ADD COLUMN IF NOT EXISTS companies String DEFAULT ''
            """)
            log.info("✅ Added 'companies' column")
        
        # Add people column if it doesn't exist
        if 'people' not in existing_columns:
            log.info("Adding 'people' column...")
            client.command("""
                ALTER TABLE news_articles 
                ADD COLUMN IF NOT EXISTS people String DEFAULT ''
            """)
            log.info("✅ Added 'people' column")
        
        log.info("🎉 Migration completed successfully!")
        
        # Show table structure
        log.info("\nCurrent table structure:")
        describe_result = client.query("DESCRIBE TABLE news_articles")
        for row in describe_result.result_rows:
            print(f"  {row[0]}: {row[1]}")
        
        client.close()
        
    except Exception as e:
        log.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    log.info("Starting ClickHouse migration: Add NER columns")
    migrate_add_ner_columns()

