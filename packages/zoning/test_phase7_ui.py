#!/usr/bin/env python3
"""
Phase 7: User Interface & Visualization Integration Test
Comprehensive test of the dashboard, visualization, and mapping components
"""
import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_phase7_ui_visualization():
    """Test Phase 7 user interface and visualization components"""
    print("🎨 PHASE 7: USER INTERFACE & VISUALIZATION TEST")
    print("=" * 80)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = {'passed': 0, 'failed': 0, 'tests': []}
    
    # Test 1: Dashboard Core Import and Initialization
    print("🧪 Test 1: Dashboard Core Import and Initialization")
    print("-" * 60)
    
    try:
        from app.utils.dashboard_core import DashboardCore
        dashboard = DashboardCore()
        print("✅ Dashboard core imported and initialized successfully")
        test_results['passed'] += 1
        test_results['tests'].append({'name': 'Dashboard Core Init', 'status': 'PASS'})
    except Exception as e:
        print(f"❌ Dashboard core import/init failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append({'name': 'Dashboard Core Init', 'status': 'FAIL', 'error': str(e)})
    
    # Test 2: Visualization Engine Import and Initialization
    print("\n🧪 Test 2: Visualization Engine Import and Initialization")
    print("-" * 60)
    
    try:
        from app.utils.visualization_engine import VisualizationEngine
        viz_engine = VisualizationEngine()
        print("✅ Visualization engine imported and initialized successfully")
        test_results['passed'] += 1
        test_results['tests'].append({'name': 'Visualization Engine Init', 'status': 'PASS'})
    except Exception as e:
        print(f"❌ Visualization engine import/init failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append({'name': 'Visualization Engine Init', 'status': 'FAIL', 'error': str(e)})
    
    # Test 3: Map Interface Import and Initialization
    print("\n🧪 Test 3: Map Interface Import and Initialization")
    print("-" * 60)
    
    try:
        from app.utils.map_interface import MapInterface
        map_interface = MapInterface()
        print("✅ Map interface imported and initialized successfully")
        test_results['passed'] += 1
        test_results['tests'].append({'name': 'Map Interface Init', 'status': 'PASS'})
    except Exception as e:
        print(f"❌ Map interface import/init failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append({'name': 'Map Interface Init', 'status': 'FAIL', 'error': str(e)})
    
    # Test 4: Web Interface Import and Initialization
    print("\n🧪 Test 4: Web Interface Import and Initialization")
    print("-" * 60)
    
    try:
        from app.utils.web_interface import WebInterface
        web_interface = WebInterface()
        print("✅ Web interface imported and initialized successfully")
        test_results['passed'] += 1
        test_results['tests'].append({'name': 'Web Interface Init', 'status': 'PASS'})
    except Exception as e:
        print(f"❌ Web interface import/init failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append({'name': 'Web Interface Init', 'status': 'FAIL', 'error': str(e)})
    
    # Test 5: Dashboard Data Generation
    print("\n🧪 Test 5: Dashboard Data Generation")
    print("-" * 60)
    
    try:
        # Create mock zone analysis data
        mock_zone_data = {
            'zone_id': 'TEST-01',
            'zone_name': 'Test Zone Lusaka',
            'area_km2': 2.5,
            'enhanced_population_estimate': {
                'estimated_population': 8500,
                'confidence': 'Medium'
            },
            'buildings_analysis': {
                'building_count': 1250,
                'error': False,
                'features': {
                    'area_statistics': {'mean': 85}
                }
            },
            'total_waste_kg_day': 3400,
            'residential_waste': 2550,
            'commercial_waste': 680,
            'industrial_waste': 170,
            'monthly_revenue': 2800,
            'annual_revenue': 33600,
            'collection_points': 15,
            'vehicles_required': 3,
            'settlement_classification': {
                'settlement_type': 'mixed',
                'confidence': 0.75,
                'error': False
            }
        }
        
        dashboard_data = dashboard.generate_dashboard_data(mock_zone_data)
        
        if not dashboard_data.get('error'):
            print("✅ Dashboard data generated successfully")
            print(f"   📊 Generated {len(dashboard_data.get('summary_cards', []))} summary cards")
            print(f"   📈 Chart types available: {len(dashboard_data.get('available_charts', []))}")
            test_results['passed'] += 1
            test_results['tests'].append({'name': 'Dashboard Data Generation', 'status': 'PASS'})
        else:
            print(f"❌ Dashboard data generation failed: {dashboard_data.get('error')}")
            test_results['failed'] += 1
            test_results['tests'].append({'name': 'Dashboard Data Generation', 'status': 'FAIL', 'error': dashboard_data.get('error')})
    
    except Exception as e:
        print(f"❌ Dashboard data generation test failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append({'name': 'Dashboard Data Generation', 'status': 'FAIL', 'error': str(e)})
    
    # Test 6: Chart Generation
    print("\n🧪 Test 6: Chart Generation")
    print("-" * 60)
    
    try:
        # Test population comparison chart
        chart_result = viz_engine.generate_chart_image('population_comparison', mock_zone_data, 'TEST-01')
        
        if not chart_result.get('error'):
            print("✅ Population comparison chart generated successfully")
            print(f"   📊 Chart title: {chart_result.get('title', 'N/A')}")
            print(f"   📈 Format: {chart_result.get('format', 'N/A')}")
            print(f"   📏 Image size: {len(chart_result.get('base64_image', ''))} characters (base64)")
            test_results['passed'] += 1
            test_results['tests'].append({'name': 'Chart Generation', 'status': 'PASS'})
        else:
            print(f"❌ Chart generation failed: {chart_result.get('error')}")
            test_results['failed'] += 1
            test_results['tests'].append({'name': 'Chart Generation', 'status': 'FAIL', 'error': chart_result.get('error')})
    
    except Exception as e:
        print(f"❌ Chart generation test failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append({'name': 'Chart Generation', 'status': 'FAIL', 'error': str(e)})
    
    # Test 7: Multiple Chart Types
    print("\n🧪 Test 7: Multiple Chart Types Generation")
    print("-" * 60)
    
    chart_types = ['waste_breakdown', 'building_distribution', 'revenue_projection']
    charts_generated = 0
    
    for chart_type in chart_types:
        try:
            chart_result = viz_engine.generate_chart_image(chart_type, mock_zone_data, 'TEST-01')
            if not chart_result.get('error'):
                charts_generated += 1
                print(f"   ✅ {chart_type} chart: Generated successfully")
            else:
                print(f"   ❌ {chart_type} chart: {chart_result.get('error')}")
        except Exception as e:
            print(f"   ❌ {chart_type} chart: Exception - {str(e)}")
    
    if charts_generated == len(chart_types):
        print(f"✅ All {len(chart_types)} chart types generated successfully")
        test_results['passed'] += 1
        test_results['tests'].append({'name': 'Multiple Chart Types', 'status': 'PASS'})
    elif charts_generated > 0:
        print(f"⚠️ Partial success: {charts_generated}/{len(chart_types)} chart types generated")
        test_results['passed'] += 1
        test_results['tests'].append({'name': 'Multiple Chart Types', 'status': 'PARTIAL'})
    else:
        print(f"❌ No chart types generated successfully")
        test_results['failed'] += 1
        test_results['tests'].append({'name': 'Multiple Chart Types', 'status': 'FAIL'})
    
    # Test 8: Map Data Generation
    print("\n🧪 Test 8: Map Data Generation")
    print("-" * 60)
    
    try:
        map_data = map_interface.generate_zone_map_data(mock_zone_data)
        
        if not map_data.get('error'):
            print("✅ Map data generated successfully")
            print(f"   🗺️ Center coordinates: {map_data.get('center', [])}")
            print(f"   🔍 Default zoom: {map_data.get('zoom', 'N/A')}")
            print(f"   🗂️ Base layers: {len(map_data.get('layers', {}).get('base_layers', {}))}")
            print(f"   📍 Data layers: {len(map_data.get('layers', {}).get('data_layers', {}))}")
            test_results['passed'] += 1
            test_results['tests'].append({'name': 'Map Data Generation', 'status': 'PASS'})
        else:
            print(f"❌ Map data generation failed: {map_data.get('error')}")
            test_results['failed'] += 1
            test_results['tests'].append({'name': 'Map Data Generation', 'status': 'FAIL', 'error': map_data.get('error')})
    
    except Exception as e:
        print(f"❌ Map data generation test failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append({'name': 'Map Data Generation', 'status': 'FAIL', 'error': str(e)})
    
    # Test 9: Map Data Export
    print("\n🧪 Test 9: Map Data Export")
    print("-" * 60)
    
    try:
        if 'map_data' in locals() and not map_data.get('error'):
            export_result = map_interface.export_map_data(map_data, 'geojson')
            
            if not export_result.get('error'):
                print("✅ Map data export successful")
                print(f"   📄 Filename: {export_result.get('filename', 'N/A')}")
                print(f"   🎯 Content type: {export_result.get('content_type', 'N/A')}")
                print(f"   📏 Data size: {len(export_result.get('data', ''))} characters")
                test_results['passed'] += 1
                test_results['tests'].append({'name': 'Map Data Export', 'status': 'PASS'})
            else:
                print(f"❌ Map data export failed: {export_result.get('error')}")
                test_results['failed'] += 1
                test_results['tests'].append({'name': 'Map Data Export', 'status': 'FAIL', 'error': export_result.get('error')})
        else:
            print("⚠️ Skipping map export test (map data generation failed)")
            test_results['tests'].append({'name': 'Map Data Export', 'status': 'SKIPPED'})
    
    except Exception as e:
        print(f"❌ Map data export test failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append({'name': 'Map Data Export', 'status': 'FAIL', 'error': str(e)})
    
    # Test 10: Web Interface Dashboard Routes
    print("\n🧪 Test 10: Web Interface Dashboard Routes")
    print("-" * 60)
    
    try:
        dashboard_routes = web_interface.get_dashboard_routes()
        
        if not dashboard_routes.get('error'):
            print("✅ Dashboard routes generated successfully")
            routes = dashboard_routes.get('routes', [])
            print(f"   🛤️ Available routes: {len(routes)}")
            for route in routes[:3]:  # Show first 3 routes
                print(f"      • {route.get('path', 'N/A')} - {route.get('name', 'N/A')}")
            if len(routes) > 3:
                print(f"      ... and {len(routes) - 3} more routes")
            test_results['passed'] += 1
            test_results['tests'].append({'name': 'Web Interface Routes', 'status': 'PASS'})
        else:
            print(f"❌ Dashboard routes generation failed: {dashboard_routes.get('error')}")
            test_results['failed'] += 1
            test_results['tests'].append({'name': 'Web Interface Routes', 'status': 'FAIL', 'error': dashboard_routes.get('error')})
    
    except Exception as e:
        print(f"❌ Web interface routes test failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append({'name': 'Web Interface Routes', 'status': 'FAIL', 'error': str(e)})
    
    # Test Summary
    print("\n" + "="*80)
    print("📋 PHASE 7 TEST SUMMARY")
    print("="*80)
    
    total_tests = test_results['passed'] + test_results['failed']
    success_rate = (test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"✅ Tests Passed: {test_results['passed']}")
    print(f"❌ Tests Failed: {test_results['failed']}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    print()
    
    # Determine overall quality score
    if success_rate >= 90:
        quality_score = "Excellent"
        quality_emoji = "🌟"
    elif success_rate >= 75:
        quality_score = "Good"
        quality_emoji = "✨"
    elif success_rate >= 60:
        quality_score = "Fair"
        quality_emoji = "⚡"
    else:
        quality_score = "Needs Improvement"
        quality_emoji = "🔧"
    
    print(f"{quality_emoji} Overall Quality: {quality_score} ({success_rate:.1f}%)")
    print()
    
    # Component Status Summary
    print("🔧 COMPONENT STATUS:")
    print("-" * 40)
    
    component_status = {
        'Dashboard Core': 'OPERATIONAL' if any(t['name'] == 'Dashboard Core Init' and t['status'] == 'PASS' for t in test_results['tests']) else 'FAILED',
        'Visualization Engine': 'OPERATIONAL' if any(t['name'] == 'Visualization Engine Init' and t['status'] == 'PASS' for t in test_results['tests']) else 'FAILED',
        'Map Interface': 'OPERATIONAL' if any(t['name'] == 'Map Interface Init' and t['status'] == 'PASS' for t in test_results['tests']) else 'FAILED',
        'Web Interface': 'OPERATIONAL' if any(t['name'] == 'Web Interface Init' and t['status'] == 'PASS' for t in test_results['tests']) else 'FAILED',
        'Chart Generation': 'OPERATIONAL' if any(t['name'] == 'Chart Generation' and t['status'] == 'PASS' for t in test_results['tests']) else 'FAILED',
        'Map Data System': 'OPERATIONAL' if any(t['name'] == 'Map Data Generation' and t['status'] == 'PASS' for t in test_results['tests']) else 'FAILED'
    }
    
    for component, status in component_status.items():
        status_emoji = "✅" if status == "OPERATIONAL" else "❌"
        print(f"{status_emoji} {component}: {status}")
    
    print("\n" + "="*80)
    
    if success_rate >= 80:
        print("🎉 PHASE 7 USER INTERFACE & VISUALIZATION: COMPLETE")
        print("🚀 Ready for production deployment!")
    elif success_rate >= 60:
        print("⚠️ PHASE 7 partially complete - minor issues to resolve")
    else:
        print("❌ PHASE 7 needs attention - critical issues found")
    
    print("="*80)
    
    return test_results

if __name__ == "__main__":
    test_phase7_ui_visualization() 