// Main JavaScript for Lusaka Zoning Platform

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Initialize CSV upload if on the upload page
    if (document.getElementById('csv-upload-form')) {
        console.log('CSV upload form detected, initializing...');
        initializeCSVUpload();
    }
});

// CSV Upload functionality
function initializeCSVUpload() {
    console.log('Initializing CSV upload...');
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.getElementById('csv_file');
    const form = document.getElementById('csv-upload-form');
    
    console.log('Elements found:', { uploadArea: !!uploadArea, fileInput: !!fileInput, form: !!form });
    
    if (!uploadArea || !fileInput) {
        console.log('Missing required elements for CSV upload');
        return;
    }
    
    // Drag and drop functionality
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        console.log('Files dropped:', files.length);
        
        if (files.length > 0) {
            console.log('First file:', files[0].name, files[0].size);
            
            try {
                // Some browsers (e.g. Chrome, Firefox, Edge) allow constructing
                // a new DataTransfer object, which is the safest way to programmatically
                // populate a FileList.
                const dataTransfer = new DataTransfer();
                for (const file of files) {
                    dataTransfer.items.add(file);
                }
                fileInput.files = dataTransfer.files;
                console.log('Files set via DataTransfer, fileInput.files.length:', fileInput.files.length);
            } catch (err) {
                console.log('DataTransfer failed, trying direct assignment:', err);
                /*
                 * Fallback for browsers that do not support the DataTransfer() constructor
                 * (notably older versions of Safari). In those cases we try setting the
                 * FileList directly. Although FileList is generally read-only, some
                 * WebKit implementations still allow the assignment.
                 */
                try {
                    fileInput.files = files;
                    console.log('Files set via direct assignment, fileInput.files.length:', fileInput.files.length);
                } catch (innerErr) {
                    console.warn('Unable to programmatically set FileList:', innerErr);
                }
            }

            // Update the UI preview with the first (and usually only) file
            handleFileSelect(files[0]);
            
            // Trigger change event to ensure form validation updates
            const changeEvent = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(changeEvent);
            
            // Double-check that the file was set
            setTimeout(() => {
                console.log('Final verification - fileInput.files.length:', fileInput.files.length);
                if (fileInput.files.length > 0) {
                    console.log('File successfully set:', fileInput.files[0].name);
                } else {
                    console.error('File was not set properly!');
                }
            }, 100);
        }
    });
    
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    // Note: Form submission removed - CSV processing now handled by direct JavaScript parsing
}

function handleFileSelect(file) {
    console.log('File selected:', file.name, file.size);
    // Validate file type
    if (!file.name.endsWith('.csv') && !file.name.endsWith('.txt')) {
        alert('Please select a CSV file');
        return;
    }
    
    // Update UI
    const uploadArea = document.querySelector('.upload-area');
    uploadArea.innerHTML = `
        <i class="fas fa-file-csv fa-3x mb-3"></i>
        <p class="mb-0">Selected: ${file.name}</p>
        <p class="text-muted">${(file.size / 1024).toFixed(2)} KB</p>
        <button type="button" class="btn btn-success mt-2" onclick="processCSVFile()">
            <i class="fas fa-map-marked-alt me-2"></i>Load Coordinates on Map
        </button>
    `;
    
    // Store the file for processing
    window.selectedCSVFile = file;
}

function processCSVFile() {
    if (!window.selectedCSVFile) {
        alert('No file selected');
        return;
    }
    
    console.log('Processing CSV file:', window.selectedCSVFile.name);
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const csvContent = e.target.result;
            const coordinates = parseCSVCoordinates(csvContent);
            
            if (coordinates.length < 3) {
                alert('CSV file must contain at least 3 coordinate points to create a zone');
                return;
            }
            
            console.log('Parsed coordinates:', coordinates);
            
            // Create zone name from filename
            const zoneName = window.selectedCSVFile.name.replace('.csv', '').replace(/[^a-zA-Z0-9_-]/g, '_');
            
            // Redirect to zone creation with coordinates
            redirectToZoneCreation(coordinates, zoneName);
            
        } catch (error) {
            console.error('Error processing CSV:', error);
            alert('Error processing CSV file: ' + error.message);
        }
    };
    
    reader.onerror = function() {
        alert('Error reading file');
    };
    
    reader.readAsText(window.selectedCSVFile);
}

function parseCSVCoordinates(csvContent) {
    const lines = csvContent.trim().split('\n');
    if (lines.length < 2) {
        throw new Error('CSV file is empty or has no data rows');
    }
    
    // Parse header to find coordinate columns
    const header = lines[0].toLowerCase().split(',').map(col => col.trim());
    
    // Find longitude column (lon, lng, longitude, long, x)
    const lonIndex = header.findIndex(col => 
        ['lon', 'lng', 'longitude', 'long', 'x'].includes(col)
    );
    
    // Find latitude column (lat, latitude, y)
    const latIndex = header.findIndex(col => 
        ['lat', 'latitude', 'y'].includes(col)
    );
    
    if (lonIndex === -1 || latIndex === -1) {
        throw new Error('Could not find longitude/latitude columns. Expected columns like: lon,lat or longitude,latitude');
    }
    
    console.log(`Found coordinates at columns: ${header[lonIndex]} (${lonIndex}), ${header[latIndex]} (${latIndex})`);
    
    const coordinates = [];
    
    // Parse data rows
    for (let i = 1; i < lines.length; i++) {
        const row = lines[i].split(',').map(cell => cell.trim());
        
        if (row.length <= Math.max(lonIndex, latIndex)) {
            console.warn(`Row ${i} has insufficient columns, skipping`);
            continue;
        }
        
        const lon = parseFloat(row[lonIndex]);
        const lat = parseFloat(row[latIndex]);
        
        if (isNaN(lon) || isNaN(lat)) {
            console.warn(`Row ${i} has invalid coordinates: ${row[lonIndex]}, ${row[latIndex]}`);
            continue;
        }
        
        // Basic validation for Lusaka area
        if (lon < 27.5 || lon > 29.0 || lat < -16.0 || lat > -14.5) {
            console.warn(`Row ${i} coordinates outside Lusaka bounds: ${lon}, ${lat}`);
            // Still include it, just warn
        }
        
        coordinates.push([lon, lat]);
    }
    
    // Remove consecutive duplicates
    const uniqueCoords = [];
    for (let i = 0; i < coordinates.length; i++) {
        if (i === 0 || coordinates[i][0] !== coordinates[i-1][0] || coordinates[i][1] !== coordinates[i-1][1]) {
            uniqueCoords.push(coordinates[i]);
        }
    }
    
    return uniqueCoords;
}

function redirectToZoneCreation(coordinates, zoneName) {
    // Create URL with coordinates as parameters
    const params = new URLSearchParams();
    params.set('coordinates', JSON.stringify(coordinates));
    params.set('name', zoneName);
    params.set('source', 'csv');
    
    // Redirect to zone creation page
    const createUrl = '/zones/create?' + params.toString();
    console.log('Redirecting to:', createUrl);
    window.location.href = createUrl;
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Zone type colors for consistent styling
const zoneTypeColors = {
    'residential': '#28a745',
    'commercial': '#ffc107',
    'industrial': '#6c757d',
    'institutional': '#17a2b8',
    'mixed_use': '#e83e8c',
    'green_space': '#20c997'
};

// Export functions for use in templates
window.LusakaZoning = {
    initializeCSVUpload: initializeCSVUpload,
    formatNumber: formatNumber,
    zoneTypeColors: zoneTypeColors
};