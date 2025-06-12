import vehicle_plate_cleaner
import pandas as pd
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run the batch license plate cleaner on the real data"""
    
    # Path to the vehicles data file
    file_path = 'extracted_vehicles.csv'
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
    
    logger.info(f"Starting batch license plate cleaning for {file_path}")
    
    # Get a sample of the data for info
    sample_df = pd.read_csv(file_path, nrows=5)
    logger.info(f"Sample of input data:\n{sample_df[['vehicle_id', 'license_plate', 'company_id']].head()}")
    
    # Count total records
    total_records = len(pd.read_csv(file_path))
    logger.info(f"Total records to process: {total_records}")
    
    # Process the data
    start_time = datetime.now()
    logger.info(f"Processing started at {start_time}")
    
    # Load original data for comparison
    original_df = pd.read_csv(file_path)
    
    # Clean plates
    cleaned_df = vehicle_plate_cleaner.clean_all_plates(file_path)
    
    # Find rejected plates by comparing vehicle IDs
    original_ids = set(original_df['vehicle_id'].tolist())
    remaining_ids = set(cleaned_df['vehicle_id'].tolist())
    rejected_ids = original_ids - remaining_ids
    
    # Create a DataFrame of rejected plates for review
    rejected_df = original_df[original_df['vehicle_id'].isin(rejected_ids)]
    
    # Save the rejected plates to a separate file
    rejected_file = f"rejected_plates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    rejected_df.to_csv(rejected_file, index=False)
    logger.info(f"Rejected plates saved to: {rejected_file}")
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    logger.info(f"Processing completed at {end_time} (took {processing_time:.2f} seconds)")
    
    # Save the cleaned data with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"cleaned_vehicles_{timestamp}.csv"
    cleaned_df.to_csv(output_file, index=False)
    
    # Results
    original_count = total_records
    cleaned_count = len(cleaned_df)
    rejected_count = original_count - cleaned_count
    
    logger.info(f"Results:")
    logger.info(f"  - Original count: {original_count}")
    logger.info(f"  - Cleaned count: {cleaned_count}")
    logger.info(f"  - Rejected plates: {rejected_count} ({rejected_count/original_count*100:.2f}%)")
    logger.info(f"  - Output saved to: {output_file}")
    
    # Generate a simple report
    report_file = f"plate_cleaning_report_{timestamp}.txt"
    with open(report_file, 'w') as f:
        f.write(f"License Plate Cleaning Report\n")
        f.write(f"Generated on: {datetime.now()}\n")
        f.write(f"Input file: {file_path}\n")
        f.write(f"Output file: {output_file}\n")
        f.write(f"Rejected plates file: {rejected_file}\n\n")
        f.write(f"Results:\n")
        f.write(f"  - Original records: {original_count}\n")
        f.write(f"  - Cleaned records: {cleaned_count}\n")
        f.write(f"  - Rejected plates: {rejected_count} ({rejected_count/original_count*100:.2f}%)\n\n")
        f.write(f"Rules applied:\n")
        f.write(f"  - Plates with only numbers were rejected\n")
        f.write(f"  - Plates with only letters were rejected\n")
        f.write(f"  - All spaces were removed\n")
        f.write(f"  - Plates with decimal points had the decimal part removed\n")
        f.write(f"  - All plates were standardized to Zambian formats\n")
        f.write(f"  - Company IDs were cleared for manual association\n")
        f.write(f"  - Tare weights were cleared for automatic calculation\n")
    
    logger.info(f"Report saved to: {report_file}")
    
    # Return the cleaned data for inspection if needed
    return cleaned_df

if __name__ == "__main__":
    main()