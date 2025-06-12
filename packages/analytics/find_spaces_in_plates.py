import pandas as pd
import re
from vehicle_plate_cleaner import clean_license_plate

def find_plates_with_spaces_between_letters_and_numbers():
    """Find license plates with spaces between letters and numbers"""
    # Load the vehicle data
    df = pd.read_csv('extracted_vehicles.csv')
    
    # Find plates with spaces between letters and numbers
    # Pattern: one or more letters, followed by space(s), followed by one or more digits
    pattern = r'[A-Za-z]+\s+\d+'
    plates_with_spaces = df[df['license_plate'].str.contains(pattern, na=False, regex=True)]
    
    # Sort by plate for easier viewing
    plates_with_spaces = plates_with_spaces.sort_values('license_plate')
    
    # Add column with cleaned version to verify fix
    plates_with_spaces['cleaned_plate'] = plates_with_spaces['license_plate'].apply(clean_license_plate)
    
    # Print summary
    print(f"Found {len(plates_with_spaces)} plates with spaces between letters and numbers")
    print("\nSample plates with spaces between letters and numbers:")
    
    # Print a sample of 20 plates
    sample = plates_with_spaces.head(20)
    for _, row in sample.iterrows():
        original = row['license_plate']
        cleaned = row['cleaned_plate']
        print(f"Original: '{original}' → Cleaned: '{cleaned}'")
    
    # Print statistics
    unique_formats = {}
    for plate in plates_with_spaces['license_plate']:
        # Extract the basic format (e.g., "AAA 1234" becomes "L S N")
        format_code = ""
        for char in plate:
            if char.isalpha():
                format_code += "L"
            elif char.isdigit():
                format_code += "N"
            elif char.isspace():
                format_code += "S"
            else:
                format_code += char
        # Compress repeated characters (e.g., "LLLSNNNN" becomes "LSN")
        compressed = ""
        for i, char in enumerate(format_code):
            if i == 0 or char != format_code[i-1]:
                compressed += char
        if compressed not in unique_formats:
            unique_formats[compressed] = 0
        unique_formats[compressed] += 1
    
    print("\nFound plate formats with spaces:")
    for format_code, count in sorted(unique_formats.items(), key=lambda x: x[1], reverse=True):
        print(f"{format_code}: {count} plates")
    
    return plates_with_spaces

# Find and print plates with spaces between letters and numbers
if __name__ == "__main__":
    plates_df = find_plates_with_spaces_between_letters_and_numbers()
    
    # Save to CSV for further analysis if needed
    plates_df.to_csv('plates_with_spaces.csv', index=False)
    print(f"\nResults saved to 'plates_with_spaces.csv'")