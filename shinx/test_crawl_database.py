#!/usr/bin/env python3
"""Test script to crawl the entire database and save metadata to a JSON file."""

import json
from shinx.adapters.postgres_adapter import PostgresAdapter
from shinx.shared.models.db_metadata import DBMetadata

def main():
    # Connect to the database
    adapter = PostgresAdapter(
        host="localhost",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="postgres"
    )

    try:
        # Crawl the database
        print("Crawling database...")
        metadata = adapter.get_database_structure()
        
        # Print summary
        print(f"\nDatabase Version: {metadata.version}")
        print(f"Number of Extensions: {len(metadata.extensions)}")
        print(f"Number of Tables: {len(metadata.tables)}")
        print(f"Number of Views: {len(metadata.views)}")
        
        # Print table summary
        print("\nTables:")
        for table in metadata.tables:
            print(f"  - {table.schema_name}.{table.name} ({len(table.columns)} columns, {len(table.constraints)} constraints, {len(table.indexes)} indexes)")
        
        # Print view summary
        print("\nViews:")
        for view in metadata.views:
            print(f"  - {view.schema_name}.{view.name} ({len(view.columns)} columns)")
        
        # Save to JSON file
        output_file = "/home/suub/IdeaProjects/shinx_suub/docs/sample_outputs/sample_db_crawling_output.json"
        with open(output_file, 'w') as f:
            json.dump(metadata.model_dump(), f, indent=2)
        
        print(f"\n{'=' * 80}")
        print(f"Full metadata saved to: {output_file}")
        print("=" * 80)
        
    finally:
        adapter.close()

if __name__ == "__main__":
    main()
