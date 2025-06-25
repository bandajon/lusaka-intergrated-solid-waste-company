/**
 * WebSocket Client for Real-time Analytics Updates
 * 
 * This module provides a client-side interface for receiving real-time
 * analytics updates during zone creation and analysis.
 */

class AnalyticsWebSocketClient {
    constructor(options = {}) {
        this.socketUrl = options.socketUrl || window.location.origin;
        this.autoReconnect = options.autoReconnect !== false;
        this.reconnectInterval = options.reconnectInterval || 5000;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.debug = options.debug || false;
        
        this.socket = null;
        this.currentRoom = null;
        this.reconnectAttempts = 0;
        this.handlers = new Map();
        this.connectionListeners = [];
        
        // Default event handlers
        this.setupDefaultHandlers();
    }
    
    /**
     * Connect to the WebSocket server
     */
    connect() {
        if (this.socket && this.socket.connected) {
            this.log('Already connected');
            return Promise.resolve();
        }
        
        return new Promise((resolve, reject) => {
            try {
                // Initialize Socket.IO connection
                this.socket = io(this.socketUrl, {
                    transports: ['websocket', 'polling'],
                    reconnection: this.autoReconnect,
                    reconnectionDelay: this.reconnectInterval,
                    reconnectionAttempts: this.maxReconnectAttempts
                });
                
                // Connection event handlers
                this.socket.on('connect', () => {
                    this.log('Connected to WebSocket server');
                    this.reconnectAttempts = 0;
                    this.notifyConnectionListeners('connected');
                    resolve();
                });
                
                this.socket.on('disconnect', (reason) => {
                    this.log('Disconnected:', reason);
                    this.notifyConnectionListeners('disconnected', reason);
                });
                
                this.socket.on('connect_error', (error) => {
                    this.log('Connection error:', error);
                    this.reconnectAttempts++;
                    
                    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                        this.notifyConnectionListeners('error', 'Max reconnection attempts reached');
                        reject(error);
                    }
                });
                
                // Setup message handlers
                this.setupSocketHandlers();
                
            } catch (error) {
                this.log('Failed to initialize socket:', error);
                reject(error);
            }
        });
    }
    
    /**
     * Disconnect from the WebSocket server
     */
    disconnect() {
        if (this.socket) {
            if (this.currentRoom) {
                this.leaveRoom(this.currentRoom);
            }
            this.socket.disconnect();
            this.socket = null;
        }
    }
    
    /**
     * Join a room for receiving specific analytics updates
     * @param {string} room - Room identifier (usually zone creation session ID)
     * @param {string} userId - Optional user identifier
     */
    joinRoom(room, userId = null) {
        if (!this.socket || !this.socket.connected) {
            throw new Error('Not connected to WebSocket server');
        }
        
        return new Promise((resolve, reject) => {
            this.socket.emit('join_room', { room, user_id: userId });
            
            const joinHandler = (data) => {
                if (data.room === room) {
                    this.currentRoom = room;
                    this.socket.off('joined_room', joinHandler);
                    this.socket.off('error', errorHandler);
                    resolve(data);
                }
            };
            
            const errorHandler = (error) => {
                this.socket.off('joined_room', joinHandler);
                this.socket.off('error', errorHandler);
                reject(error);
            };
            
            this.socket.once('joined_room', joinHandler);
            this.socket.once('error', errorHandler);
        });
    }
    
    /**
     * Leave a room
     * @param {string} room - Room identifier
     */
    leaveRoom(room) {
        if (!this.socket || !this.socket.connected) {
            return;
        }
        
        this.socket.emit('leave_room', { room });
        if (this.currentRoom === room) {
            this.currentRoom = null;
        }
    }
    
    /**
     * Send a ping to maintain connection health
     */
    ping() {
        if (this.socket && this.socket.connected) {
            this.socket.emit('ping');
        }
    }
    
    /**
     * Register a handler for analytics updates
     * @param {string} updateType - Type of update to handle
     * @param {Function} handler - Handler function
     */
    onAnalyticsUpdate(updateType, handler) {
        if (!this.handlers.has(updateType)) {
            this.handlers.set(updateType, []);
        }
        this.handlers.get(updateType).push(handler);
    }
    
    /**
     * Register a connection status listener
     * @param {Function} listener - Listener function
     */
    onConnectionChange(listener) {
        this.connectionListeners.push(listener);
    }
    
    /**
     * Setup default event handlers
     */
    setupDefaultHandlers() {
        // Progress update handler
        this.onAnalyticsUpdate('analysis_progress', (data) => {
            this.log('Progress:', data.task, data.progress + '%', data.message);
        });
        
        // Error handler
        this.onAnalyticsUpdate('analysis_error', (data) => {
            console.error('Analytics error:', data.message, data.details);
        });
    }
    
    /**
     * Setup Socket.IO event handlers
     */
    setupSocketHandlers() {
        // Handle analytics updates
        this.socket.on('analytics_update', (update) => {
            this.log('Analytics update received:', update.type);
            
            // Call registered handlers for this update type
            const handlers = this.handlers.get(update.type) || [];
            handlers.forEach(handler => {
                try {
                    handler(update.data, update);
                } catch (error) {
                    console.error('Handler error:', error);
                }
            });
            
            // Also call generic update handlers
            const genericHandlers = this.handlers.get('*') || [];
            genericHandlers.forEach(handler => {
                try {
                    handler(update.type, update.data, update);
                } catch (error) {
                    console.error('Generic handler error:', error);
                }
            });
        });
        
        // Handle pong responses
        this.socket.on('pong', (data) => {
            this.log('Pong received:', data.timestamp);
        });
    }
    
    /**
     * Notify connection listeners
     */
    notifyConnectionListeners(status, data = null) {
        this.connectionListeners.forEach(listener => {
            try {
                listener(status, data);
            } catch (error) {
                console.error('Connection listener error:', error);
            }
        });
    }
    
    /**
     * Log message if debug is enabled
     */
    log(...args) {
        if (this.debug) {
            console.log('[WebSocket]', ...args);
        }
    }
    
    /**
     * Get connection status
     */
    isConnected() {
        return this.socket && this.socket.connected;
    }
    
    /**
     * Get current room
     */
    getCurrentRoom() {
        return this.currentRoom;
    }
}

// Example usage and UI integration
class AnalyticsProgressUI {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.websocketClient = null;
        this.progressBars = new Map();
    }
    
    /**
     * Initialize WebSocket connection and UI
     */
    async initialize(sessionId) {
        // Create WebSocket client
        this.websocketClient = new AnalyticsWebSocketClient({
            debug: true,
            autoReconnect: true
        });
        
        // Setup event handlers
        this.setupEventHandlers();
        
        // Connect and join room
        try {
            await this.websocketClient.connect();
            await this.websocketClient.joinRoom(sessionId);
            this.showStatus('Connected', 'success');
        } catch (error) {
            this.showStatus('Connection failed', 'error');
            console.error('WebSocket initialization error:', error);
        }
    }
    
    /**
     * Setup WebSocket event handlers
     */
    setupEventHandlers() {
        // Connection status
        this.websocketClient.onConnectionChange((status, data) => {
            this.showStatus(`Connection: ${status}`, 
                           status === 'connected' ? 'success' : 'warning');
        });
        
        // Analysis started
        this.websocketClient.onAnalyticsUpdate('analysis_started', (data) => {
            this.showStatus('Analysis started', 'info');
            this.clearProgress();
        });
        
        // Progress updates
        this.websocketClient.onAnalyticsUpdate('analysis_progress', (data) => {
            this.updateProgress(data.task, data.progress, data.message);
        });
        
        // Settlement detection
        this.websocketClient.onAnalyticsUpdate('settlement_detected', (data) => {
            this.showResult('Settlements', `Detected ${data.count} settlements`);
        });
        
        // Population calculation
        this.websocketClient.onAnalyticsUpdate('population_calculated', (data) => {
            this.showResult('Population', `Total: ${data.total || 0}`);
        });
        
        // Waste estimation
        this.websocketClient.onAnalyticsUpdate('waste_estimation_complete', (data) => {
            this.showResult('Waste Estimation', 
                          `Daily: ${data.daily_tons || 0} tons`);
        });
        
        // Analysis complete
        this.websocketClient.onAnalyticsUpdate('analysis_complete', (data) => {
            this.showStatus('Analysis complete', 'success');
            this.showSummary(data.summary);
        });
        
        // Errors
        this.websocketClient.onAnalyticsUpdate('analysis_error', (data) => {
            this.showStatus(`Error: ${data.message}`, 'error');
        });
    }
    
    /**
     * Update progress bar
     */
    updateProgress(task, progress, message) {
        let progressBar = this.progressBars.get(task);
        
        if (!progressBar) {
            progressBar = this.createProgressBar(task);
            this.progressBars.set(task, progressBar);
        }
        
        progressBar.bar.style.width = `${progress}%`;
        progressBar.bar.textContent = `${Math.round(progress)}%`;
        
        if (message) {
            progressBar.message.textContent = message;
        }
        
        if (progress >= 100) {
            progressBar.element.classList.add('completed');
        }
    }
    
    /**
     * Create a progress bar element
     */
    createProgressBar(task) {
        const element = document.createElement('div');
        element.className = 'progress-item';
        element.innerHTML = `
            <h4>${this.formatTaskName(task)}</h4>
            <div class="progress">
                <div class="progress-bar" role="progressbar" style="width: 0%">0%</div>
            </div>
            <small class="progress-message"></small>
        `;
        
        this.container.appendChild(element);
        
        return {
            element: element,
            bar: element.querySelector('.progress-bar'),
            message: element.querySelector('.progress-message')
        };
    }
    
    /**
     * Format task name for display
     */
    formatTaskName(task) {
        return task.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }
    
    /**
     * Show status message
     */
    showStatus(message, type = 'info') {
        const statusEl = document.getElementById('analytics-status');
        if (statusEl) {
            statusEl.className = `alert alert-${type}`;
            statusEl.textContent = message;
        }
    }
    
    /**
     * Show result
     */
    showResult(title, content) {
        const resultsEl = document.getElementById('analytics-results');
        if (resultsEl) {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            resultItem.innerHTML = `<strong>${title}:</strong> ${content}`;
            resultsEl.appendChild(resultItem);
        }
    }
    
    /**
     * Show analysis summary
     */
    showSummary(summary) {
        const summaryEl = document.getElementById('analytics-summary');
        if (summaryEl) {
            summaryEl.innerHTML = `
                <h3>Analysis Summary</h3>
                <ul>
                    <li>Settlements: ${summary.settlements || 0}</li>
                    <li>Population: ${summary.population || 0}</li>
                    <li>Daily Waste: ${summary.daily_waste_tons || 0} tons</li>
                </ul>
            `;
        }
    }
    
    /**
     * Clear all progress bars
     */
    clearProgress() {
        this.progressBars.clear();
        this.container.innerHTML = '';
    }
    
    /**
     * Cleanup
     */
    destroy() {
        if (this.websocketClient) {
            this.websocketClient.disconnect();
        }
    }
}

// Export for use in other modules
window.AnalyticsWebSocketClient = AnalyticsWebSocketClient;
window.AnalyticsProgressUI = AnalyticsProgressUI;