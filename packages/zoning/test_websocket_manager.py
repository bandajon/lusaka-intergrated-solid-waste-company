"""
Test script for WebSocket Manager

This script demonstrates how to use the WebSocket manager for real-time analytics updates.
"""

import time
import threading
from flask import Flask
from flask_socketio import SocketIO
from app.utils.websocket_manager import WebSocketManager
from app.utils.websocket_integration import init_websocket, WebSocketEnabledZoneAnalyzer


def create_test_app():
    """Create a test Flask application with WebSocket support."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Initialize WebSocket support
    socketio, websocket_manager = init_websocket(app)
    
    return app, socketio, websocket_manager


def simulate_zone_analysis(websocket_manager, session_id):
    """Simulate a zone analysis with progressive updates."""
    print(f"Starting zone analysis simulation for session: {session_id}")
    
    # Create analyzer with WebSocket support
    analyzer = WebSocketEnabledZoneAnalyzer(
        websocket_manager=websocket_manager,
        session_id=session_id
    )
    
    # Simulate zone data
    zone_data = {
        'id': 'zone_123',
        'name': 'Test Zone',
        'geometry': {
            'type': 'Polygon',
            'coordinates': [[
                [-15.4, -8.6],
                [-15.3, -8.6],
                [-15.3, -8.5],
                [-15.4, -8.5],
                [-15.4, -8.6]
            ]]
        }
    }
    
    # Start analysis with real-time updates
    websocket_manager.send_analytics_update(
        session_id,
        'analysis_started',
        {
            'zone_id': zone_data['id'],
            'zone_name': zone_data['name'],
            'timestamp': time.time()
        }
    )
    
    # Simulate settlement detection
    for i in range(0, 101, 20):
        websocket_manager.send_progress_update(
            session_id,
            'settlement_detection',
            i,
            f'Analyzing satellite imagery... {i}%'
        )
        time.sleep(0.5)
    
    # Send settlement results
    settlements = [
        {'id': 1, 'type': 'formal', 'area_sqm': 5000},
        {'id': 2, 'type': 'informal', 'area_sqm': 3000},
        {'id': 3, 'type': 'mixed', 'area_sqm': 4000}
    ]
    websocket_manager.send_analytics_update(
        session_id,
        'settlement_detected',
        {
            'count': len(settlements),
            'settlements': settlements
        }
    )
    
    # Simulate population estimation
    for i in range(0, 101, 25):
        websocket_manager.send_progress_update(
            session_id,
            'population_estimation',
            i,
            f'Estimating population density... {i}%'
        )
        time.sleep(0.4)
    
    # Send population results
    population_data = {
        'total': 15000,
        'density_per_sqm': 1.25,
        'breakdown': {
            'formal': 8000,
            'informal': 5000,
            'mixed': 2000
        }
    }
    websocket_manager.send_analytics_update(
        session_id,
        'population_calculated',
        population_data
    )
    
    # Simulate infrastructure analysis
    for i in range(0, 101, 33):
        websocket_manager.send_progress_update(
            session_id,
            'infrastructure_analysis',
            i,
            f'Analyzing road networks and facilities... {i}%'
        )
        time.sleep(0.3)
    
    infrastructure_data = {
        'road_length_km': 12.5,
        'collection_points': 8,
        'accessibility_score': 0.75
    }
    websocket_manager.send_analytics_update(
        session_id,
        'infrastructure_analyzed',
        infrastructure_data
    )
    
    # Simulate waste estimation
    for i in range(0, 101, 50):
        websocket_manager.send_progress_update(
            session_id,
            'waste_estimation',
            i,
            f'Calculating waste generation rates... {i}%'
        )
        time.sleep(0.5)
    
    # Send waste estimation results
    waste_data = {
        'daily_tons': 12.5,
        'weekly_tons': 87.5,
        'monthly_tons': 375,
        'composition': {
            'organic': 0.6,
            'plastic': 0.15,
            'paper': 0.1,
            'metal': 0.05,
            'other': 0.1
        }
    }
    websocket_manager.send_analytics_update(
        session_id,
        'waste_estimation_complete',
        waste_data
    )
    
    # Send completion notification
    websocket_manager.send_analytics_update(
        session_id,
        'analysis_complete',
        {
            'zone_id': zone_data['id'],
            'duration_seconds': 5,
            'summary': {
                'settlements': len(settlements),
                'population': population_data['total'],
                'daily_waste_tons': waste_data['daily_tons']
            }
        }
    )
    
    print(f"Zone analysis simulation completed for session: {session_id}")


def test_error_handling(websocket_manager, session_id):
    """Test error handling and notification."""
    print(f"Testing error handling for session: {session_id}")
    
    # Simulate an error during analysis
    websocket_manager.send_analytics_update(
        session_id,
        'analysis_started',
        {'zone_id': 'error_test', 'zone_name': 'Error Test Zone'}
    )
    
    time.sleep(1)
    
    # Send error notification
    websocket_manager.send_error(
        session_id,
        'Failed to connect to Earth Engine API',
        'EE_CONNECTION_ERROR',
        {
            'retry_count': 3,
            'last_attempt': time.time()
        }
    )


def test_connection_health(websocket_manager):
    """Test connection health monitoring."""
    print("\nTesting connection health monitoring...")
    
    # Get connection stats
    stats = websocket_manager.get_stats()
    print(f"Connection stats: {stats}")
    
    # Check health of all connections
    health_status = websocket_manager.check_connection_health()
    print(f"Connection health: {health_status}")
    
    # Clean up unhealthy connections
    websocket_manager.cleanup_unhealthy_connections()
    print("Cleaned up unhealthy connections")


if __name__ == '__main__':
    # Create test application
    app, socketio, websocket_manager = create_test_app()
    
    # Define test routes
    @app.route('/')
    def index():
        return '''
        <html>
        <head>
            <title>WebSocket Manager Test</title>
            <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
        </head>
        <body>
            <h1>WebSocket Manager Test</h1>
            <div id="status">Connecting...</div>
            <div id="messages"></div>
            
            <script>
                const socket = io();
                const sessionId = 'test_session_' + Date.now();
                
                socket.on('connect', () => {
                    document.getElementById('status').textContent = 'Connected';
                    console.log('Connected to server');
                    
                    // Join test room
                    socket.emit('join_room', {
                        room: sessionId,
                        user_id: 'test_user'
                    });
                });
                
                socket.on('analytics_update', (data) => {
                    console.log('Analytics update:', data);
                    const msgDiv = document.createElement('div');
                    msgDiv.textContent = `${data.type}: ${JSON.stringify(data.data)}`;
                    document.getElementById('messages').appendChild(msgDiv);
                });
                
                socket.on('disconnect', () => {
                    document.getElementById('status').textContent = 'Disconnected';
                    console.log('Disconnected from server');
                });
            </script>
        </body>
        </html>
        '''
    
    # Start analysis simulation in a separate thread
    def run_simulations():
        time.sleep(2)  # Wait for client to connect
        
        # Run zone analysis simulation
        simulate_zone_analysis(websocket_manager, 'test_session_1')
        
        time.sleep(2)
        
        # Test error handling
        test_error_handling(websocket_manager, 'test_session_2')
        
        time.sleep(2)
        
        # Test connection health
        test_connection_health(websocket_manager)
    
    simulation_thread = threading.Thread(target=run_simulations)
    simulation_thread.start()
    
    # Run the application
    print("Starting test server on http://localhost:5000")
    print("Open this URL in your browser to see WebSocket updates in real-time")
    socketio.run(app, debug=True, port=5000)