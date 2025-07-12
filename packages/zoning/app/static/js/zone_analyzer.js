/**
 * Real-time Zone Analysis JavaScript
 * Provides immediate feedback when users draw zones
 */

console.log('[ZoneAnalyzer] Script loading...');

class ZoneAnalyzer {
    constructor(map, options = {}) {
        console.log('[ZoneAnalyzer] Initializing with options:', options);
        this.map = map;
        this.options = {
            enableRealTimeAnalysis: true,
            enableQuickValidation: true,
            analysisDelay: 2000,
            ...options
        };
        
        this.currentZone = null;
        this.analysisTimeout = null;
        this.isAnalyzing = false;
        this.panel = null;
        
        this.init();
    }
    
    init() {
        console.log('[ZoneAnalyzer] Init called');
        this.createAnalysisPanel();
        this.setupEventListeners();
    }
    
    createAnalysisPanel() {
        console.log('[ZoneAnalyzer] Creating analysis panel...');
        // Create analysis results panel
        const panel = document.createElement('div');
        panel.id = 'zone-analysis-panel';
        panel.className = 'analysis-panel';
        panel.innerHTML = `
            <div class="analysis-header">
                <h3>Zone Analysis</h3>
                <div class="analysis-status">
                    <span class="status-indicator" id="analysis-status">Ready</span>
                </div>
            </div>
            
            <div class="analysis-content" id="analysis-content">
                <div class="no-zone-message">
                    Draw a zone on the map to see analysis results
                </div>
            </div>
            
            <div class="analysis-actions" id="analysis-actions" style="display: none;">
                <button class="btn btn-primary" onclick="zoneAnalyzer.saveZone()">Save Zone</button>
                <button class="btn btn-secondary" onclick="zoneAnalyzer.adjustZone()">Adjust Zone</button>
                <button class="btn btn-warning" onclick="zoneAnalyzer.clearZone()">Clear Zone</button>
            </div>
        `;
        
        // Add CSS styles
        const style = document.createElement('style');
        style.textContent = `
            .analysis-panel {
                position: fixed;
                top: 20px;
                right: 20px;
                width: 350px;
                max-height: 80vh;
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 1000;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .analysis-header {
                background: #2c3e50;
                color: white;
                padding: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .analysis-header h3 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }
            
            .status-indicator {
                background: #95a5a6;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }
            
            .status-indicator.analyzing {
                background: #f39c12;
                animation: pulse 1.5s infinite;
            }
            
            .status-indicator.complete {
                background: #27ae60;
            }
            
            .status-indicator.error {
                background: #e74c3c;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.6; }
            }
            
            .analysis-content {
                padding: 15px;
                max-height: 500px;
                overflow-y: auto;
            }
            
            .no-zone-message {
                text-align: center;
                color: #7f8c8d;
                padding: 20px;
                font-style: italic;
            }
            
            .viability-score {
                text-align: center;
                margin-bottom: 20px;
            }
            
            .score-circle {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                margin: 0 auto 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: bold;
                color: white;
            }
            
            .score-excellent { background: #27ae60; }
            .score-good { background: #f39c12; }
            .score-fair { background: #e67e22; }
            .score-poor { background: #e74c3c; }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin-bottom: 20px;
            }
            
            .metric-item {
                background: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                text-align: center;
            }
            
            .metric-value {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
            }
            
            .metric-label {
                font-size: 12px;
                color: #7f8c8d;
                margin-top: 2px;
            }
            
            .recommendations {
                margin-bottom: 20px;
            }
            
            .recommendations h4 {
                font-size: 14px;
                margin-bottom: 10px;
                color: #2c3e50;
            }
            
            .recommendation-item {
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 10px;
                margin-bottom: 8px;
                border-radius: 0 4px 4px 0;
                font-size: 13px;
            }
            
            .recommendation-item.high-priority {
                background: #f8d7da;
                border-left-color: #dc3545;
            }
            
            .recommendation-item.critical {
                background: #f5c6cb;
                border-left-color: #721c24;
            }
            
            .revenue-projections {
                margin-bottom: 20px;
                background: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 6px;
                padding: 15px;
            }
            
            .revenue-overview {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 15px;
            }
            
            .revenue-metric {
                text-align: center;
                padding: 10px;
                background: white;
                border-radius: 4px;
                border: 1px solid #28a745;
            }
            
            .revenue-value {
                font-size: 24px;
                font-weight: bold;
                color: #28a745;
                margin-bottom: 5px;
            }
            
            .revenue-label {
                font-size: 12px;
                color: #6c757d;
                text-transform: uppercase;
                font-weight: 500;
            }
            
            .revenue-details {
                border-top: 1px solid #c3e6cb;
                padding-top: 10px;
            }
            
            /* AI-Powered Recommendation Styles */
            .ai-recommendation {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            
            .ai-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                padding-bottom: 10px;
            }
            
            .ai-header h5 {
                margin: 0;
                font-size: 18px;
                font-weight: 600;
            }
            
            .ai-badge {
                background: rgba(255, 255, 255, 0.2);
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
                backdrop-filter: blur(10px);
            }
            
            .ai-recommendation .solution-header strong {
                color: #fff;
                font-size: 16px;
            }
            
            .ai-recommendation .detail-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                padding: 5px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .ai-recommendation .detail-row:last-child {
                border-bottom: none;
            }
            
            .ai-reasoning {
                margin-top: 15px;
                padding: 15px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                backdrop-filter: blur(10px);
            }
            
            .ai-reasoning h6 {
                margin: 0 0 10px 0;
                font-size: 14px;
                font-weight: 600;
            }
            
            .ai-reasoning p {
                margin: 0;
                line-height: 1.4;
                font-size: 13px;
            }
            
            .math-validation {
                margin-top: 10px;
                padding: 10px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                border-left: 3px solid #28a745;
            }
            
            .math-validation h6 {
                margin: 0 0 5px 0;
                font-size: 12px;
                font-weight: 600;
                color: #90ee90;
            }
            
            .math-validation p {
                margin: 0;
                font-size: 11px;
                opacity: 0.9;
                line-height: 1.3;
            }
            
            .fallback-recommendation {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
            }
            
            .revenue-breakdown {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                font-size: 13px;
            }
            
            .revenue-potential.high {
                color: #28a745;
                font-weight: bold;
            }
            
            .revenue-potential.medium {
                color: #ffc107;
                font-weight: bold;
            }
            
            .revenue-potential.low {
                color: #dc3545;
                font-weight: bold;
            }
            
            .enhanced-estimates-banner {
                border-left: 4px solid #28a745 !important;
                margin-bottom: 15px;
            }
            
            .enhanced-estimates-banner .fas {
                color: #28a745;
            }
            
            .truck-requirements-section {
                margin-bottom: 20px;
            }
            
            .truck-requirements-section h4 {
                font-size: 14px;
                margin-bottom: 12px;
                color: #2c3e50;
            }
            
            .recommended-solution {
                background: #e8f5e8;
                border: 1px solid #d4edda;
                border-radius: 6px;
                padding: 12px;
                margin-bottom: 12px;
            }
            
            .solution-header {
                font-size: 14px;
                color: #155724;
                margin-bottom: 8px;
            }
            
            .solution-details {
                font-size: 12px;
            }
            
            .detail-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 4px;
                color: #2c3e50;
            }
            
            .justification {
                margin-top: 8px;
                padding-top: 8px;
                border-top: 1px solid #c3e6cb;
                font-size: 11px;
                color: #495057;
            }
            
            .truck-comparison {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }
            
            .truck-option {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                text-align: center;
            }
            
            .truck-option h5 {
                font-size: 12px;
                margin: 0 0 6px 0;
                color: #495057;
            }
            
            .truck-details {
                font-size: 11px;
                color: #6c757d;
            }
            
            .truck-details div {
                margin-bottom: 2px;
            }
            
            .analysis-actions {
                padding: 15px;
                background: #f8f9fa;
                border-top: 1px solid #dee2e6;
                display: flex;
                gap: 8px;
            }
            
            .analysis-actions .btn {
                flex: 1;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            
            .btn-primary {
                background: #007bff;
                color: white;
            }
            
            .btn-primary:hover {
                background: #0056b3;
            }
            
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            
            .btn-secondary:hover {
                background: #545b62;
            }
            
            .btn-warning {
                background: #ffc107;
                color: #212529;
            }
            
            .btn-warning:hover {
                background: #e0a800;
            }
            
            .loading-spinner {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #3498db;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 8px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(panel);
        
        this.panel = panel;
        console.log('[ZoneAnalyzer] Panel created and appended to body. Panel visible:', panel.style.display, 'Panel element:', panel);
    }
    
    setupEventListeners() {
        // Listen for map drawing events
        if (this.map.drawControl) {
            this.map.on('draw:created', (e) => this.onZoneDrawn(e));
            this.map.on('draw:edited', (e) => this.onZoneEdited(e));
            this.map.on('draw:deleted', (e) => this.onZoneDeleted(e));
        }
    }
    
    onZoneDrawn(e) {
        this.currentZone = e.layer;
        this.triggerAnalysis();
    }
    
    onZoneEdited(e) {
        if (this.currentZone) {
            this.triggerAnalysis();
        }
    }
    
    onZoneDeleted(e) {
        this.currentZone = null;
        this.clearAnalysis();
    }
    
    triggerAnalysis() {
        if (!this.options.enableRealTimeAnalysis || !this.currentZone) {
            return;
        }
        
        // Clear existing timeout
        if (this.analysisTimeout) {
            clearTimeout(this.analysisTimeout);
        }
        
        // Set new timeout to debounce analysis
        this.analysisTimeout = setTimeout(() => {
            this.performAnalysis();
        }, this.options.analysisDelay);
    }
    
    async performAnalysis() {
        if (this.isAnalyzing || !this.currentZone) {
            return;
        }
        
        this.isAnalyzing = true;
        this.updateStatus('analyzing', 'Analyzing...');
        
        try {
            // Get zone geometry
            const geometry = this.currentZone.toGeoJSON();
            
            // Perform quick validation first
            if (this.options.enableQuickValidation) {
                await this.performQuickValidation(geometry);
            }
            
            // Perform full analysis
            const response = await fetch('/zones/api/analyze-zone', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    geometry: geometry,
                    metadata: this.getZoneMetadata(),
                    session_id: this.getSessionId()
                })
            });
            
            if (!response.ok) {
                throw new Error(`Analysis failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.displayAnalysisResults(result);
                await this.loadDashboardData(result);
                this.updateStatus('complete', 'Analysis Complete');
            } else {
                throw new Error(result.error || 'Analysis failed');
            }
            
        } catch (error) {
            console.error('Analysis error:', error);
            this.displayError(error.message);
            this.updateStatus('error', 'Analysis Failed');
        } finally {
            this.isAnalyzing = false;
        }
    }
    
    async performQuickValidation(geometry) {
        try {
            const response = await fetch('/zones/api/validate-zone-boundary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ geometry: geometry })
            });
            
            if (response.ok) {
                const validation = await response.json();
                this.displayQuickValidation(validation);
            }
        } catch (error) {
            console.warn('Quick validation failed:', error);
        }
    }
    
    displayQuickValidation(validation) {
        const content = document.getElementById('analysis-content');
        
        const html = `
            <div class="quick-validation">
                <h4>Quick Validation</h4>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value">${validation.area_sqkm.toFixed(2)}</div>
                        <div class="metric-label">Area (km²)</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">${validation.compactness_score}%</div>
                        <div class="metric-label">Compactness</div>
                    </div>
                </div>
                <div class="size-assessment">
                    <strong>Size Assessment:</strong> ${validation.size_assessment}
                </div>
                ${validation.quick_recommendations.length > 0 ? `
                    <div class="quick-recommendations">
                        <h5>Quick Tips:</h5>
                        ${validation.quick_recommendations.map(rec => 
                            `<div class="recommendation-item">${rec}</div>`
                        ).join('')}
                    </div>
                ` : ''}
                <div class="full-analysis-notice">
                    <span class="loading-spinner"></span>
                    Running full analysis...
                </div>
            </div>
        `;
        
        content.innerHTML = html;
    }
    
    displayAnalysisResults(result) {
        const analysis = result.analysis;
        const content = document.getElementById('analysis-content');
        const actions = document.getElementById('analysis-actions');
        
        // Build viability score display
        const score = analysis.zone_viability_score || 0;
        const scoreClass = this.getScoreClass(score);
        const scoreLabel = this.getScoreLabel(score);
        
        // Build metrics from analysis
        const geometry = analysis.analysis_modules?.geometry || {};
        const population = analysis.analysis_modules?.population || {};
        const feasibility = analysis.analysis_modules?.collection_feasibility || {};
        const truckRequirements = feasibility.truck_requirements || {};
        const recommended = truckRequirements.recommended_solution || {};
        
        // Debug logging
        console.log('[ZoneAnalyzer] Truck requirements:', {
            ai_powered: truckRequirements.ai_powered,
            recommended_fleet: truckRequirements.recommended_fleet,
            gemini_reasoning: truckRequirements.gemini_reasoning ? 'Present' : 'Missing',
            weekly_operational_cost: truckRequirements.weekly_operational_cost,
            monthly_cost: truckRequirements.monthly_cost,
            mathematical_validation: truckRequirements.mathematical_validation ? 'Present' : 'Missing'
        });
        console.log('[ZoneAnalyzer] Full truck requirements object:', truckRequirements);
        
        // Check for enhanced estimates mode or offline mode
        let statusBanner = '';
        if (analysis.enhanced_estimates_mode) {
            const enhancedComponents = analysis.enhanced_components || [];
            const earthEngineData = analysis.analysis_modules?.earth_engine || {};
            
            statusBanner = `
                <div class="enhanced-estimates-banner alert alert-success">
                    <i class="fas fa-chart-area"></i>
                    <strong>Enhanced Estimates Active:</strong> Using advanced area-based modeling for: ${enhancedComponents.join(', ')}
                    <small class="d-block">High-quality results based on Lusaka urban patterns and zone characteristics.</small>
                    ${earthEngineData.user_message ? `<small class="d-block mt-1 text-muted">${earthEngineData.user_message}</small>` : ''}
                </div>
            `;
        } else if (analysis.offline_mode) {
            const offlineComponents = analysis.offline_components || [];
            const earthEngineData = analysis.analysis_modules?.earth_engine || {};
            
            // Check if we have enhanced estimates (less concerning than basic offline)
            const hasEnhancedEstimates = earthEngineData.data_source === 'enhanced_estimates';
            
            if (hasEnhancedEstimates) {
                statusBanner = `
                    <div class="offline-banner alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        <strong>Enhanced Estimates:</strong> Using area-based modeling for: ${offlineComponents.join(', ')}
                        <small class="d-block">Results based on Lusaka urban patterns and zone characteristics.</small>
                        ${earthEngineData.quality_note ? `<small class="d-block mt-1 text-muted">${earthEngineData.quality_note}</small>` : ''}
                    </div>
                `;
            } else {
                statusBanner = `
                    <div class="offline-banner alert alert-warning">
                        <i class="fas fa-wifi-slash"></i>
                        <strong>Offline Mode:</strong> Some services unavailable. Using estimates for: ${offlineComponents.join(', ')}
                        <small class="d-block">Results may be less accurate than usual.</small>
                    </div>
                `;
            }
        }

        const html = `
            ${statusBanner}
            <div class="viability-score">
                <div class="score-circle ${scoreClass}">
                    ${Math.round(score)}%
                </div>
                <div class="score-label">${scoreLabel}</div>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">${(geometry.area_sqkm || 0).toFixed(2)}</div>
                    <div class="metric-label">Area (km²)</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">${Math.round(population.consensus || 0).toLocaleString()}</div>
                    <div class="metric-label">Est. Population</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">${Math.round(geometry.compactness_index * 100 || 0)}%</div>
                    <div class="metric-label">Compactness</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">${Math.round(feasibility.overall_score || 0)}%</div>
                    <div class="metric-label">Feasibility</div>
                </div>
            </div>
            
            ${!truckRequirements.error ? `
                <div class="truck-requirements-section">
                    <h4>🚛 Complete Collection Analysis</h4>
                    
                    <!-- Waste Generation Summary -->
                    <div class="waste-generation-summary">
                        <h5>📊 Waste Generation</h5>
                        <div class="metric-row">
                            <span>Population:</span>
                            <strong>${(truckRequirements.waste_generation?.estimated_population || 0).toLocaleString()}</strong>
                        </div>
                        <div class="metric-row">
                            <span>Daily waste:</span>
                            <strong>${(truckRequirements.waste_generation?.daily_waste_kg || 0).toFixed(0)} kg</strong>
                        </div>
                        <div class="metric-row">
                            <span>Weekly waste:</span>
                            <strong>${(truckRequirements.waste_generation?.weekly_waste_tonnes || 0).toFixed(1)} tonnes</strong>
                        </div>
                    </div>
                    
                    <!-- Chunga Dumpsite Logistics -->
                    <div class="dumpsite-logistics">
                        <h5>📍 Chunga Dumpsite Logistics</h5>
                        <div class="metric-row">
                            <span>Distance to Chunga:</span>
                            <strong>${(truckRequirements.dumpsite_logistics?.chunga_dumpsite_distance_km || 0).toFixed(1)} km</strong>
                        </div>
                        <div class="metric-row">
                            <span>Round trip distance:</span>
                            <strong>${(truckRequirements.dumpsite_logistics?.round_trip_distance_km || 0).toFixed(1)} km</strong>
                        </div>
                        <div class="metric-row">
                            <span>Fuel cost:</span>
                            <strong>K${((truckRequirements.dumpsite_logistics?.fuel_price_usd_per_liter || 0) * 27).toFixed(0)}/liter</strong>
                        </div>
                        <div class="metric-row">
                            <span>Franchise fee:</span>
                            <strong>K${truckRequirements.dumpsite_logistics?.franchise_cost_kwacha_per_tonne || 50}/tonne</strong>
                        </div>
                    </div>
                    
                    <div class="truck-summary">
                        <!-- Debug info: AI powered = ${truckRequirements.ai_powered} -->
                        <!-- Debug data: ${JSON.stringify({
                            ai_powered: truckRequirements.ai_powered,
                            weekly_operational_cost: truckRequirements.weekly_operational_cost,
                            monthly_cost: truckRequirements.monthly_cost,
                            recommended_fleet: truckRequirements.recommended_fleet
                        }, null, 2)} -->
                        ${truckRequirements.ai_powered ? `
                            <div class="ai-recommendation">
                                <div class="ai-header">
                                    <h5>🤖 AI-Powered Recommendation</h5>
                                    <span class="ai-badge">Gemini Flash</span>
                                </div>
                                <div class="solution-header">
                                    <strong>💡 Recommended: ${truckRequirements.recommended_fleet || 'Calculating...'}</strong>
                                </div>
                                <div class="solution-details">
                                    <div class="detail-row">
                                        <span>Collections per week:</span>
                                        <strong>${truckRequirements.vehicle_requirements?.frequency_per_week || truckRequirements.frequency_per_week || 2} times</strong>
                                    </div>
                                    <div class="detail-row">
                                        <span>Total capacity provided:</span>
                                        <strong>${(truckRequirements.total_capacity_provided / 1000).toFixed(1)} tonnes/week</strong>
                                    </div>
                                    <div class="detail-row">
                                        <span>Collection coverage:</span>
                                        <strong>${truckRequirements.collection_coverage || '100%'}</strong>
                                    </div>
                                    <div class="detail-row">
                                        <span>Weekly operational cost:</span>
                                        <strong>K${(truckRequirements.weekly_operational_cost || 0).toLocaleString()}</strong>
                                    </div>
                                    <div class="detail-row">
                                        <span>Monthly total cost:</span>
                                        <strong>K${(truckRequirements.monthly_cost || 0).toLocaleString()}</strong>
                                    </div>
                                </div>
                                ${truckRequirements.gemini_reasoning ? `
                                    <div class="ai-reasoning">
                                        <h6>🧠 AI Analysis:</h6>
                                        <p><em>${truckRequirements.gemini_reasoning}</em></p>
                                    </div>
                                ` : ''}
                                ${truckRequirements.mathematical_validation ? `
                                    <div class="math-validation">
                                        <h6>🧮 Mathematical Validation:</h6>
                                        <p><small>${truckRequirements.mathematical_validation}</small></p>
                                    </div>
                                ` : ''}
                            </div>
                        ` : `
                            <div class="fallback-recommendation">
                                <div class="solution-header">
                                    <strong>💡 Recommended: ${recommended.trucks_needed || 1} × ${recommended.truck_type?.replace('_', '-')?.toUpperCase() || 'TRUCK'}(S)</strong>
                                </div>
                                <div class="solution-details">
                                    <div class="detail-row">
                                        <span>Collections per week:</span>
                                        <strong>${recommended.collections_per_week || 2} times</strong>
                                    </div>
                                    <div class="detail-row">
                                        <span>Weekly operational cost:</span>
                                        <strong>K${(recommended.weekly_operational_cost || 0).toLocaleString()}</strong>
                                    </div>
                                    <div class="detail-row">
                                        <span>Monthly total cost:</span>
                                        <strong>K${(recommended.monthly_cost || 0).toLocaleString()}</strong>
                                    </div>
                                </div>
                            </div>
                        `}
                    </div>
                </div>
            ` : ''}
            
${result.revenue_projections && result.revenue_projections.success ? `
                <div class="revenue-projections">
                    <h4>💰 Revenue Projections</h4>
                    
                    ${result.area_config ? `
                        <div class="area-config-display mb-3" style="background: #f8f9fa; border-radius: 6px; padding: 12px;">
                            <h6 style="margin: 0 0 8px 0; color: #495057;">
                                <i class="fas fa-map-marker-alt"></i> Area Configuration
                            </h6>
                            <div class="config-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
                                <div><strong>Zone Type:</strong> ${(result.area_config.zone_type || 'mixed_use').replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}</div>
                                <div><strong>Settlement Density:</strong> ${(result.area_config.settlement_density || 'medium_density').replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}</div>
                                <div><strong>Economic Level:</strong> ${(result.area_config.socioeconomic_level || 'mixed_income').replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}</div>
                                <div><strong>Household Rate:</strong> K${result.area_config.average_household_charge || 150}/month</div>
                                ${result.area_config.waste_generation_rate ? `<div style="grid-column: span 2;"><strong>Custom Waste Rate:</strong> ${result.area_config.waste_generation_rate} kg/person/day</div>` : ''}
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="revenue-overview">
                        <div class="revenue-metric">
                            <div class="revenue-value">K${result.revenue_projections.realistic_monthly_revenue_kwacha.toLocaleString()}</div>
                            <div class="revenue-label">Monthly Revenue (${result.revenue_projections.collection_efficiency_percent.toFixed(0)}% collection rate)</div>
                        </div>
                        <div class="revenue-metric">
                            <div class="revenue-value">K${result.revenue_projections.realistic_annual_revenue_kwacha.toLocaleString()}</div>
                            <div class="revenue-label">Annual Revenue</div>
                        </div>
                    </div>
                    <div class="revenue-details">
                        <div class="revenue-breakdown">
                            <div><strong>Settlement Type:</strong> ${result.revenue_projections.settlement_description}</div>
                            <div><strong>Total Buildings:</strong> ${result.revenue_projections.total_buildings}</div>
                            <div><strong>Rate per Building:</strong> K${result.revenue_projections.rate_per_building_kwacha}/month</div>
                            <div><strong>Revenue Potential:</strong> <span class="revenue-potential ${result.revenue_projections.revenue_potential}">${result.revenue_projections.revenue_potential.toUpperCase()}</span></div>
                        </div>
                    </div>
                </div>
            ` : ''}
            
            ${result.recommendations && result.recommendations.length > 0 ? `
                <div class="recommendations">
                    <h4>💡 Recommendations</h4>
                    ${result.recommendations.slice(0, 5).map(rec => `
                        <div class="recommendation-item ${rec.priority}-priority">
                            <strong>${rec.issue}</strong><br>
                            ${rec.recommendation}
                            ${rec.impact ? `<br><em>Impact: ${rec.impact}</em>` : ''}
                        </div>
                    `).join('')}
                    ${result.recommendations.length > 5 ? `
                        <div class="more-recommendations">
                            +${result.recommendations.length - 5} more recommendations
                        </div>
                    ` : ''}
                </div>
            ` : ''}
            
            <div class="analysis-summary">
                <small>
                    Analysis completed in ${analysis.performance_metrics?.total_analysis_time_seconds || 0}s
                    | ${analysis.performance_metrics?.modules_completed || 0} modules successful
                </small>
            </div>
        `;
        
        content.innerHTML = html;
        actions.style.display = 'flex';
    }
    
    displayError(message) {
        const content = document.getElementById('analysis-content');
        content.innerHTML = `
            <div class="error-message">
                <h4>❌ Analysis Error</h4>
                <p>${message}</p>
                <button class="btn btn-secondary" onclick="zoneAnalyzer.retryAnalysis()">
                    Retry Analysis
                </button>
            </div>
        `;
    }
    
    clearAnalysis() {
        const content = document.getElementById('analysis-content');
        const actions = document.getElementById('analysis-actions');
        
        content.innerHTML = `
            <div class="no-zone-message">
                Draw a zone on the map to see analysis results
            </div>
        `;
        
        actions.style.display = 'none';
        
        // Hide enhanced analytics panels
        const analyticsPanel = document.getElementById('analytics-panel');
        const recommendationsPanel = document.getElementById('recommendations-panel');
        
        if (analyticsPanel) analyticsPanel.style.display = 'none';
        if (recommendationsPanel) recommendationsPanel.style.display = 'none';
        
        this.updateStatus('ready', 'Ready');
    }
    
    updateStatus(type, text) {
        const statusIndicator = document.getElementById('analysis-status');
        statusIndicator.textContent = text;
        statusIndicator.className = `status-indicator ${type}`;
    }
    
    getScoreClass(score) {
        if (score >= 80) return 'score-excellent';
        if (score >= 60) return 'score-good';
        if (score >= 40) return 'score-fair';
        return 'score-poor';
    }
    
    getScoreLabel(score) {
        if (score >= 80) return 'Excellent Zone';
        if (score >= 60) return 'Good Zone';
        if (score >= 40) return 'Fair Zone';
        return 'Needs Improvement';
    }
    
    getZoneMetadata() {
        // Get additional metadata from form or UI if available
        const metadata = {
            zone_type: 'mixed_use', // Default
            estimated_population: null,
            collection_frequency: 2
        };
        
        // Try to get values from form fields if they exist
        try {
            const zoneTypeEl = document.getElementById('zone_type');
            if (zoneTypeEl && zoneTypeEl.value) {
                metadata.zone_type = zoneTypeEl.value.toLowerCase();
            }
            
            const settlementDensityEl = document.getElementById('settlement_density');
            if (settlementDensityEl && settlementDensityEl.value) {
                metadata.settlement_density = settlementDensityEl.value;
            }
            
            const socioeconomicLevelEl = document.getElementById('socioeconomic_level');
            if (socioeconomicLevelEl && socioeconomicLevelEl.value) {
                metadata.socioeconomic_level = socioeconomicLevelEl.value;
            }
            
            const householdChargeEl = document.getElementById('average_household_charge');
            if (householdChargeEl && householdChargeEl.value) {
                metadata.average_household_charge = parseFloat(householdChargeEl.value);
            }
            
            const wasteRateEl = document.getElementById('waste_generation_rate');
            if (wasteRateEl && wasteRateEl.value) {
                metadata.waste_generation_rate = parseFloat(wasteRateEl.value);
            }
            
            const populationEl = document.getElementById('estimated_population');
            if (populationEl && populationEl.value) {
                metadata.estimated_population = parseInt(populationEl.value);
            }
            
            const frequencyEl = document.getElementById('collection_frequency_week');
            if (frequencyEl && frequencyEl.value) {
                metadata.collection_frequency = parseInt(frequencyEl.value);
            }
            
        } catch (e) {
            console.warn('Could not read form metadata:', e);
        }
        
        return metadata;
    }
    
    // Action methods
    saveZone() {
        if (!this.currentZone) {
            alert('No zone to save');
            return;
        }
        
        // Redirect to zone creation form with geometry
        const geometry = this.currentZone.toGeoJSON();
        localStorage.setItem('pending_zone_geometry', JSON.stringify(geometry));
        window.location.href = '/zones/create';
    }
    
    adjustZone() {
        // Enable edit mode for the current zone
        if (this.currentZone && this.map.editTools) {
            this.map.editTools.startEditing(this.currentZone);
        }
    }
    
    clearZone() {
        if (this.currentZone) {
            this.map.removeLayer(this.currentZone);
            this.currentZone = null;
            this.clearAnalysis();
        }
    }
    
    async loadDashboardData(analysisResult) {
        try {
            console.log('[ZoneAnalyzer] Loading dashboard data for analysis:', analysisResult);
            
            // Request enhanced dashboard data
            const response = await fetch('/zones/api/dashboard-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    analysis: analysisResult.analysis
                })
            });
            
            if (response.ok) {
                const dashboardData = await response.json();
                console.log('[ZoneAnalyzer] Dashboard data received:', dashboardData);
                
                if (dashboardData.success) {
                    this.displayDashboardData(dashboardData);
                    // Recommendations are already displayed in displayAnalysisResults
                } else {
                    console.warn('[ZoneAnalyzer] Dashboard data generation failed:', dashboardData.error);
                }
            } else {
                console.warn('[ZoneAnalyzer] Dashboard data request failed:', response.status, response.statusText);
            }
        } catch (error) {
            console.warn('[ZoneAnalyzer] Failed to load dashboard data:', error);
        }
    }
    
    displayDashboardData(dashboardData) {
        console.log('[ZoneAnalyzer] Displaying dashboard data:', dashboardData);
        // Find the actual analysis content element from the panel we created
        const content = document.getElementById('analysis-content');
        const data = dashboardData.dashboard_data;
        
        if (!content) {
            console.error('[ZoneAnalyzer] analysis-content element not found!');
            return;
        }
        
        if (!data) {
            console.warn('[ZoneAnalyzer] No dashboard data available');
            // Don't overwrite the existing analysis results
            return;
        }
        
        const keyMetrics = data.key_metrics || {};
        const qualityIndicators = data.quality_indicators || {};
        
        // Debug logging
        console.log('[ZoneAnalyzer] Key metrics:', keyMetrics);
        console.log('[ZoneAnalyzer] Daily waste:', keyMetrics.daily_waste, 'Total waste kg/day:', keyMetrics.total_waste_kg_day);
        console.log('[ZoneAnalyzer] Trucks needed:', keyMetrics.trucks_needed, 'Vehicles required:', keyMetrics.vehicles_required);
        
        // Get the existing analysis HTML and append dashboard data
        const existingContent = content.innerHTML;
        
        // Create a separate dashboard metrics section
        const dashboardMetricsHtml = `
            <div class="dashboard-metrics-section" style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <h4 style="font-size: 14px; margin-bottom: 15px; color: #2c3e50;">
                    <i class="fas fa-chart-line"></i> Real-Time Analytics
                </h4>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                    <div style="background: white; padding: 12px; border-radius: 6px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="font-size: 20px; font-weight: bold; color: #2c3e50;">${(keyMetrics.estimated_population || 0).toLocaleString()}</div>
                        <div style="font-size: 12px; color: #7f8c8d; margin-top: 4px;">Population</div>
                    </div>
                    <div style="background: white; padding: 12px; border-radius: 6px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="font-size: 20px; font-weight: bold; color: #2c3e50;">${(keyMetrics.daily_waste || keyMetrics.total_waste_kg_day || 0).toFixed(1)} kg</div>
                        <div style="font-size: 12px; color: #7f8c8d; margin-top: 4px;">Daily Waste</div>
                    </div>
                    <div style="background: white; padding: 12px; border-radius: 6px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="font-size: 20px; font-weight: bold; color: #2c3e50;">${keyMetrics.building_count || 0}</div>
                        <div style="font-size: 12px; color: #7f8c8d; margin-top: 4px;">Buildings</div>
                    </div>
                    <div style="background: white; padding: 12px; border-radius: 6px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="font-size: 20px; font-weight: bold; color: #2c3e50;">${(keyMetrics.trucks_needed || keyMetrics.vehicles_required || keyMetrics.trucks_required || 0)}</div>
                        <div style="font-size: 12px; color: #7f8c8d; margin-top: 4px;">Trucks Needed</div>
                    </div>
                </div>
                
                <div class="quality-indicators">
                    <h5 style="font-size: 13px; margin-bottom: 12px; color: #2c3e50;">Quality Assessment</h5>
                    ${this.renderQualityIndicator('Data Quality', qualityIndicators.overall_quality || 0)}
                    ${this.renderQualityIndicator('Population Confidence', qualityIndicators.population_confidence || 0)}
                    ${this.renderQualityIndicator('Collection Feasibility', qualityIndicators.collection_feasibility || 0)}
                </div>
                
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #dee2e6;">
                    ${dashboardData.enhanced_estimates_mode ? 
                        '<div style="color: #28a745; font-size: 12px;"><i class="fas fa-chart-area"></i> Enhanced by DashboardCore</div>' : 
                        dashboardData.offline_mode ? 
                        '<div style="color: #17a2b8; font-size: 12px;"><i class="fas fa-info-circle"></i> Enhanced by DashboardCore</div>' : 
                        '<div style="color: #6c757d; font-size: 12px;"><i class="fas fa-chart-line"></i> Enhanced by DashboardCore</div>'}
                </div>
            </div>
        `;
        
        // Find where to insert the dashboard metrics - after the main analysis results
        // Look for the truck requirements section or recommendations section
        const insertionPoint = existingContent.indexOf('<div class="recommendations">');
        if (insertionPoint > -1) {
            // Insert before recommendations
            content.innerHTML = existingContent.slice(0, insertionPoint) + dashboardMetricsHtml + existingContent.slice(insertionPoint);
        } else {
            // Just append at the end
            content.innerHTML = existingContent + dashboardMetricsHtml;
        }
    }
    
    renderQualityIndicator(label, value) {
        const percentage = Math.round(value * 100);
        const colorClass = percentage >= 80 ? 'success' : percentage >= 60 ? 'warning' : 'danger';
        
        return `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <small>${label}</small>
                <small class="text-${colorClass}">${percentage}%</small>
            </div>
            <div class="progress mb-2" style="height: 4px;">
                <div class="progress-bar bg-${colorClass}" style="width: ${percentage}%"></div>
            </div>
        `;
    }
    
    displayRecommendations(analysisResult) {
        const panel = document.getElementById('recommendations-panel');
        const content = document.getElementById('recommendations-content');
        
        const recommendations = analysisResult.recommendations || [];
        const revenueProjections = analysisResult.revenue_projections || {};
        
        if (recommendations.length === 0 && !revenueProjections.success) {
            panel.style.display = 'none';
            return;
        }
        
        panel.style.display = 'block';
        
        let html = '';
        
        if (revenueProjections.success) {
            html += '<div class="mb-3"><h6 class="text-success mb-2"><i class="fas fa-dollar-sign"></i> Revenue Projections</h6>';
            html += `<div class="alert alert-success py-2 px-3 mb-1">
                <small>
                    <strong>Monthly Revenue:</strong> K${revenueProjections.realistic_monthly_revenue_kwacha?.toLocaleString() || 0} 
                    (${revenueProjections.total_buildings || 0} buildings × K${revenueProjections.rate_per_building_kwacha || 0})
                </small>
            </div>`;
            html += `<div class="alert alert-info py-2 px-3 mb-1">
                <small>
                    <strong>Settlement:</strong> ${revenueProjections.settlement_description || 'Unknown'} - 
                    <strong>Potential:</strong> ${(revenueProjections.revenue_potential || 'unknown').toUpperCase()}
                </small>
            </div>`;
            html += '</div>';
        }
        
        if (recommendations.length > 0) {
            html += '<div><h6 class="text-primary mb-2"><i class="fas fa-lightbulb"></i> Recommendations</h6>';
            recommendations.forEach(rec => {
                html += `<div class="alert alert-info py-2 px-3 mb-1"><small>${rec}</small></div>`;
            });
            html += '</div>';
        }
        
        content.innerHTML = html;
    }
    
    getSessionId() {
        // Get or create session ID for persisting analysis results
        let sessionId = sessionStorage.getItem('zoneAnalysisSessionId');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('zoneAnalysisSessionId', sessionId);
        }
        return sessionId;
    }
    
    retryAnalysis() {
        if (this.currentZone) {
            this.performAnalysis();
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on a map page
    if (typeof map !== 'undefined' && map) {
        window.zoneAnalyzer = new ZoneAnalyzer(map, {
            enableRealTimeAnalysis: true,
            enableQuickValidation: true,
            analysisDelay: 2000 // 2 second delay for better UX
        });
    }
}); 