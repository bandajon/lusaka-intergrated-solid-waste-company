"""
Google Gemini Flash API Integration for Intelligent Waste Collection Recommendations
"""

import os
import json
import logging
import math
from typing import Dict, Any, Optional
from dataclasses import dataclass
import google.genai as genai

logger = logging.getLogger(__name__)

@dataclass
class TruckRecommendation:
    """Structured truck recommendation from Gemini"""
    truck_type: str
    truck_count: int
    total_capacity_kg: int
    collection_frequency: int
    weekly_operational_cost: int
    monthly_total_cost: int
    cost_breakdown: Dict[str, int]
    efficiency_percent: float
    reasoning: str
    mathematical_validation: str

class GeminiRecommendationEngine:
    """
    AI-powered waste collection recommendation engine using Google Gemini Flash
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client with API key"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        try:
            # Set API key as environment variable for the client
            os.environ['GOOGLE_API_KEY'] = self.api_key
            self.client = genai.Client()
            logger.info("✅ Gemini Flash recommendation engine initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini client: {str(e)}")
            raise
    
    def generate_truck_recommendation(self, 
                                    population: int,
                                    daily_waste_kg: float,
                                    distance_to_dump_km: float,
                                    settlement_type: str = "mixed") -> TruckRecommendation:
        """
        Generate intelligent truck fleet recommendations using Gemini Flash
        """
        try:
            weekly_waste_kg = daily_waste_kg * 7
            weekly_waste_tonnes = weekly_waste_kg / 1000
            
            # Prepare comprehensive context for Gemini
            context = self._build_analysis_context(
                population, daily_waste_kg, weekly_waste_kg, 
                distance_to_dump_km, settlement_type
            )
            
            # Generate recommendation using Gemini
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=context
            )
            
            # Parse and validate response
            recommendation = self._parse_gemini_response(response.text, weekly_waste_kg, distance_to_dump_km)
            
            logger.info(f"🎯 Gemini recommendation: {recommendation.truck_count}x {recommendation.truck_type} "
                       f"for {weekly_waste_tonnes:.1f} tonnes/week")
            
            return recommendation
            
        except Exception as e:
            logger.error(f"❌ Gemini recommendation failed: {str(e)}")
            return self._fallback_recommendation(daily_waste_kg)
    
    def _build_analysis_context(self, population: int, daily_waste_kg: float, 
                               weekly_waste_kg: float, distance_km: float, 
                               settlement_type: str) -> str:
        """Build comprehensive context for Gemini analysis"""
        
        # Calculate example costs for guidance
        round_trip_km = distance_km * 2
        fuel_cost_per_trip = (round_trip_km / 6.0) * 23  # K23/liter, 6km/liter
        weekly_waste_tonnes = weekly_waste_kg / 1000
        # Chunga dumpsite charges full tonnes only (3.1 tonnes = 4 tonnes billing)
        billable_tonnes = math.ceil(weekly_waste_tonnes)
        franchise_cost_per_week = billable_tonnes * 50  # K50/tonne
        
        context = f"""
You are an expert waste management consultant for Lusaka, Zambia. Your goal is to recommend the MOST EFFICIENT and COST-EFFECTIVE truck fleet that can handle all waste with minimal over-capacity.

SCENARIO ANALYSIS:
📊 Zone Data:
- Population: {population:,} people
- Daily waste generation: {daily_waste_kg:,.1f} kg ({daily_waste_kg/1000:.1f} tonnes)
- Weekly waste generation: {weekly_waste_kg:,.1f} kg ({weekly_waste_kg/1000:.1f} tonnes)
- Distance to Chunga dump site: {distance_km:.1f} km (round trip: {round_trip_km:.1f} km)
- Settlement type: {settlement_type}

💰 COST CALCULATION REQUIREMENTS:
- Fuel cost per trip: K{fuel_cost_per_trip:.0f} ({round_trip_km:.1f}km @ K23/liter, 6km/liter efficiency)
- Franchise fee: K{franchise_cost_per_week:.0f} total per week ({billable_tonnes:.0f} billable tonnes @ K50/tonne)
  ⚠️ IMPORTANT: Chunga dumpsite bills full tonnes only (3.1 tonnes = 4 tonnes billing)
- Employee salaries: K10,000/month (4 employees × K2,500 each)
- Admin overhead: 30% of (operational + salaries)

🚛 Available Truck Options:
- 5-tonne: 5,000 kg capacity
- 10-tonne: 10,000 kg capacity  
- 15-tonne: 15,000 kg capacity
- 20-tonne: 20,000 kg capacity
- 25-tonne: 25,000 kg capacity

⚡ EFFICIENCY TARGETS:
- Truck utilization: 80-95% of capacity (avoid under-utilization)
- Prefer fewer trucks over multiple trucks when possible
- Minimize excess capacity to reduce costs
- Collection frequency: 1-3 times per week is typical

💡 COST CALCULATION EXAMPLES:
- Example: 1x 10-tonne, 1 collection/week, 10km distance, collecting 10 tonnes
  * Weekly fuel: K{fuel_cost_per_trip:.0f} × 1 trip = K{fuel_cost_per_trip:.0f}
  * Weekly franchise: ceil(10.0 tonnes) = 10 billable tonnes × K50 = K500
  * Weekly operational: K{fuel_cost_per_trip:.0f} + K500 = K{fuel_cost_per_trip + 500:.0f}
  * Monthly operational: K{fuel_cost_per_trip + 500:.0f} × 4.33 = K{(fuel_cost_per_trip + 500) * 4.33:.0f}
  * Monthly salaries: K10,000
  * Admin overhead: K{((fuel_cost_per_trip + 500) * 4.33 + 10000) * 0.30:.0f}
  * Total monthly: K{((fuel_cost_per_trip + 500) * 4.33 + 10000) * 1.30:.0f}

CRITICAL RULES:
1. Weekly capacity should be 105-120% of weekly waste (small buffer only)
2. Avoid recommending 3+ trucks unless waste > 60 tonnes/week
3. Single truck solutions are preferred for operational simplicity
4. Calculate realistic costs using the formulas above

PROVIDE YOUR RECOMMENDATION IN THIS EXACT JSON FORMAT:
{{
    "truck_type": "XX_tonne",
    "truck_count": X,
    "collection_frequency": X,
    "total_weekly_capacity_kg": XXXX,
    "weekly_operational_cost": XXXX,
    "monthly_total_cost": XXXX,
    "cost_breakdown": {{
        "weekly_fuel_cost": XXXX,
        "weekly_franchise_cost": XXXX,
        "monthly_salaries": 10000,
        "monthly_admin_overhead": XXXX
    }},
    "efficiency_percent": XX.X,
    "reasoning": "Explain efficiency and show cost calculation",
    "mathematical_validation": "Show capacity vs waste and cost calculation"
}}

FOR THIS SCENARIO ({weekly_waste_kg:,.0f} kg/week = {weekly_waste_tonnes:.1f} tonnes/week):
Calculate weekly operational cost and monthly total cost using the formulas above.
"""
        
        return context
    
    def _calculate_cost_breakdown(self, truck_count: int, collection_frequency: int, 
                                 weekly_waste_kg: float, distance_km: float) -> Dict[str, int]:
        """Calculate fallback cost breakdown"""
        round_trip_distance = distance_km * 2
        fuel_cost_per_trip = (round_trip_distance / 6.0) * 23
        trips_per_week = collection_frequency * truck_count
        weekly_fuel_cost = fuel_cost_per_trip * trips_per_week
        
        weekly_waste_tonnes = weekly_waste_kg / 1000
        # Chunga dumpsite charges full tonnes only (round up)
        billable_tonnes = math.ceil(weekly_waste_tonnes)
        weekly_franchise_cost = billable_tonnes * 50
        
        monthly_operational = (weekly_fuel_cost + weekly_franchise_cost) * 4.33
        monthly_salaries = 10000
        monthly_admin_overhead = int((monthly_operational + monthly_salaries) * 0.30)
        
        return {
            'weekly_fuel_cost': int(weekly_fuel_cost),
            'weekly_franchise_cost': int(weekly_franchise_cost),
            'monthly_salaries': monthly_salaries,
            'monthly_admin_overhead': monthly_admin_overhead
        }
    
    def _parse_gemini_response(self, response_text: str, weekly_waste_kg: float, distance_km: float = 10.0) -> TruckRecommendation:
        """Parse Gemini's JSON response into structured recommendation"""
        try:
            # Extract JSON from response (handle potential markdown formatting)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in Gemini response")
            
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['truck_type', 'truck_count', 'collection_frequency', 
                             'total_weekly_capacity_kg', 'weekly_operational_cost', 'monthly_total_cost', 'reasoning']
            
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate mathematical accuracy
            weekly_capacity = data['total_weekly_capacity_kg']
            if weekly_capacity < weekly_waste_kg:
                logger.warning(f"⚠️ Gemini recommendation insufficient: {weekly_capacity} < {weekly_waste_kg}")
                # Auto-correct by scaling up truck count
                scale_factor = (weekly_waste_kg / weekly_capacity) + 0.1  # 10% buffer
                data['truck_count'] = int(data['truck_count'] * scale_factor) + 1
                data['total_weekly_capacity_kg'] = int(weekly_capacity * scale_factor)
                data['weekly_operational_cost'] = int(data['weekly_operational_cost'] * scale_factor)
                data['monthly_total_cost'] = int(data['monthly_total_cost'] * scale_factor)
                data['reasoning'] += f" [Auto-corrected truck count for mathematical accuracy]"
            
            # Validate cost breakdown exists
            cost_breakdown = data.get('cost_breakdown', {})
            if not cost_breakdown:
                # Fallback cost breakdown calculation
                cost_breakdown = self._calculate_cost_breakdown(
                    data['truck_count'], data['collection_frequency'], weekly_waste_kg, distance_km
                )
            
            return TruckRecommendation(
                truck_type=data['truck_type'],
                truck_count=data['truck_count'],
                total_capacity_kg=data['total_weekly_capacity_kg'],
                collection_frequency=data['collection_frequency'],
                weekly_operational_cost=data['weekly_operational_cost'],
                monthly_total_cost=data['monthly_total_cost'],
                cost_breakdown=cost_breakdown,
                efficiency_percent=data.get('efficiency_percent', 85.0),
                reasoning=data['reasoning'],
                mathematical_validation=data.get('mathematical_validation', 
                    f"Weekly capacity {data['total_weekly_capacity_kg']:,} kg ≥ Weekly waste {weekly_waste_kg:,.0f} kg")
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to parse Gemini response: {str(e)}")
            logger.debug(f"Raw response: {response_text}")
            return self._fallback_recommendation(weekly_waste_kg / 7)
    
    
    def _fallback_recommendation(self, daily_waste_kg: float) -> TruckRecommendation:
        """Fallback recommendation when Gemini fails"""
        weekly_waste_kg = daily_waste_kg * 7
        
        # Simple logic: use 25-tonne trucks with appropriate count
        truck_capacity = 25000
        collection_frequency = 1  # Start with once per week
        
        # Calculate trucks needed for weekly capacity
        trucks_needed = max(1, int((weekly_waste_kg + truck_capacity - 1) / truck_capacity))
        total_capacity = trucks_needed * truck_capacity
        
        # Calculate costs using standard formula
        cost_breakdown = self._calculate_cost_breakdown(
            trucks_needed, collection_frequency, weekly_waste_kg, 10.0  # Default 10km distance
        )
        
        weekly_operational_cost = cost_breakdown['weekly_fuel_cost'] + cost_breakdown['weekly_franchise_cost']
        monthly_total_cost = int(weekly_operational_cost * 4.33 + cost_breakdown['monthly_salaries'] + cost_breakdown['monthly_admin_overhead'])
        
        return TruckRecommendation(
            truck_type="25_tonne",
            truck_count=trucks_needed,
            total_capacity_kg=int(total_capacity),
            collection_frequency=collection_frequency,
            weekly_operational_cost=weekly_operational_cost,
            monthly_total_cost=monthly_total_cost,
            cost_breakdown=cost_breakdown,
            efficiency_percent=min(100.0, (weekly_waste_kg / total_capacity) * 100),
            reasoning=f"Fallback recommendation: {trucks_needed}x 25-tonne trucks with {collection_frequency}x weekly collection",
            mathematical_validation=f"Weekly capacity {total_capacity:,.0f} kg ≥ Weekly waste {weekly_waste_kg:,.0f} kg"
        )

# Global instance for easy import
gemini_engine = None

def initialize_gemini_engine(api_key: str = "AIzaSyCS1D1Fayd8ekwQE8NwberHPU-Xkaqcel4") -> GeminiRecommendationEngine:
    """Initialize global Gemini engine instance"""
    global gemini_engine
    try:
        gemini_engine = GeminiRecommendationEngine(api_key=api_key)
        return gemini_engine
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini engine: {str(e)}")
        return None

def get_gemini_recommendation(population: int, daily_waste_kg: float, 
                            distance_km: float, settlement_type: str = "mixed") -> Optional[TruckRecommendation]:
    """Get truck recommendation using Gemini AI"""
    if not gemini_engine:
        logger.warning("⚠️ Gemini engine not initialized, using fallback")
        return None
    
    try:
        return gemini_engine.generate_truck_recommendation(
            population, daily_waste_kg, distance_km, settlement_type
        )
    except Exception as e:
        logger.error(f"❌ Gemini recommendation failed: {str(e)}")
        return None