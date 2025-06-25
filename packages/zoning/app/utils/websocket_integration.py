"""
WebSocket Integration Example

This module demonstrates how to integrate the WebSocket manager with the Flask application
and existing analytics modules.
"""

from flask import Flask
from flask_socketio import SocketIO
from .websocket_manager import WebSocketManager
import logging

logger = logging.getLogger(__name__)


def init_websocket(app: Flask) -> tuple[SocketIO, WebSocketManager]:
    """
    Initialize WebSocket support for the Flask application.
    
    Args:
        app: Flask application instance
        
    Returns:
        Tuple of (SocketIO instance, WebSocketManager instance)
    """
    # Configure SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",  # Configure based on your security requirements
        logger=True,
        engineio_logger=False,
        async_mode='threading'  # Can be 'threading', 'eventlet', or 'gevent'
    )
    
    # Create WebSocket manager
    websocket_manager = WebSocketManager(socketio)
    
    # Store in app context for easy access
    app.websocket_manager = websocket_manager
    app.socketio = socketio
    
    logger.info("WebSocket support initialized")
    
    return socketio, websocket_manager


class AnalyticsWebSocketMixin:
    """
    Mixin class for adding WebSocket support to analytics classes.
    
    Add this mixin to your existing analytics classes to enable
    real-time progress updates.
    """
    
    def __init__(self, *args, websocket_manager: WebSocketManager = None, 
                 session_id: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket_manager = websocket_manager
        self.session_id = session_id
    
    def send_progress(self, task: str, progress: float, message: str = None,
                     details: dict = None):
        """Send progress update via WebSocket if available."""
        if self.websocket_manager and self.session_id:
            self.websocket_manager.send_progress_update(
                self.session_id,
                task,
                progress,
                message,
                details
            )
    
    def send_error(self, error_message: str, error_code: str = None,
                   details: dict = None):
        """Send error notification via WebSocket if available."""
        if self.websocket_manager and self.session_id:
            self.websocket_manager.send_error(
                self.session_id,
                error_message,
                error_code,
                details
            )
    
    def send_result(self, update_type: str, data: dict):
        """Send result update via WebSocket if available."""
        if self.websocket_manager and self.session_id:
            self.websocket_manager.send_analytics_update(
                self.session_id,
                update_type,
                data
            )


# Example: Enhanced Real-time Zone Analyzer with WebSocket support
class WebSocketEnabledZoneAnalyzer:
    """
    Example of integrating WebSocket updates with zone analysis.
    
    This demonstrates how to add real-time progress updates to
    existing analytics classes.
    """
    
    def __init__(self, websocket_manager: WebSocketManager = None,
                 session_id: str = None):
        self.websocket_manager = websocket_manager
        self.session_id = session_id
    
    def analyze_zone(self, zone_data: dict):
        """Analyze zone with real-time progress updates."""
        try:
            # Start analysis
            self._send_update('analysis_started', {
                'zone_id': zone_data.get('id'),
                'zone_name': zone_data.get('name')
            })
            
            # Settlement detection
            self._send_progress('settlement_detection', 0, 'Starting settlement detection...')
            settlements = self._detect_settlements(zone_data)
            self._send_progress('settlement_detection', 100, 'Settlement detection complete')
            self._send_update('settlement_detected', {
                'count': len(settlements),
                'settlements': settlements
            })
            
            # Population estimation
            self._send_progress('population_estimation', 0, 'Estimating population...')
            population = self._estimate_population(zone_data, settlements)
            self._send_progress('population_estimation', 100, 'Population estimation complete')
            self._send_update('population_calculated', population)
            
            # Infrastructure analysis
            self._send_progress('infrastructure_analysis', 0, 'Analyzing infrastructure...')
            infrastructure = self._analyze_infrastructure(zone_data)
            self._send_progress('infrastructure_analysis', 100, 'Infrastructure analysis complete')
            self._send_update('infrastructure_analyzed', infrastructure)
            
            # Waste estimation
            self._send_progress('waste_estimation', 0, 'Calculating waste estimates...')
            waste_estimates = self._estimate_waste(population, infrastructure)
            self._send_progress('waste_estimation', 100, 'Waste estimation complete')
            self._send_update('waste_estimation_complete', waste_estimates)
            
            # Analysis complete
            self._send_update('analysis_complete', {
                'zone_id': zone_data.get('id'),
                'summary': {
                    'settlements': len(settlements),
                    'population': population.get('total', 0),
                    'daily_waste_tons': waste_estimates.get('daily_tons', 0)
                }
            })
            
        except Exception as e:
            logger.error(f"Zone analysis error: {e}")
            self._send_error(str(e), 'ANALYSIS_ERROR')
            raise
    
    def _send_update(self, update_type: str, data: dict):
        """Send analytics update."""
        if self.websocket_manager and self.session_id:
            self.websocket_manager.send_analytics_update(
                self.session_id,
                update_type,
                data
            )
    
    def _send_progress(self, task: str, progress: float, message: str = None):
        """Send progress update."""
        if self.websocket_manager and self.session_id:
            self.websocket_manager.send_progress_update(
                self.session_id,
                task,
                progress,
                message
            )
    
    def _send_error(self, error_message: str, error_code: str = None):
        """Send error notification."""
        if self.websocket_manager and self.session_id:
            self.websocket_manager.send_error(
                self.session_id,
                error_message,
                error_code
            )
    
    # Placeholder methods for actual analysis logic
    def _detect_settlements(self, zone_data):
        """Detect settlements in zone."""
        # Implement actual settlement detection
        return []
    
    def _estimate_population(self, zone_data, settlements):
        """Estimate population."""
        # Implement actual population estimation
        return {'total': 0}
    
    def _analyze_infrastructure(self, zone_data):
        """Analyze infrastructure."""
        # Implement actual infrastructure analysis
        return {}
    
    def _estimate_waste(self, population, infrastructure):
        """Estimate waste generation."""
        # Implement actual waste estimation
        return {'daily_tons': 0}


# Example: WebSocket-enabled route decorator
def with_websocket_updates(f):
    """
    Decorator to add WebSocket support to route handlers.
    
    Usage:
        @app.route('/analyze/<zone_id>')
        @with_websocket_updates
        def analyze_zone(zone_id, websocket_session_id=None):
            # websocket_session_id will be injected if provided in request
            pass
    """
    from functools import wraps
    from flask import request, current_app
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get session ID from request (could be from headers, query params, etc.)
        session_id = request.headers.get('X-WebSocket-Session-ID') or \
                    request.args.get('ws_session_id')
        
        if session_id and hasattr(current_app, 'websocket_manager'):
            kwargs['websocket_session_id'] = session_id
            kwargs['websocket_manager'] = current_app.websocket_manager
        
        return f(*args, **kwargs)
    
    return decorated_function