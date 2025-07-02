#!/usr/bin/env python3
"""
Test script for Company Unification Tool
"""

import sys
import os
import pandas as pd

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

from flask_app.utils.company_unifier import CompanyUnifier

def create_test_data():
    """Create sample test data to demonstrate the unification tool"""
    test_companies = [
        {'company_id': 'comp_001', 'name': 'LISWMC MATERO', 'type_code': 1, 'location': 'Matero'},
        {'company_id': 'comp_002', 'name': 'LISWMC MATERO LIMITED', 'type_code': 1, 'location': 'Matero'},
        {'company_id': 'comp_003', 'name': 'LCC/LISWMC', 'type_code': 2, 'location': 'Lusaka'},
        {'company_id': 'comp_004', 'name': 'LCC LISWMC', 'type_code': 2, 'location': 'Lusaka'},
        {'company_id': 'comp_005', 'name': 'Lusaka city Council', 'type_code': 3, 'location': 'City Center'},
        {'company_id': 'comp_006', 'name': 'LUSAKA CITY COUNCIL', 'type_code': 3, 'location': 'City Center'},
        {'company_id': 'comp_007', 'name': 'petrushka', 'type_code': 4, 'location': 'Industrial'},
        {'company_id': 'comp_008', 'name': 'PETRUSHKA LIMITED', 'type_code': 4, 'location': 'Industrial'},
        {'company_id': 'comp_009', 'name': 'BL', 'type_code': 5, 'location': 'Suburb'},
        {'company_id': 'comp_010', 'name': 'BL CONSTRUCTION', 'type_code': 5, 'location': 'Suburb'},
        {'company_id': 'comp_011', 'name': 'CDF', 'type_code': 6, 'location': 'Rural'},
        {'company_id': 'comp_012', 'name': 'CITIMOP LIMITED', 'type_code': 7, 'location': 'Commercial'},
        {'company_id': 'comp_013', 'name': 'franchel', 'type_code': 8, 'location': 'Residential'},
        {'company_id': 'comp_014', 'name': 'FRANCHEL COMPANY', 'type_code': 8, 'location': 'Residential'},
    ]
    
    return pd.DataFrame(test_companies)

def test_duplicate_detection():
    """Test the duplicate detection functionality"""
    print("🔍 Testing Company Unification Tool")
    print("=" * 50)
    
    # Create test unifier
    unifier = CompanyUnifier(similarity_threshold=0.6)  # Lower threshold for testing
    
    # Use test data instead of database
    unifier.companies_df = create_test_data()
    
    print(f"📊 Loaded {len(unifier.companies_df)} test companies")
    print("\nTest companies:")
    for _, company in unifier.companies_df.iterrows():
        print(f"  • {company['name']} (ID: {company['company_id']})")
    
    # Find duplicates
    print(f"\n🔄 Finding duplicate groups with threshold {unifier.similarity_threshold}...")
    duplicate_groups = unifier.find_duplicate_groups()
    
    print(f"\n✅ Found {len(duplicate_groups)} duplicate groups")
    
    # Display results
    if duplicate_groups:
        for i, group in enumerate(duplicate_groups):
            print(f"\n📋 Group {i+1} ({group['group_id']}):")
            print(f"   Main: {group['main_company']['name']} (ID: {group['main_company']['company_id']})")
            print(f"   Similar companies:")
            for similar in group['similar_companies']:
                print(f"     • {similar['name']} (ID: {similar['company_id']}, {similar['similarity']:.1%} match)")
            print(f"   Suggested merge name: '{group['suggested_merge_name']}'")
    
    # Get summary
    summary = unifier.get_duplicate_summary()
    print(f"\n📈 Summary:")
    print(f"   Total groups: {summary['total_groups']}")
    print(f"   Total duplicates: {summary['total_duplicates']}")
    print(f"   Potential reduction: {summary['potential_reduction']} companies")
    print(f"   Original count: {summary['original_count']}")
    
    if summary['total_duplicates'] > 0:
        reduction_pct = (summary['potential_reduction'] / summary['original_count']) * 100
        print(f"   Potential reduction: {reduction_pct:.1f}%")
    
    return duplicate_groups, summary

def test_similarity_calculations():
    """Test similarity calculation function"""
    print("\n🧮 Testing similarity calculations:")
    print("=" * 50)
    
    unifier = CompanyUnifier()
    
    test_pairs = [
        ("LISWMC MATERO", "LISWMC MATERO LIMITED"),
        ("LCC/LISWMC", "LCC LISWMC"),
        ("Lusaka city Council", "LUSAKA CITY COUNCIL"),
        ("petrushka", "PETRUSHKA LIMITED"),
        ("BL", "BL CONSTRUCTION"),
        ("franchel", "FRANCHEL COMPANY"),
        ("CDF", "CITIMOP LIMITED"),  # Should be low similarity
    ]
    
    for name1, name2 in test_pairs:
        similarity = unifier.calculate_similarity(name1, name2)
        print(f"   '{name1}' <-> '{name2}': {similarity:.3f} ({similarity:.1%})")

def test_pattern_search():
    """Test pattern-based company search"""
    print("\n🔍 Testing pattern search:")
    print("=" * 50)
    
    unifier = CompanyUnifier()
    unifier.companies_df = create_test_data()
    
    patterns = ["BL", "LISWMC", "Council", "LIMITED"]
    
    for pattern in patterns:
        matches = unifier.get_companies_by_pattern(pattern)
        print(f"   Pattern '{pattern}': {len(matches)} matches")
        for match in matches:
            print(f"     • {match['name']} (ID: {match['company_id']})")

if __name__ == "__main__":
    print("🚀 Company Unification Tool Test Suite")
    print("=====================================")
    
    try:
        # Test similarity calculations
        test_similarity_calculations()
        
        # Test pattern search
        test_pattern_search()
        
        # Test duplicate detection
        duplicate_groups, summary = test_duplicate_detection()
        
        print(f"\n✅ All tests completed successfully!")
        
        if summary['total_groups'] > 0:
            print(f"\n💡 The tool found {summary['total_groups']} groups of potential duplicates.")
            print("   You can now use the web interface to review and merge them.")
        else:
            print(f"\n💡 No duplicates found with current threshold.")
            print("   Try lowering the similarity threshold if you expect more matches.")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()