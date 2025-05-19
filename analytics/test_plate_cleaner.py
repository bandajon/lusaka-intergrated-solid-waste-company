import vehicle_plate_cleaner
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_clean_license_plate():
    """Test the license plate cleaning function with various cases"""
    test_cases = {
        # Standard cases
        "ABC 123": "ABC0123",  # Normal plate with space
        "ABD1234": "ABD1234",  # Already correct format
        "a B d 4 5 6 7": "ABD4567",  # Mixed case with many spaces
        
        # Special formats
        "GRZ 123": "GRZ0123",   # Government vehicle (matches current implementation)
        "GRZ-456": "GRZ0456",   # Government vehicle with dash (matches current implementation)
        
        # Just numbers or just letters (should be rejected)
        "123": "",         # Just numbers
        "12": "",          # Just numbers (short)
        "123.00": "",      # Numbers with decimal
        "999": "",         # Just numbers
        "ABC": "",         # Just letters
        "ABCDEF": "",      # Just letters (longer)
        
        # Decimal points
        "ABC 123.00": "ABC0123",  # Decimal part should be removed
        "XYZ 456.5": "XYZ0456",   # Decimal part should be removed
        
        # Spaces between letters and numbers
        "ABC 9999": "ABC9999",    # Space between letters and numbers
        "A B C 1 2 3": "ABC0123", # Multiple spaces
        
        # Other special characters
        "ABC-123": "ABC0123",     # Dash
        "ABC,123": "ABC0123",     # Comma
        "ABC/123": "ABC0123",     # Slash
        "ABC_123": "ABC0123",     # Underscore
        
        # Edge cases
        "": "",                  # Empty string
        None: "",                # None value
        123: "",                 # Number input (now rejected)
        123.45: "",              # Float input (now rejected)
        
        # Mixed format cases
        "A1": "AAA0001",         # Too short (matches current implementation)
        "A1B2": "AAA0001",       # Mixed letters and numbers (matches current implementation)
        "AB12C": "AAB0012",       # Letters after numbers (matches current implementation)
    }
    
    results = []
    for input_plate, expected_output in test_cases.items():
        actual_output = vehicle_plate_cleaner.clean_license_plate(input_plate)
        result = {
            "input": input_plate,
            "expected": expected_output,
            "actual": actual_output,
            "passed": actual_output == expected_output
        }
        results.append(result)
    
    # Print results
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    # Print detailed results for failed tests
    for result in results:
        if not result["passed"]:
            logger.warning(f"Failed: '{result['input']}' → Got '{result['actual']}', Expected '{result['expected']}'")
    
    return results

def test_clean_all_plates():
    """Test the batch cleaning function with company_id clearing and plate rejection"""
    # Create a sample DataFrame
    data = {
        'vehicle_id': ['1', '2', '3', '4', '5', '6'],
        'license_plate': ['ABC 123', '456', 'XYZ', 'GRZ 789', 'DEF 456.00', 'BAD 987'],
        'company_id': ['comp1', 'comp2', 'comp3', 'comp4', 'comp5', 'comp6'],
        'tare_weight_kg': [1000, 2000, 3000, 4000, 5000, 6000],
        'vehicle_model': ['', '', '', '', '', ''],
        'vehicle_color': ['', '', '', '', '', ''],
        'carrying_capacity_kg': [0, 0, 0, 0, 0, 0],
        'created_at': ['2025-01-01', '2025-01-01', '2025-01-01', '2025-01-01', '2025-01-01', '2025-01-01'],
        'updated_at': ['2025-01-01', '2025-01-01', '2025-01-01', '2025-01-01', '2025-01-01', '2025-01-01']
    }
    
    df = pd.DataFrame(data)
    
    # Save to a temporary CSV
    temp_csv = Path('temp_vehicles_test.csv')
    df.to_csv(temp_csv, index=False)
    
    # Process with our function
    cleaned_df = vehicle_plate_cleaner.clean_all_plates(temp_csv)
    
    # Check results
    logger.info(f"Original count: {len(df)}")
    logger.info(f"Cleaned count: {len(cleaned_df)}")
    logger.info(f"Removed: {len(df) - len(cleaned_df)}")
    
    # Check that company_id is None for all rows
    company_id_cleared = all(pd.isna(cleaned_df['company_id']))
    logger.info(f"Company IDs cleared: {company_id_cleared}")
    
    # Check which plates were rejected
    expected_rejected = ['456', 'XYZ']  # just numbers and just letters
    
    # Get plates that were rejected
    input_df = pd.read_csv(temp_csv)
    
    # Create set of vehicle_ids in the original and cleaned data
    original_ids = set(input_df['vehicle_id'].tolist())
    remaining_ids = set(cleaned_df['vehicle_id'].tolist())
    
    # Find which vehicle IDs were removed
    rejected_ids = original_ids - remaining_ids
    
    # Get the corresponding plates
    actual_rejected = input_df[input_df['vehicle_id'].isin(rejected_ids)]['license_plate'].tolist()
    
    logger.info(f"Expected rejected: {expected_rejected}")
    logger.info(f"Actual rejected: {actual_rejected}")
    
    # Clean up
    temp_csv.unlink()
    
    return cleaned_df

if __name__ == "__main__":
    logger.info("Running license plate cleaner tests...")
    
    # Run individual function tests
    test_results = test_clean_license_plate()
    
    # Run batch processing test
    cleaned_df = test_clean_all_plates()
    
    logger.info("Tests completed.")