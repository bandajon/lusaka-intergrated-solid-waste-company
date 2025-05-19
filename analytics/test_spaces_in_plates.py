import pandas as pd
from vehicle_plate_cleaner import clean_license_plate

# Test various space-related issues in license plates
def test_space_handling():
    test_plates = [
        # Plates with spaces in various positions
        " ABC123",          # Space at beginning
        "ABC 123",          # Space between letters and numbers
        "A B C 1 2 3",      # Spaces between all characters
        "  ABC  123  ",     # Multiple spaces before, between, and after
        
        # Plates with both spaces and decimals
        "BAD 52.00",        # Space and decimal
        " ALK 55.00 ",      # Spaces at beginning/end plus decimal
        "B A D 2 0 4.0 0",  # Spaces everywhere plus decimal
        
        # Other problematic formats
        "22",               # Just numbers - should be rejected
        " 30 ",             # Just numbers with spaces - should be rejected
        "G R Z 1 2 3",      # GRZ with spaces
        "   XYZ   ",        # Just letters with spaces
    ]
    
    print("Testing space handling in license plates:")
    print("=" * 65)
    print("| {:<20} | {:<20} | {:<20} |".format("Original", "Cleaned", "Status"))
    print("|" + "-"*22 + "|" + "-"*22 + "|" + "-"*22 + "|")
    
    for plate in test_plates:
        cleaned = clean_license_plate(plate)
        status = "✓ Valid" if cleaned else "✗ Rejected"
        print("| {:<20} | {:<20} | {:<20} |".format(plate, cleaned, status))
    
    print("=" * 65)

# Run the test
if __name__ == "__main__":
    test_space_handling()