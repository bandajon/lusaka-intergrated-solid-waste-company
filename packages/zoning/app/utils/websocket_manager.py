"""
WebSocket Manager for Real-time Analytics Updates

This module manages WebSocket connections for streaming real-time analytics updates
to connected clients during zone creation and analysis processes.
"""

import logging
import time
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
from threading import Lock
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request

logger = logging.getLogger(__name__)


class ConnectionInfo:
    """Stores information about a WebSocket connection."""
    
    def __init__(self, sid: str, room: str = None):
        self.sid = sid
        self.room = room
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.user_id = None
        self.metadata = {}
    
    def update_ping(self):
        """Update the last ping timestamp."""
        self.last_ping = datetime.utcnow()
    
    def is_healthy(self, timeout_seconds: int = 60) -> bool:
        """Check if the connection is still healthy."""
        time_since_ping = (datetime.utcnow() - self.last_ping).total_seconds()
        return time_since_ping < timeout_seconds


class WebSocketManager:
    """
    Manages WebSocket connections for real-time analytics updates.
    
    Features:
    - Room-based messaging for zone creation sessions
    - Progressive update streaming
    - Connection lifecycle management
    - Health monitoring
    - Error handling
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.connections: Dict[str, ConnectionInfo] = {}
        self.rooms: Dict[str, Set[str]] = {}
        self.lock = Lock()
        self._register_handlers()
        
        # Analytics update types
        self.UPDATE_TYPES = {
            'zone_created': 'zone_created',
            'analysis_started': 'analysis_started',
            'analysis_progress': 'analysis_progress',
            'analysis_complete': 'analysis_complete',
            'analysis_error': 'analysis_error',
            'settlement_detected': 'settlement_detected',
            'population_calculated': 'population_calculated',
            'infrastructure_analyzed': 'infrastructure_analyzed',
            'waste_estimation_complete': 'waste_estimation_complete'
        }
    
    def _register_handlers(self):
        """Register WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle new WebSocket connection."""
            sid = request.sid
            logger.info(f"Client connected: {sid}")
            
            with self.lock:
                self.connections[sid] = ConnectionInfo(sid)
            
            emit('connected', {
                'sid': sid,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle WebSocket disconnection."""
            sid = request.sid
            logger.info(f"Client disconnected: {sid}")
            
            with self.lock:
                if sid in self.connections:
                    # Remove from any rooms
                    conn_info = self.connections[sid]
                    if conn_info.room:
                        self._remove_from_room(sid, conn_info.room)
                    
                    del self.connections[sid]
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle room join request."""
            sid = request.sid
            room = data.get('room')
            user_id = data.get('user_id')
            
            if not room:
                emit('error', {'message': 'Room name required'})
                return
            
            logger.info(f"Client {sid} joining room: {room}")
            
            with self.lock:
                if sid in self.connections:
                    # Leave previous room if any
                    conn_info = self.connections[sid]
                    if conn_info.room:
                        self._remove_from_room(sid, conn_info.room)
                    
                    # Join new room
                    conn_info.room = room
                    conn_info.user_id = user_id
                    self._add_to_room(sid, room)
                    
            join_room(room)
            emit('joined_room', {
                'room': room,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle room leave request."""
            sid = request.sid
            room = data.get('room')
            
            if not room:
                emit('error', {'message': 'Room name required'})
                return
            
            logger.info(f"Client {sid} leaving room: {room}")
            
            with self.lock:
                if sid in self.connections:
                    conn_info = self.connections[sid]
                    if conn_info.room == room:
                        self._remove_from_room(sid, room)
                        conn_info.room = None
            
            leave_room(room)
            emit('left_room', {
                'room': room,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.socketio.on('ping')
        def handle_ping():
            """Handle ping from client for health monitoring."""
            sid = request.sid
            
            with self.lock:
                if sid in self.connections:
                    self.connections[sid].update_ping()
            
            emit('pong', {'timestamp': datetime.utcnow().isoformat()})
    
    def _add_to_room(self, sid: str, room: str):
        """Add a connection to a room (internal use)."""
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(sid)
    
    def _remove_from_room(self, sid: str, room: str):
        """Remove a connection from a room (internal use)."""
        if room in self.rooms:
            self.rooms[room].discard(sid)
            if not self.rooms[room]:
                del self.rooms[room]
    
    def send_to_client(self, sid: str, event: str, data: Any):
        """Send data to a specific client."""
        try:
            self.socketio.emit(event, data, to=sid)
            logger.debug(f"Sent {event} to client {sid}")
        except Exception as e:
            logger.error(f"Error sending to client {sid}: {e}")
    
    def send_to_room(self, room: str, event: str, data: Any, exclude_sid: str = None):
        """Send data to all clients in a room."""
        try:
            if exclude_sid:
                # Send to everyone in room except specified client
                with self.lock:
                    if room in self.rooms:
                        for sid in self.rooms[room]:
                            if sid != exclude_sid:
                                self.send_to_client(sid, event, data)
            else:
                # Send to entire room
                self.socketio.emit(event, data, to=room)
            
            logger.debug(f"Sent {event} to room {room}")
        except Exception as e:
            logger.error(f"Error sending to room {room}: {e}")
    
    def broadcast(self, event: str, data: Any):
        """Broadcast data to all connected clients."""
        try:
            self.socketio.emit(event, data)
            logger.debug(f"Broadcasted {event} to all clients")
        except Exception as e:
            logger.error(f"Error broadcasting: {e}")
    
    def send_analytics_update(self, room: str, update_type: str, data: Dict[str, Any]):
        """
        Send analytics update to a room.
        
        Args:
            room: Room identifier (usually zone creation session ID)
            update_type: Type of update from UPDATE_TYPES
            data: Update data
        """
        if update_type not in self.UPDATE_TYPES:
            logger.warning(f"Unknown update type: {update_type}")
            return
        
        update_data = {
            'type': update_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        self.send_to_room(room, 'analytics_update', update_data)
    
    def send_progress_update(self, room: str, task: str, progress: float, 
                           message: str = None, details: Dict[str, Any] = None):
        """
        Send progress update for a specific task.
        
        Args:
            room: Room identifier
            task: Task name (e.g., 'settlement_analysis', 'population_estimation')
            progress: Progress percentage (0-100)
            message: Optional progress message
            details: Optional additional details
        """
        update_data = {
            'task': task,
            'progress': min(100, max(0, progress)),
            'message': message,
            'details': details or {}
        }
        
        self.send_analytics_update(room, 'analysis_progress', update_data)
    
    def send_error(self, room: str, error_message: str, error_code: str = None,
                   details: Dict[str, Any] = None):
        """Send error notification to a room."""
        error_data = {
            'message': error_message,
            'code': error_code,
            'details': details or {}
        }
        
        self.send_analytics_update(room, 'analysis_error', error_data)
    
    def get_room_connections(self, room: str) -> List[str]:
        """Get list of connection IDs in a room."""
        with self.lock:
            return list(self.rooms.get(room, set()))
    
    def get_connection_info(self, sid: str) -> Optional[ConnectionInfo]:
        """Get information about a specific connection."""
        with self.lock:
            return self.connections.get(sid)
    
    def check_connection_health(self, timeout_seconds: int = 60) -> Dict[str, bool]:
        """
        Check health of all connections.
        
        Returns:
            Dictionary mapping connection IDs to health status
        """
        health_status = {}
        
        with self.lock:
            for sid, conn_info in self.connections.items():
                health_status[sid] = conn_info.is_healthy(timeout_seconds)
        
        return health_status
    
    def cleanup_unhealthy_connections(self, timeout_seconds: int = 60):
        """Remove unhealthy connections."""
        unhealthy_sids = []
        
        with self.lock:
            for sid, conn_info in self.connections.items():
                if not conn_info.is_healthy(timeout_seconds):
                    unhealthy_sids.append(sid)
        
        for sid in unhealthy_sids:
            logger.warning(f"Removing unhealthy connection: {sid}")
            try:
                disconnect(sid)
            except Exception as e:
                logger.error(f"Error disconnecting unhealthy connection {sid}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        with self.lock:
            total_connections = len(self.connections)
            rooms_count = len(self.rooms)
            connections_per_room = {
                room: len(sids) for room, sids in self.rooms.items()
            }
            
            return {
                'total_connections': total_connections,
                'rooms_count': rooms_count,
                'connections_per_room': connections_per_room,
                'timestamp': datetime.utcnow().isoformat()
            }


# Example usage functions for integration with existing analytics

def send_zone_creation_update(websocket_manager: WebSocketManager, session_id: str,
                            zone_data: Dict[str, Any]):
    """Send zone creation notification."""
    websocket_manager.send_analytics_update(
        session_id,
        'zone_created',
        {
            'zone_id': zone_data.get('id'),
            'zone_name': zone_data.get('name'),
            'geometry': zone_data.get('geometry')
        }
    )


def send_analysis_progress(websocket_manager: WebSocketManager, session_id: str,
                         task: str, progress: float, message: str = None):
    """Send analysis progress update."""
    websocket_manager.send_progress_update(
        session_id,
        task,
        progress,
        message
    )


def send_settlement_detection_result(websocket_manager: WebSocketManager, session_id: str,
                                   settlements: List[Dict[str, Any]]):
    """Send settlement detection results."""
    websocket_manager.send_analytics_update(
        session_id,
        'settlement_detected',
        {
            'count': len(settlements),
            'settlements': settlements
        }
    )


def send_population_estimation_result(websocket_manager: WebSocketManager, session_id: str,
                                    population_data: Dict[str, Any]):
    """Send population estimation results."""
    websocket_manager.send_analytics_update(
        session_id,
        'population_calculated',
        population_data
    )


def send_waste_estimation_result(websocket_manager: WebSocketManager, session_id: str,
                               waste_data: Dict[str, Any]):
    """Send waste estimation results."""
    websocket_manager.send_analytics_update(
        session_id,
        'waste_estimation_complete',
        waste_data
    )