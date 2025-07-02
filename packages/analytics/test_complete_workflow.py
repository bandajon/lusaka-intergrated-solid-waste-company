#!/usr/bin/env python3
"""
Complete Analytics Workflow Test
================================
Test the complete analytics workflow with database loading and company unification
"""

import sys
import os

# Add analytics directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_database_connection():
    """Test database connectivity"""
    print("🔌 Testing database connection...")
    try:
        from database_connection import check_connection
        is_connected, msg = check_connection()
        if is_connected:
            print("   ✅ Database connection successful")
            return True
        else:
            print(f"   ❌ Database connection failed: {msg}")
            return False
    except Exception as e:
        print(f"   ❌ Database connection error: {e}")
        return False

def test_data_loading():
    """Test data loading from database"""
    print("📊 Testing data loading from database...")
    try:
        from database_connection import read_companies, read_vehicles, read_weigh_events
        
        # Test companies loading
        companies_df = read_companies()
        print(f"   ✅ Loaded {len(companies_df)} companies")
        
        # Test vehicles loading  
        vehicles_df = read_vehicles()
        print(f"   ✅ Loaded {len(vehicles_df)} vehicles")
        
        # Test weigh events loading
        weigh_df = read_weigh_events()
        print(f"   ✅ Loaded {len(weigh_df)} weigh events")
        
        return True
    except Exception as e:
        print(f"   ❌ Data loading error: {e}")
        return False

def test_company_unifier():
    """Test company unification functionality"""
    print("🏢 Testing company unification...")
    try:
        from flask_app.utils.company_unifier import CompanyUnifier
        
        unifier = CompanyUnifier()
        success = unifier.load_companies_from_db()
        
        if success:
            print("   ✅ Company unifier database loading successful")
            
            # Find duplicate groups
            duplicate_groups = unifier.find_duplicate_groups()
            print(f"   ✅ Found {len(duplicate_groups)} duplicate groups")
            
            # Get summary
            summary = unifier.get_duplicate_summary()
            print(f"   ✅ Summary: {summary['total_duplicates']} potential duplicates")
            
            return True
        else:
            print("   ❌ Company unifier failed to load from database")
            return False
    except Exception as e:
        print(f"   ❌ Company unifier error: {e}")
        return False

def test_dashboard_loading():
    """Test dashboard data loading"""
    print("📈 Testing dashboard data loading...")
    try:
        from flask_app.dashboards.weigh_events_dashboard import load_data
        
        merged_df, weigh_df, vehicles_df, companies_df = load_data()
        
        print(f"   ✅ Dashboard loaded:")
        print(f"      - {len(companies_df)} companies")
        print(f"      - {len(vehicles_df)} vehicles") 
        print(f"      - {len(weigh_df)} weigh events")
        print(f"      - {len(merged_df)} merged records")
        
        return True
    except Exception as e:
        print(f"   ❌ Dashboard loading error: {e}")
        return False

def main():
    """Run complete workflow test"""
    print("🚀 LISWMC Analytics Complete Workflow Test")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Data Loading", test_data_loading),
        ("Company Unification", test_company_unifier),
        ("Dashboard Loading", test_dashboard_loading)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Complete Workflow Test Results")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🏁 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Complete workflow test successful!")
        print("\n💡 System Status:")
        print("   ✅ Database connectivity working")
        print("   ✅ Data loading from database working")
        print("   ✅ Company unification ready")
        print("   ✅ Dashboard using live database data")
        print("\n🌐 Services Available:")
        print("   📊 Analytics Dashboard: http://localhost:5007")
        print("   🔧 Data Management: http://localhost:5002")
        print("   🏢 Company Unification: http://localhost:5002/companies/unify")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)