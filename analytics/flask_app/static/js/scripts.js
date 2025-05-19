// Main application scripts

document.addEventListener('DOMContentLoaded', function() {
  console.log('Application scripts loaded successfully');
  
  // Toggle mobile menu
  const menuButton = document.getElementById('menu-toggle');
  const mobileMenu = document.getElementById('mobile-menu');
  
  if (menuButton && mobileMenu) {
    menuButton.addEventListener('click', function() {
      mobileMenu.classList.toggle('hidden');
    });
  }
  
  // Flash message auto-close
  const flashMessages = document.querySelectorAll('.flash-message');
  
  flashMessages.forEach(function(message) {
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.innerHTML = '&times;';
    closeButton.classList.add('close-button');
    message.appendChild(closeButton);
    
    // Close on click
    closeButton.addEventListener('click', function() {
      message.remove();
    });
    
    // Auto-close after 5 seconds
    setTimeout(function() {
      message.style.opacity = '0';
      setTimeout(function() {
        message.remove();
      }, 300);
    }, 5000);
  });
  
  // Form validation
  const forms = document.querySelectorAll('form.validate');
  
  forms.forEach(function(form) {
    form.addEventListener('submit', function(event) {
      let valid = true;
      
      // Check required fields
      const requiredFields = form.querySelectorAll('[required]');
      requiredFields.forEach(function(field) {
        if (\!field.value.trim()) {
          valid = false;
          field.classList.add('invalid');
          
          // Add error message if it doesn't exist
          let errorMessage = field.nextElementSibling;
          if (\!errorMessage || \!errorMessage.classList.contains('error-message')) {
            errorMessage = document.createElement('p');
            errorMessage.classList.add('error-message', 'text-red-500', 'text-sm', 'mt-1');
            errorMessage.innerText = 'This field is required';
            field.insertAdjacentElement('afterend', errorMessage);
          }
        } else {
          field.classList.remove('invalid');
          const errorMessage = field.nextElementSibling;
          if (errorMessage && errorMessage.classList.contains('error-message')) {
            errorMessage.remove();
          }
        }
      });
      
      if (\!valid) {
        event.preventDefault();
      }
    });
  });
  
  // Data tables
  const dataTables = document.querySelectorAll('.data-table');
  if (dataTables.length > 0) {
    dataTables.forEach(function(table) {
      // Get all th elements in the table
      const ths = table.querySelectorAll('th');
      
      // Make columns sortable
      ths.forEach(function(th, index) {
        th.classList.add('sortable');
        th.addEventListener('click', function() {
          sortTable(table, index);
        });
      });
      
      // Add search functionality
      const wrapper = table.parentElement;
      const searchInput = document.createElement('input');
      searchInput.type = 'text';
      searchInput.placeholder = 'Search...';
      searchInput.classList.add('form-control', 'mb-4', 'w-full', 'md:w-64');
      wrapper.insertBefore(searchInput, table);
      
      searchInput.addEventListener('input', function() {
        filterTable(table, searchInput.value);
      });
    });
  }
  
  // Helper function for table sorting
  function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const headers = table.querySelectorAll('th');
    
    // Toggle sort direction
    const header = headers[columnIndex];
    const isAscending = header.classList.contains('sort-asc');
    
    // Reset all headers
    headers.forEach(h => {
      h.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Set the new sort direction
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    
    // Sort the rows
    rows.sort((a, b) => {
      const cellA = a.querySelectorAll('td')[columnIndex].textContent.trim();
      const cellB = b.querySelectorAll('td')[columnIndex].textContent.trim();
      
      // Check if the values are numbers
      const numA = parseFloat(cellA);
      const numB = parseFloat(cellB);
      
      if (\!isNaN(numA) && \!isNaN(numB)) {
        return isAscending ? numB - numA : numA - numB;
      } else {
        return isAscending ? cellB.localeCompare(cellA) : cellA.localeCompare(cellB);
      }
    });
    
    // Reorder the rows
    rows.forEach(row => tbody.appendChild(row));
  }
  
  // Helper function for table filtering
  function filterTable(table, searchText) {
    const rows = table.querySelectorAll('tbody tr');
    const lowerSearchText = searchText.toLowerCase();
    
    rows.forEach(function(row) {
      const text = row.textContent.toLowerCase();
      if (text.includes(lowerSearchText)) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });
  }
  
  // File input styling
  const fileInputs = document.querySelectorAll('input[type="file"]');
  
  fileInputs.forEach(function(input) {
    const wrapper = document.createElement('div');
    wrapper.classList.add('file-input-wrapper');
    
    const label = document.createElement('label');
    label.classList.add('file-input-label');
    label.innerHTML = 'Choose file...';
    
    const fileNameSpan = document.createElement('span');
    fileNameSpan.classList.add('file-name');
    fileNameSpan.innerText = 'No file selected';
    
    // Replace input with wrapper and move input inside
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    wrapper.appendChild(label);
    wrapper.appendChild(fileNameSpan);
    
    // Update filename on change
    input.addEventListener('change', function() {
      if (input.files.length > 0) {
        fileNameSpan.innerText = input.files[0].name;
      } else {
        fileNameSpan.innerText = 'No file selected';
      }
    });
  });
});

// CSV Export function
function exportTableToCSV(tableID, filename) {
  const table = document.getElementById(tableID);
  const rows = table.querySelectorAll('tr');
  
  // Format rows as CSV
  let csv = [];
  for (let i = 0; i < rows.length; i++) {
    const row = [];
    const cols = rows[i].querySelectorAll('td, th');
    
    for (let j = 0; j < cols.length; j++) {
      // Replace commas with spaces and wrap in quotes if needed
      let text = cols[j].innerText.replace(/\n/g, ' ');
      if (text.includes(',')) {
        text = '"' + text + '"';
      }
      row.push(text);
    }
    
    csv.push(row.join(','));
  }
  
  // Create a CSV file
  const csvContent = csv.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  
  // Create a download link
  if (navigator.msSaveBlob) { // IE 10+
    navigator.msSaveBlob(blob, filename);
  } else {
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
EOF < /dev/null