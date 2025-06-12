import pandas as pd
from vehicle_plate_cleaner import clean_license_plate

def test_enhanced_space_handling():
    """Test the enhanced license plate cleaner with various space patterns"""
    test_plates = [
        # Various formats of spaces between letters and numbers
        "ABC 1234",        # Standard format with space
        "AB 123",          # Short format with space
        "ABCD 12345",      # Long format with space
        "A B C 1 2 3 4",   # Spaces everywhere
        "A BC 12 34",      # Mixed spaces
        
        # Spaces in different positions
        " ABC1234",        # Space at beginning
        "ABC1234 ",        # Space at end
        " ABC 1234 ",      # Spaces at beginning, middle, and end
        
        # Real-world examples with unusual spacing
        "ABG 6138",
        "ALK 55",
        "BAL 8583",
        "GRZ 24",
    ]
    
    print("Testing enhanced space handling in license plates:")
    print("=" * 65)
    print("| {:<20} | {:<20} | {:<20} |".format("Original", "Cleaned", "Notes"))
    print("|" + "-"*22 + "|" + "-"*22 + "|" + "-"*22 + "|")
    
    for plate in test_plates:
        cleaned = clean_license_plate(plate)
        
        # Add notes about the transformation
        notes = ""
        if not cleaned:
            notes = "Rejected"
        elif len(cleaned) == 7 and cleaned.isalnum() and cleaned[:3].isalpha() and cleaned[3:].isdigit():
            notes = "Standardized to AAA####"
        elif cleaned.startswith("GRZ"):
            notes = "GRZ format preserved"
        else:
            notes = "Custom format"
        
        print("| {:<20} | {:<20} | {:<20} |".format(plate, cleaned, notes))
    
    print("=" * 65)

# Run the test
if __name__ == "__main__":
    test_enhanced_space_handling()