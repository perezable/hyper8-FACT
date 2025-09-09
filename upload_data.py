#!/usr/bin/env python3
"""
FACT System Data Upload CLI

Command-line interface for uploading custom data to the FACT system.
"""

import asyncio
import sys
import os
import argparse
import json
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_upload import DataUploader
from src.core.config import get_config


async def upload_from_file(file_path: str, data_type: str, clear_existing: bool = False):
    """Upload data from file."""
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        return False
    
    try:
        uploader = DataUploader()
        
        print(f"📂 Loading data from: {file_path}")
        print(f"📊 Data type: {data_type}")
        print(f"🗑️ Clear existing: {clear_existing}")
        
        if file_path.lower().endswith('.csv'):
            result = await uploader.load_from_csv(file_path, data_type, clear_existing)
        elif file_path.lower().endswith('.json'):
            result = await uploader.load_from_json(file_path, data_type, clear_existing)
        else:
            print("❌ Error: File must be CSV or JSON format")
            return False
        
        records_count = result.get("companies_uploaded", result.get("records_uploaded", 0))
        print(f"✅ Success: Uploaded {records_count} records")
        print(f"⏰ Timestamp: {result['timestamp']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def upload_json_data(json_data: str, data_type: str, clear_existing: bool = False):
    """Upload data from JSON string."""
    try:
        data = json.loads(json_data)
        if not isinstance(data, list):
            print("❌ Error: JSON must be an array of objects")
            return False
        
        uploader = DataUploader()
        
        print(f"📊 Data type: {data_type}")
        print(f"📝 Records to upload: {len(data)}")
        print(f"🗑️ Clear existing: {clear_existing}")
        
        if data_type == "companies":
            result = await uploader.upload_companies(data, clear_existing)
        elif data_type == "financial_records":
            result = await uploader.upload_financial_records(data, clear_existing)
        else:
            print("❌ Error: Invalid data_type. Must be 'companies' or 'financial_records'")
            return False
        
        records_count = result.get("companies_uploaded", result.get("records_uploaded", 0))
        print(f"✅ Success: Uploaded {records_count} records")
        print(f"⏰ Timestamp: {result['timestamp']}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def clear_data(data_type: str):
    """Clear existing data."""
    try:
        uploader = DataUploader()
        
        print(f"🗑️ Clearing {data_type} data...")
        
        if data_type == "all":
            await uploader.clear_existing_data("financial_records")
            await uploader.clear_existing_data("financial_data")
            await uploader.clear_existing_data("companies")
            print("✅ All data cleared successfully")
        else:
            await uploader.clear_existing_data(data_type)
            if data_type == "financial_records":
                await uploader.clear_existing_data("financial_data")
            print(f"✅ {data_type} data cleared successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def show_template(data_type: str):
    """Show data upload template."""
    try:
        uploader = DataUploader()
        template = await uploader.get_upload_template(data_type)
        
        print(f"\n📋 {template['description']}")
        print(f"\n📝 Required fields: {', '.join(template['required_fields'])}")
        
        if template['optional_fields']:
            print(f"📝 Optional fields: {', '.join(template['optional_fields'])}")
        
        print(f"\n📄 Example data:")
        print(json.dumps(template['example_data'], indent=2))
        
        print(f"\n📖 Field descriptions:")
        for field, description in template['field_descriptions'].items():
            print(f"  • {field}: {description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def create_example_files():
    """Create example CSV and JSON files."""
    try:
        # Create examples directory
        examples_dir = Path("examples")
        examples_dir.mkdir(exist_ok=True)
        
        # Example companies CSV
        companies_csv = """name,symbol,sector,founded_year,employees,market_cap
Acme Corp,ACME,Technology,2000,5000,1000000000.0
Global Finance,GFIN,Financial Services,1995,15000,5000000000.0
Health Solutions,HLTH,Healthcare,2010,3000,750000000.0"""
        
        with open(examples_dir / "companies_example.csv", "w") as f:
            f.write(companies_csv)
        
        # Example financial records CSV
        financial_csv = """company_id,quarter,year,revenue,profit,expenses
1,Q1,2025,1000000000.0,200000000.0,800000000.0
1,Q2,2025,1100000000.0,220000000.0,880000000.0
2,Q1,2025,500000000.0,50000000.0,450000000.0"""
        
        with open(examples_dir / "financial_records_example.csv", "w") as f:
            f.write(financial_csv)
        
        # Example companies JSON
        companies_json = [
            {
                "name": "Example Tech Inc",
                "symbol": "TECH",
                "sector": "Technology",
                "founded_year": 2005,
                "employees": 10000,
                "market_cap": 2500000000.0
            },
            {
                "name": "Retail Giant",
                "symbol": "RTLG",
                "sector": "Retail",
                "founded_year": 1980,
                "employees": 50000,
                "market_cap": 8000000000.0
            }
        ]
        
        with open(examples_dir / "companies_example.json", "w") as f:
            json.dump(companies_json, f, indent=2)
        
        # Example financial records JSON
        financial_json = [
            {
                "company_id": 1,
                "quarter": "Q1",
                "year": 2025,
                "revenue": 2000000000.0,
                "profit": 400000000.0,
                "expenses": 1600000000.0
            },
            {
                "company_id": 2,
                "quarter": "Q1", 
                "year": 2025,
                "revenue": 800000000.0,
                "profit": 120000000.0,
                "expenses": 680000000.0
            }
        ]
        
        with open(examples_dir / "financial_records_example.json", "w") as f:
            json.dump(financial_json, f, indent=2)
        
        print("✅ Example files created in 'examples/' directory:")
        print("  • companies_example.csv")
        print("  • companies_example.json") 
        print("  • financial_records_example.csv")
        print("  • financial_records_example.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating examples: {e}")
        return False


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="FACT System Data Upload CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload companies from CSV file (replace existing data)
  python upload_data.py --file companies.csv --type companies --clear
  
  # Upload financial records from JSON file (append to existing data)
  python upload_data.py --file financial.json --type financial_records
  
  # Upload data from JSON string
  python upload_data.py --json '[{"name":"Test","symbol":"TEST","sector":"Tech"}]' --type companies
  
  # Show data template
  python upload_data.py --template companies
  
  # Clear all existing data
  python upload_data.py --clear-data all
  
  # Create example files
  python upload_data.py --create-examples
        """
    )
    
    # File upload options
    parser.add_argument("--file", type=str, help="Path to CSV or JSON file")
    parser.add_argument("--json", type=str, help="JSON data string")
    parser.add_argument("--type", choices=["companies", "financial_records"], 
                       help="Type of data to upload")
    parser.add_argument("--clear", action="store_true", 
                       help="Clear existing data before upload")
    
    # Utility options
    parser.add_argument("--template", choices=["companies", "financial_records"],
                       help="Show data template and examples")
    parser.add_argument("--clear-data", choices=["companies", "financial_records", "all"],
                       help="Clear existing data")
    parser.add_argument("--create-examples", action="store_true",
                       help="Create example CSV and JSON files")
    
    args = parser.parse_args()
    
    # Handle utility commands
    if args.create_examples:
        success = create_example_files()
        sys.exit(0 if success else 1)
    
    if args.template:
        success = await show_template(args.template)
        sys.exit(0 if success else 1)
    
    if args.clear_data:
        success = await clear_data(args.clear_data)
        sys.exit(0 if success else 1)
    
    # Handle data upload
    if args.file and args.type:
        success = await upload_from_file(args.file, args.type, args.clear)
        sys.exit(0 if success else 1)
    
    if args.json and args.type:
        success = await upload_json_data(args.json, args.type, args.clear)
        sys.exit(0 if success else 1)
    
    # No valid command provided
    print("❌ Error: Please specify a valid command")
    print("Use --help for usage information")
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)