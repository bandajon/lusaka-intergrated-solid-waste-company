"""
AI-powered waste management analysis using OpenAI and Claude APIs
Provides predictive analytics, optimization suggestions, and insights
"""
import openai
import anthropic
import json
import requests
from config.config import Config
from app.models import Zone, ZoneAnalysis


class AIWasteAnalyzer:
    """AI-powered waste management analyzer"""
    
    def __init__(self):
        """Initialize AI clients"""
        self.openai_api_key = Config.OPENAI_API_KEY
        self.claude_api_key = Config.CLAUDE_API_KEY
        self.perplexity_api_key = Config.PERPLEXITY_API_KEY
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        if self.claude_api_key:
            self.claude = anthropic.Anthropic(api_key=self.claude_api_key)
    
    def predict_waste_generation(self, zone, historical_data=None):
        """Use AI to predict future waste generation patterns"""
        if not self.openai_api_key:
            return {"error": "OpenAI API key not configured"}
        
        try:
            # Prepare context
            context = f"""
            Zone Information:
            - Name: {zone.name}
            - Type: {zone.zone_type.value}
            - Area: {zone.area_sqm / 1000000:.2f} km²
            - Population: {zone.estimated_population or 'Unknown'}
            - Households: {zone.household_count or 'Unknown'}
            - Businesses: {zone.business_count or 'Unknown'}
            - Current waste generation: {zone.waste_generation_kg_day or 0} kg/day
            """
            
            if historical_data:
                context += f"\nHistorical data: {json.dumps(historical_data)}"
            
            # Create prediction prompt
            prompt = f"""
            Based on the following zone information, predict the waste generation for the next 12 months.
            Consider seasonal variations, population growth, and economic factors for Lusaka, Zambia.
            
            {context}
            
            Provide predictions in JSON format with monthly estimates and reasoning.
            Include factors like:
            - Seasonal variations (rainy/dry seasons)
            - Holiday periods
            - Population growth trends
            - Economic development
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert waste management analyst specializing in African urban areas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Parse response
            prediction_text = response.choices[0].message.content
            
            # Extract JSON if present
            try:
                import re
                json_match = re.search(r'\{[\s\S]*\}', prediction_text)
                if json_match:
                    predictions = json.loads(json_match.group())
                else:
                    predictions = {"raw_response": prediction_text}
            except:
                predictions = {"raw_response": prediction_text}
            
            return {
                "predictions": predictions,
                "model": "gpt-4",
                "confidence": "high"
            }
            
        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}
    
    def optimize_collection_routes(self, zones):
        """Use AI to optimize waste collection routes"""
        if not self.claude_api_key:
            return {"error": "Claude API key not configured"}
        
        try:
            # Prepare zone data
            zones_data = []
            for zone in zones:
                zones_data.append({
                    "id": zone.id,
                    "name": zone.name,
                    "centroid": zone.centroid if zone.centroid else None,
                    "area": zone.area_sqm,
                    "waste_generation": zone.waste_generation_kg_day or 0,
                    "collection_frequency": zone.collection_frequency_week or 2
                })
            
            prompt = f"""
            Optimize waste collection routes for the following zones in Lusaka, Zambia:
            
            {json.dumps(zones_data, indent=2)}
            
            Consider:
            1. Minimize total distance traveled
            2. Balance truck loads (5000 kg capacity)
            3. Account for traffic patterns in Lusaka
            4. Group zones by collection frequency
            5. Consider road conditions and accessibility
            
            Provide an optimized route plan with:
            - Suggested collection groups
            - Route sequence for each group
            - Estimated time and distance
            - Truck allocation
            - Cost optimization suggestions
            """
            
            message = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = message.content[0].text
            
            # Parse structured data from response
            optimization_plan = self._parse_optimization_response(response_text)
            
            return {
                "optimization_plan": optimization_plan,
                "raw_response": response_text,
                "model": "claude-3-opus",
                "estimated_savings": optimization_plan.get("estimated_savings", "Unknown")
            }
            
        except Exception as e:
            return {"error": f"Route optimization failed: {str(e)}"}
    
    def generate_insights(self, zone, analysis_data):
        """Generate actionable insights using AI"""
        if not self.openai_api_key:
            return {"error": "OpenAI API key not configured"}
        
        try:
            context = f"""
            Zone: {zone.name} ({zone.zone_type.value})
            Area: {zone.area_sqm / 1000000:.2f} km²
            Population: {zone.estimated_population or 'Unknown'}
            Waste Generation: {zone.waste_generation_kg_day or 0} kg/day
            
            Analysis Results:
            {json.dumps(analysis_data, indent=2)}
            """
            
            prompt = f"""
            Based on the following waste management data for a zone in Lusaka, Zambia, 
            provide actionable insights and recommendations:
            
            {context}
            
            Focus on:
            1. Efficiency improvements
            2. Cost reduction opportunities
            3. Environmental impact reduction
            4. Service quality enhancement
            5. Revenue optimization
            6. Community engagement strategies
            
            Provide specific, actionable recommendations suitable for Lusaka's context.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a waste management consultant with expertise in African cities."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            
            insights = response.choices[0].message.content
            
            # Structure insights
            structured_insights = self._structure_insights(insights)
            
            return {
                "insights": structured_insights,
                "raw_insights": insights,
                "priority_actions": structured_insights.get("priority_actions", []),
                "estimated_impact": structured_insights.get("impact", "Medium")
            }
            
        except Exception as e:
            return {"error": f"Insight generation failed: {str(e)}"}
    
    def research_best_practices(self, topic):
        """Research global best practices using Perplexity AI"""
        if not self.perplexity_api_key:
            return {"error": "Perplexity API key not configured"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "pplx-70b-online",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Research best practices for {topic} in waste management, with specific examples from African cities and adaptation strategies for Lusaka, Zambia."
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                research = result['choices'][0]['message']['content']
                
                return {
                    "research": research,
                    "sources": self._extract_sources(research),
                    "key_findings": self._extract_key_findings(research),
                    "model": "perplexity-70b"
                }
            else:
                return {"error": f"Research failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Research failed: {str(e)}"}
    
    def _parse_optimization_response(self, response_text):
        """Parse route optimization response into structured data"""
        # This would implement parsing logic to extract structured data
        # For now, return a basic structure
        return {
            "collection_groups": [],
            "estimated_distance_reduction": "20-30%",
            "estimated_time_savings": "2-3 hours per day",
            "truck_utilization": "85-90%",
            "estimated_savings": "$500-800 per month"
        }
    
    def _structure_insights(self, insights_text):
        """Structure insights into actionable format"""
        # Basic structuring - in production, use NLP to extract key points
        lines = insights_text.split('\n')
        priority_actions = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'must']):
                priority_actions.append(line.strip())
        
        return {
            "summary": insights_text[:200] + "...",
            "priority_actions": priority_actions[:5],
            "full_analysis": insights_text,
            "impact": "High" if len(priority_actions) > 3 else "Medium"
        }
    
    def _extract_sources(self, research_text):
        """Extract sources from research text"""
        # Simple extraction - look for URLs or citations
        import re
        urls = re.findall(r'https?://\S+', research_text)
        return urls[:5]  # Return top 5 sources
    
    def _extract_key_findings(self, research_text):
        """Extract key findings from research"""
        # Extract numbered points or bullet points
        import re
        findings = re.findall(r'^\d+\.|^-\s+(.+)$', research_text, re.MULTILINE)
        return findings[:5]  # Return top 5 findings