#!/usr/bin/env python
"""
Test WebSocket Real-time Analytics Functionality
"""
import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up environment
os.environ['FLASK_ENV'] = 'development'
os.environ['GOOGLE_MAPS_API_KEY'] = 'test-key'

from app import create_app, socketio
from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer

def test_websocket_analytics():
    """Test WebSocket real-time analytics"""
    app = create_app()
    
    with app.app_context():
        print("\n=== Testing WebSocket Real-time Analytics ===")
        
        # Check if WebSocket manager is initialized
        if hasattr(app, 'websocket_manager'):
            print("✅ WebSocket manager is initialized")
            
            # Test zone analyzer
            analyzer = EnhancedRealTimeZoneAnalyzer()
            
            # Test geometry
            test_zone_geojson = {
                "type": "Polygon",
                "coordinates": [[
                    [28.2833, -15.4167],
                    [28.2900, -15.4167], 
                    [28.2900, -15.4100],
                    [28.2833, -15.4100],
                    [28.2833, -15.4167]
                ]]
            }
            
            print("\n🔄 Running zone analysis...")
            start_time = time.time()
            
            try:
                result = analyzer.analyze_drawn_zone(test_zone_geojson, {
                    'name': 'Test Zone',
                    'zone_type': 'residential'
                })
                
                end_time = time.time()
                
                print(f"\n✅ Analysis completed in {end_time - start_time:.2f} seconds")
                
                # Display key results
                if 'analysis_modules' in result:
                    modules = result['analysis_modules']
                    
                    # Geometry analysis
                    if 'geometry' in modules and not modules['geometry'].get('error'):
                        geo = modules['geometry']
                        print(f"\n📐 Geometry Analysis:")
                        print(f"   Area: {geo.get('area_sqkm', 0):.3f} km²")
                        print(f"   Perimeter: {geo.get('perimeter_km', 0):.2f} km")
                        print(f"   Compactness: {geo.get('compactness_index', 0):.2f}")
                    
                    # Population estimation
                    if 'population_estimation' in modules and not modules['population_estimation'].get('error'):
                        pop = modules['population_estimation']
                        print(f"\n👥 Population Estimation:")
                        print(f"   Total Population: {pop.get('total_population', 0):,}")
                        print(f"   Density: {pop.get('density_per_sqkm', 0):.0f} people/km²")
                    
                    # Waste analysis
                    if 'waste_analysis' in modules and not modules['waste_analysis'].get('error'):
                        waste = modules['waste_analysis']
                        print(f"\n♻️  Waste Analysis:")
                        print(f"   Daily Waste: {waste.get('daily_waste_tons', 0):.2f} tons")
                        print(f"   Monthly Waste: {waste.get('monthly_waste_tons', 0):.0f} tons")
                    
                    # Check for offline components
                    if result.get('offline_mode'):
                        print(f"\n⚠️  Running in offline mode")
                        print(f"   Offline components: {', '.join(result.get('offline_components', []))}")
                        if result.get('enhanced_estimates_mode'):
                            print("   Using enhanced area-based estimates (reliable for planning)")
                
                # Overall assessment
                print(f"\n📊 Zone Viability Score: {result.get('zone_viability_score', 0):.1f}/10")
                
                if result.get('critical_issues'):
                    print(f"\n⚠️  Critical Issues:")
                    for issue in result['critical_issues'][:3]:
                        print(f"   - {issue}")
                
                if result.get('optimization_recommendations'):
                    print(f"\n💡 Top Recommendations:")
                    for rec in result['optimization_recommendations'][:3]:
                        print(f"   - {rec}")
                
            except Exception as e:
                print(f"\n❌ Analysis failed: {str(e)}")
                import traceback
                traceback.print_exc()
                
        else:
            print("❌ WebSocket manager not initialized")
        
        # Test WebSocket server
        print("\n\n=== Testing WebSocket Server ===")
        print("To test real-time updates:")
        print("1. Run this app with: python test_websocket_real_time.py --server")
        print("2. Open browser to: http://localhost:5001/zones/create/websocket")
        print("3. Draw a zone and watch real-time analytics")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--server':
        # Run the WebSocket server
        app = create_app()
        print("\n🚀 Starting WebSocket-enabled server on http://localhost:5001")
        print("   Navigate to: http://localhost:5001/zones/create/websocket")
        socketio.run(app, debug=True, host='0.0.0.0', port=5001)
    else:
        # Run the test
        test_websocket_analytics() 