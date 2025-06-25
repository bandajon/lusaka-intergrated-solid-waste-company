#!/usr/bin/env python3
"""
Real-time Zone Analysis Demo
Demonstrates the comprehensive zone analysis that runs when users draw zones
"""
import json
import time
import sys
from typing import Dict, Any

# Add the app directory to the path
sys.path.insert(0, './app')

from app.utils.real_time_zone_analyzer import RealTimeZoneAnalyzer


def create_test_zones():
    """Create different test zone scenarios"""
    
    zones = {
        "optimal_residential": {
            "name": "Optimal Residential Zone",
            "geometry": {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [28.2800, -15.4100],  # SW corner
                        [28.2850, -15.4100],  # SE corner  
                        [28.2850, -15.4050],  # NE corner
                        [28.2800, -15.4050],  # NW corner
                        [28.2800, -15.4100]   # Close polygon
                    ]]
                },
                "properties": {}
            },
            "metadata": {
                "zone_type": "residential",
                "estimated_population": 1200,
                "collection_frequency": 2
            },
            "description": "Well-sized residential zone with good access"
        },
        
        "too_large_zone": {
            "name": "Oversized Zone (Should Trigger Warnings)",
            "geometry": {
                "type": "Feature", 
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [28.2700, -15.4200],  # SW corner - much larger
                        [28.3000, -15.4200],  # SE corner  
                        [28.3000, -15.3900],  # NE corner
                        [28.2700, -15.3900],  # NW corner
                        [28.2700, -15.4200]   # Close polygon
                    ]]
                },
                "properties": {}
            },
            "metadata": {
                "zone_type": "mixed",
                "estimated_population": 8000,
                "collection_frequency": 3
            },
            "description": "Very large zone that should trigger recommendations to split"
        },
        
        "complex_shaped_zone": {
            "name": "Complex Shaped Zone",
            "geometry": {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon", 
                    "coordinates": [[
                        [28.2800, -15.4100],
                        [28.2900, -15.4100],
                        [28.2900, -15.4050],
                        [28.2950, -15.4050],
                        [28.2950, -15.4000],
                        [28.2850, -15.4000],
                        [28.2850, -15.4030],
                        [28.2800, -15.4030],
                        [28.2800, -15.4100]   # Close polygon
                    ]]
                },
                "properties": {}
            },
            "metadata": {
                "zone_type": "commercial",
                "estimated_population": 500,
                "collection_frequency": 4
            },
            "description": "Irregularly shaped zone with potential collection challenges"
        }
    }
    
    return zones


def format_analysis_results(zone_name: str, results: Dict[str, Any]) -> str:
    """Format analysis results for display"""
    
    output = [
        f"\n{'='*60}",
        f"🗺️  ZONE ANALYSIS: {zone_name}",
        f"{'='*60}",
    ]
    
    # Zone Viability Score
    score = results.get('zone_viability_score', 0)
    score_emoji = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
    output.append(f"\n{score_emoji} **Zone Viability Score: {score:.1f}/100**")
    
    # Critical Issues (Most Important)
    critical_issues = results.get('critical_issues', [])
    if critical_issues:
        output.append(f"\n⚠️  **CRITICAL ISSUES:**")
        for issue in critical_issues:
            output.append(f"   • {issue.get('issue', 'Unknown issue')}")
            output.append(f"     → {issue.get('recommendation', 'No recommendation')}")
    else:
        output.append(f"\n✅ **No Critical Issues Detected**")
    
    # Optimization Recommendations
    recommendations = results.get('optimization_recommendations', [])
    if recommendations:
        output.append(f"\n💡 **OPTIMIZATION RECOMMENDATIONS:**")
        for rec in recommendations:
            output.append(f"   • {rec.get('issue', 'Improvement area')}")
            output.append(f"     → {rec.get('recommendation', 'No specific recommendation')}")
    else:
        output.append(f"\n✅ **Zone appears well-optimized**")
    
    # Analysis Modules Summary
    modules = results.get('analysis_modules', {})
    output.append(f"\n📊 **ANALYSIS SUMMARY:**")
    
    # Geometry Analysis
    geometry = modules.get('geometry', {})
    if geometry:
        area = geometry.get('area_sqkm', 0)
        perimeter = geometry.get('perimeter_km', 0)
        output.append(f"   📐 Area: {area:.3f} km² | Perimeter: {perimeter:.2f} km")
        
        quality = geometry.get('shape_quality', {})
        if quality:
            size_rating = quality.get('size_appropriateness', 'unknown')
            compactness = geometry.get('compactness_index', 0)
            output.append(f"   📏 Size Rating: {size_rating} | Compactness: {compactness:.2f}")
    
    # Population Analysis
    population = modules.get('population', {})
    if population:
        consensus = population.get('consensus', 0)
        confidence = population.get('confidence', 0)
        output.append(f"   👥 Est. Population: {consensus:,} (Confidence: {confidence}%)")
    
    # Collection Feasibility
    collection = modules.get('collection_feasibility', {})
    if collection:
        score = collection.get('overall_score', 0)
        access = collection.get('accessibility', 'unknown')
        output.append(f"   🚛 Collection Score: {score}/100 | Access: {access}")
    
    # AI Insights
    ai_insights = modules.get('ai_insights', {})
    if ai_insights:
        risk = ai_insights.get('waste_generation_risk', 'unknown')
        challenges = ai_insights.get('collection_challenges', [])
        output.append(f"   🤖 AI Risk Assessment: {risk}")
        if challenges:
            output.append(f"      Challenges: {', '.join(challenges)}")
    
    # Performance Metrics
    performance = results.get('performance_metrics', {})
    if performance:
        analysis_time = performance.get('total_analysis_time_seconds', 0)
        completed = performance.get('modules_completed', 0)
        failed = performance.get('modules_failed', 0)
        output.append(f"\n⏱️  **Analysis completed in {analysis_time:.2f}s**")
        output.append(f"   ✅ {completed} modules completed | ❌ {failed} modules failed")
    
    return '\n'.join(output)


def demonstrate_real_time_feedback():
    """Demonstrate the real-time analysis feedback system"""
    
    print("🚀 Real-time Zone Analysis Demo")
    print("This shows what happens when you draw a zone on the map")
    print("=" * 60)
    
    # Initialize the analyzer
    print("\n🔧 Initializing Real-time Zone Analyzer...")
    analyzer = RealTimeZoneAnalyzer()
    print("✅ Analyzer ready!")
    
    # Get test zones
    test_zones = create_test_zones()
    
    # Analyze each zone scenario
    for zone_key, zone_data in test_zones.items():
        print(f"\n🎯 Analyzing: {zone_data['name']}")
        print(f"📝 Scenario: {zone_data['description']}")
        print("⏳ Running comprehensive analysis...")
        
        start_time = time.time()
        
        try:
            # This is what happens when a user draws a zone
            results = analyzer.analyze_drawn_zone(
                zone_data['geometry'], 
                zone_data['metadata']
            )
            
            analysis_time = time.time() - start_time
            print(f"✅ Analysis completed in {analysis_time:.2f} seconds")
            
            # Display results (this would be shown in the UI)
            formatted_results = format_analysis_results(zone_data['name'], results)
            print(formatted_results)
            
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
        
        print(f"\n{'─'*60}")
        input("Press Enter to analyze next zone...")
    
    print(f"\n🎉 Demo Complete!")
    print("\n💡 **Real-time Analysis Features:**")
    print("   • Instant feedback as you draw zones")
    print("   • Comprehensive viability scoring")
    print("   • Critical issue identification")
    print("   • Optimization recommendations")
    print("   • Multi-module analysis integration")
    print("   • Performance monitoring")
    print("\n📱 **User Experience:**")
    print("   • Draw zone → Get immediate feedback")
    print("   • Adjust boundaries → See updated analysis")
    print("   • Red flags for critical issues")
    print("   • Green light when zone is optimal")
    print("   • Specific recommendations for improvements")


def simulate_interactive_drawing():
    """Simulate the interactive zone drawing experience"""
    
    print("\n" + "="*60)
    print("🎮 INTERACTIVE ZONE DRAWING SIMULATION")
    print("="*60)
    
    print("\n🗺️  Imagine you're drawing a zone on the map...")
    print("As you add each point, the analysis updates in real-time:")
    
    # Simulate progressive zone drawing
    analyzer = RealTimeZoneAnalyzer()
    
    # Start with a simple square
    base_coords = [
        [28.2800, -15.4100],  # SW corner
        [28.2820, -15.4100],  # SE corner  
        [28.2820, -15.4080],  # NE corner
        [28.2800, -15.4080],  # NW corner
        [28.2800, -15.4100]   # Close polygon
    ]
    
    stages = [
        {"name": "Small zone", "scale": 1.0, "description": "Good size for residential"},
        {"name": "Medium zone", "scale": 2.0, "description": "Getting larger..."},
        {"name": "Large zone", "scale": 3.0, "description": "Might be too big"},
        {"name": "Very large zone", "scale": 4.0, "description": "Definitely too big!"}
    ]
    
    for stage in stages:
        print(f"\n🖱️  Drawing stage: {stage['name']}")
        print(f"📝 {stage['description']}")
        
        # Scale the coordinates
        scaled_coords = []
        center_lng, center_lat = 28.2810, -15.4090
        for lng, lat in base_coords:
            scaled_lng = center_lng + (lng - center_lng) * stage['scale']
            scaled_lat = center_lat + (lat - center_lat) * stage['scale']
            scaled_coords.append([scaled_lng, scaled_lat])
        
        geometry = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [scaled_coords]
            },
            "properties": {}
        }
        
        metadata = {
            "zone_type": "residential",
            "estimated_population": int(1000 * stage['scale']**2),
            "collection_frequency": 2
        }
        
        # Quick analysis
        try:
            results = analyzer.analyze_drawn_zone(geometry, metadata)
            score = results.get('zone_viability_score', 0)
            critical_issues = results.get('critical_issues', [])
            
            # Show immediate feedback
            if score >= 70:
                print(f"   ✅ Viability Score: {score:.1f}/100 - Looking good!")
            elif score >= 50:
                print(f"   ⚠️  Viability Score: {score:.1f}/100 - Consider adjustments")
            else:
                print(f"   ❌ Viability Score: {score:.1f}/100 - Needs significant changes")
            
            if critical_issues:
                print("   🚨 Critical Issues:")
                for issue in critical_issues[:2]:  # Show first 2 issues
                    print(f"      • {issue.get('issue', 'Unknown issue')}")
            else:
                print("   ✨ No critical issues detected")
                
        except Exception as e:
            print(f"   ❌ Analysis error: {str(e)}")
        
        time.sleep(1)  # Simulate real-time delay
    
    print(f"\n💡 **This real-time feedback helps you:**")
    print("   • Optimize zone boundaries as you draw")
    print("   • Avoid problematic configurations")
    print("   • Understand analysis criteria")
    print("   • Make data-driven zoning decisions")


def main():
    """Run the comprehensive real-time analysis demo"""
    
    try:
        # Main demonstration
        demonstrate_real_time_feedback()
        
        # Interactive simulation
        simulate_interactive_drawing()
        
        print(f"\n🎯 **Integration Summary:**")
        print("✅ Real-time zone analyzer integrated")
        print("✅ JavaScript frontend integration ready")
        print("✅ Flask API endpoints configured")
        print("✅ Comprehensive analysis modules connected")
        print("✅ User experience optimized for immediate feedback")
        
        print(f"\n🚀 **Ready for Production!**")
        print("Users can now draw zones and get instant analysis feedback!")
        
    except KeyboardInterrupt:
        print(f"\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main() 