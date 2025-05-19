import pandas as pd
import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_license_plate(plate):
    """Clean and standardize vehicle license plates according to Zambian standards
    
    Rules applied:
    1. Convert to string and remove ALL spaces immediately
    2. Convert to uppercase
    3. Remove special characters, dashes, etc.
    4. Ensure proper format for common patterns (GRZ, ABC1234, etc.)
    5. Handle special cases (CD for diplomatic, ZP for police, etc.)
    6. Strip decimal parts from plates with decimal points
    7. Reject plates that are only numbers
    """
    if not plate or pd.isna(plate):
        return ""
    
    # Convert to string and IMMEDIATELY remove all spaces
    plate = str(plate).replace(' ', '').strip().upper()
    
    # Check if the plate contains only digits or only letters (after stripping)
    if re.match(r'^\d+$', plate) or re.match(r'^\d+\.\d+$', plate):
        return ""  # Return empty string for plates that are just numbers
    
    if re.match(r'^[A-Z]+$', plate):
        return ""  # Return empty string for plates that are just letters
    
    # Handle plates with decimal points (like "BAD52.00")
    if '.' in plate:
        # Extract the part before the decimal
        parts = plate.split('.')
        plate = parts[0]
    
    # Remove dots, commas, slashes, etc.
    plate = re.sub(r'[^\w\-]', '', plate)
    
    # Remove underscores
    plate = plate.replace('_', '')
    
    # Format GRZ plates (government vehicles)
    if plate.startswith('GRZ'):
        # Just keep GRZ followed by the digits, no spaces or dashes
        grz_match = re.match(r'GRZ[-\s]*(\d+[A-Z]*)', plate)
        if grz_match:
            plate = f"GRZ{grz_match.group(1)}"
        # For cases with just GRZ, keep it as is
    
    # Try to extract letters and numbers wherever they appear
    # Look for different letter-number patterns
    
    # First try standard format of 2-3 letters followed by 3-4 digits
    std_match = re.match(r'([A-Z]{2,3})[-\s]*(\d{3,4})', plate)
    
    # If no match, try a more general pattern for any letters followed by any numbers
    if not std_match:
        std_match = re.match(r'([A-Z]+)[-\s]*(\d+)', plate)
    
    if std_match:
        letters = std_match.group(1)
        numbers = std_match.group(2)
        
        # Make sure we have 3 letters
        if len(letters) < 3:
            # Add leading letters as needed
            letters = 'A' * (3 - len(letters)) + letters
        elif len(letters) > 3:
            # Truncate to 3 letters if longer
            letters = letters[:3]
        
        # Make sure we have 4 digits
        if len(numbers) < 4:
            # Add leading zeros as needed
            numbers = '0' * (4 - len(numbers)) + numbers
        elif len(numbers) > 4:
            # Truncate to 4 digits if longer
            numbers = numbers[:4]
            
        plate = f"{letters}{numbers}"
    
    # Final check - don't return plates that are too short
    if len(plate) < 3:
        return ""
    
    # Return the cleaned plate
    return plate

def batch_clean_plates(file_path):
    """Clean all license plates in a CSV file"""
    logger.info(f"Batch cleaning license plates from {file_path}")
    df = pd.read_csv(file_path)
    
    # Check for license_plate column
    if 'license_plate' not in df.columns:
        logger.error("CSV file does not have a license_plate column")
        raise ValueError("CSV file must have a license_plate column")
    
    # Apply plate cleaning function
    df['cleaned_plate'] = df['license_plate'].apply(clean_license_plate)
    
    # Count before filtering
    total_count = len(df)
    
    # Identify rejected plates (empty cleaned_plate)
    rejected_plates = df[df['cleaned_plate'] == '']
    rejected_count = len(rejected_plates)
    
    if rejected_count > 0:
        logger.info(f"Rejected {rejected_count} plates (empty/invalid/numeric-only)")
        
        # Save rejected plates to a separate file for reference
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rejected_file = f"rejected_plates_{timestamp}.csv"
        rejected_plates.to_csv(rejected_file, index=False)
        logger.info(f"Saved rejected plates to {rejected_file}")
    
    # Remove rows with empty cleaned_plate (rejected plates)
    df_valid = df[df['cleaned_plate'] != '']
    
    # Count standardized formats
    standard_formats = {
        'GRZ': df_valid['cleaned_plate'].str.startswith('GRZ').sum(),
        'AAA####': len(df_valid[df_valid['cleaned_plate'].str.match(r'^[A-Z]{3}\d{4}$')]),
        'Special': len(df_valid) - \
                 df_valid['cleaned_plate'].str.startswith('GRZ').sum() - \
                 len(df_valid[df_valid['cleaned_plate'].str.match(r'^[A-Z]{3}\d{4}$')])
    }
    
    logger.info(f"License plate formats after cleaning:")
    for format_type, count in standard_formats.items():
        logger.info(f"  - {format_type}: {count} vehicles")
    
    # Update the actual license_plate field with the cleaned version
    df_valid['license_plate'] = df_valid['cleaned_plate']
    
    # Drop the cleaned_plate column to maintain the same schema as the input
    df_valid = df_valid.drop(columns=['cleaned_plate'])
    
    # Show success message
    logger.info(f"Successfully cleaned {len(df_valid)}/{total_count} license plates")
    
    return df_valid

def analyze_plates(df):
    """Analyze a dataframe with license plates for potential issues"""
    if 'license_plate' not in df.columns:
        return {"error": "No license_plate column found"}
    
    # Apply cleaning to get standardized plates
    df['cleaned_plate'] = df['license_plate'].apply(clean_license_plate)
    
    # Count total plates
    total_plates = len(df)
    
    # Count valid plates (non-empty after cleaning)
    valid_plates = df['cleaned_plate'].replace('', pd.NA).count()
    
    # Count invalid plates
    invalid_plates = total_plates - valid_plates
    
    # Count duplicate plates after cleaning
    duplicates = df[df['cleaned_plate'] != ''].duplicated(subset=['cleaned_plate'], keep=False)
    duplicate_count = duplicates.sum()
    
    # Group duplicates
    if duplicate_count > 0:
        duplicate_groups = df[duplicates].groupby('cleaned_plate').size().reset_index(name='count')
        duplicate_groups = duplicate_groups.sort_values('count', ascending=False)
        top_duplicates = duplicate_groups.head(10).to_dict('records')
    else:
        top_duplicates = []
    
    # Count format types
    format_types = {
        'Standard (AAA####)': len(df[df['cleaned_plate'].str.match(r'^[A-Z]{3}\d{4}$', na=False)]),
        'GRZ': len(df[df['cleaned_plate'].str.startswith('GRZ', na=False)]),
        'Invalid/Empty': invalid_plates,
        'Other': valid_plates - \
                len(df[df['cleaned_plate'].str.match(r'^[A-Z]{3}\d{4}$', na=False)]) - \
                len(df[df['cleaned_plate'].str.startswith('GRZ', na=False)])
    }
    
    # Return analysis results
    return {
        "total_plates": total_plates,
        "valid_plates": valid_plates,
        "invalid_plates": invalid_plates,
        "duplicate_plates": duplicate_count,
        "format_types": format_types,
        "top_duplicates": top_duplicates
    }