# File: extract_files.py
import asyncio
import os
import sys
from sqlalchemy.future import select
from database import AsyncSessionLocal
from models import InvoiceLog

# Directory where extracted files will be saved
OUTPUT_DIR = "extracted_files"

async def extract_single_file(log_id: int):
    """
    Connects to the database, fetches a specific invoice log by ID, 
    and writes the stored binary content back to a file on disk.
    """
    
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    print(f"Connecting to database to fetch Log ID: {log_id}...")
    
    async with AsyncSessionLocal() as session:
        # Fetch specific log
        stmt = select(InvoiceLog).where(InvoiceLog.id == log_id)
        result = await session.execute(stmt)
        log = result.scalars().first()
        
        if not log:
            print(f"❌ Error: No invoice log found with ID {log_id}")
            return

        try:
            # Construct output path
            # We prepend ID to filename to avoid overwrites if filenames are duplicates
            safe_filename = f"{log.id}_{log.filename}"
            file_path = os.path.join(OUTPUT_DIR, safe_filename)
            
            # Write binary data to file
            with open(file_path, "wb") as f:
                f.write(log.file_content)
            
            print(f"✅ Successfully saved file to: {file_path}")
            print(f"📄 Original Filename: {log.filename}")
            print(f"📅 Created At: {log.created_at}")
            
        except Exception as e:
            print(f"❌ Failed to save file: {e}")

if __name__ == "__main__":
    try:
        # Check if ID was passed as command line argument
        if len(sys.argv) > 1:
            target_id = int(sys.argv[1])
        else:
            # Otherwise ask the user
            user_input = input("Enter the Invoice Log ID to extract: ")
            target_id = int(user_input)

        asyncio.run(extract_single_file(target_id))
        
    except ValueError:
        print("❌ Invalid ID. Please enter a numeric integer.")
    except KeyboardInterrupt:
        print("\nProcess interrupted.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")