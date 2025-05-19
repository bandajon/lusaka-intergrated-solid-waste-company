import pandas as pd
from vehicle_plate_cleaner import run_license_plate_cleaner, batch_clean_plates, clean_license_plate

# For batch cleaning without interactive review
def clean_all_plates_batch():
    """Clean all plates using the batch method"""
    print("Cleaning all license plates in batch mode...")
    
    # Load the original dataframe
    original_df = pd.read_csv('extracted_vehicles.csv')
    total_plates = len(original_df)
    
    # Apply the plate cleaning
    cleaned_df = batch_clean_plates('extracted_vehicles.csv')
    
    # Count statistics
    numeric_only_count = original_df[original_df['license_plate'].str.match(r'^\s*\d+\s*$', na=False)].shape[0]
    decimal_plates = original_df[original_df['license_plate'].str.contains(r'\.', na=False)].shape[0]
    plates_with_spaces = original_df[original_df['license_plate'].str.contains(r'\s', na=False)].shape[0]
    
    # Count how many plates were changed
    original_df['temp_cleaned'] = original_df['license_plate'].apply(clean_license_plate)
    changed_plates = original_df[original_df['license_plate'] != original_df['temp_cleaned']].shape[0]
    rejected_plates = original_df[original_df['temp_cleaned'] == ''].shape[0]
    
    # Print statistics
    print("\nCleaning Statistics:")
    print(f"Total license plates: {total_plates}")
    print(f"Plates containing spaces: {plates_with_spaces} ({plates_with_spaces/total_plates*100:.1f}%)")
    print(f"Plates containing decimals: {decimal_plates} ({decimal_plates/total_plates*100:.1f}%)")
    print(f"Plates with only numbers: {numeric_only_count} ({numeric_only_count/total_plates*100:.1f}%)")
    print(f"Plates modified during cleaning: {changed_plates} ({changed_plates/total_plates*100:.1f}%)")
    print(f"Plates rejected as invalid: {rejected_plates} ({rejected_plates/total_plates*100:.1f}%)")
    
    return cleaned_df

# For interactive deduplication 
def clean_plates_interactive():
    """Run the interactive license plate cleaner and deduplicator"""
    print("Starting interactive license plate cleaner...")
    reviewer = run_license_plate_cleaner('extracted_vehicles.csv')
    print("Use the UI to review and merge duplicate plates")
    return reviewer

# Sample usage to test cleaning on a single plate
def test_plate_cleaner():
    """Test the license plate cleaner on a few examples"""
    test_plates = [
        # Regular plates
        "ABG 6138",
        "GRZ-680DA",
        "GRZ 12",
        "CA231",
        "MUMBA",
        
        # Problem plates that should be rejected or fixed
        "22",            # Only numbers - should be rejected
        "30",            # Only numbers - should be rejected
        "713",           # Only numbers - should be rejected
        "BAD 52.00",     # Decimal value - should remove decimal part
        "ALK 55.00",     # Decimal value - should remove decimal part
        "BAD 204.00",    # Decimal value - should remove decimal part
        "BAD 274.00",    # Decimal value - should remove decimal part
        "BAD 452.00",    # Decimal value - should remove decimal part
        "BAD 615.00",    # Decimal value - should remove decimal part
        "BAD 829.00",    # Decimal value - should remove decimal part
        "BAD 932.00",    # Decimal value - should remove decimal part
        "BAD 941.00",    # Decimal value - should remove decimal part
        
        # Other formatting challenges
        "a b c 1 2 3 4", # Spaces in letters and numbers
        "AB.12.34",      # Dots between characters
        "XYZ-999"        # Hyphen between letters and numbers
    ]
    
    print("Testing plate cleaning:")
    print("=" * 50)
    print("| Original         | Cleaned          | Status   |")
    print("|------------------|------------------|----------|")
    for plate in test_plates:
        cleaned = clean_license_plate(plate)
        status = "✓ Valid" if cleaned else "✗ Rejected"
        print(f"| {plate:<16} | {cleaned:<16} | {status:<8} |")
    print("=" * 50)

# Run the test function
if __name__ == "__main__":
    print("Zambian License Plate Cleaning and Deduplication Tool")
    print("=" * 50)
    print("1. To run batch cleaning (non-interactive):")
    print("   df = clean_all_plates_batch()")
    print()
    print("2. To run interactive cleaning and deduplication:")
    print("   reviewer = clean_plates_interactive()")
    print()
    print("3. To test cleaning on sample plates:")
    print("   test_plate_cleaner()")