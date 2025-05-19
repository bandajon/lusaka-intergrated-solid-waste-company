// Custom JavaScript for Dash app

// When document is loaded
document.addEventListener('DOMContentLoaded', function() {
  console.log('Dashboard scripts loaded successfully');
  
  // Helper function to add hover effects to cards
  function addCardHoverEffects() {
    const cards = document.querySelectorAll('.stat-card, .bg-white');
    cards.forEach(card => {
      card.addEventListener('mouseenter', function() {
        this.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)';
      });
      
      card.addEventListener('mouseleave', function() {
        this.style.boxShadow = '';
      });
    });
  }
  
  // Function to improve table responsiveness
  function improveTableResponsiveness() {
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
      const wrapper = document.createElement('div');
      wrapper.className = 'overflow-x-auto';
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    });
  }
  
  // Set up a mutation observer to handle dynamically added content
  const observer = new MutationObserver(function(mutations) {
    addCardHoverEffects();
    improveTableResponsiveness();
  });
  
  // Start observing the document with the configured parameters
  observer.observe(document.body, { childList: true, subtree: true });
  
  // Initial call to set up effects
  addCardHoverEffects();
  improveTableResponsiveness();
});

// Custom function to export data to Excel
function exportTableToExcel(tableID, filename = '') {
  const table = document.getElementById(tableID);
  if (!table) return;
  
  const wb = XLSX.utils.table_to_book(table);
  XLSX.writeFile(wb, filename);
}

// Function to print the dashboard
function printDashboard() {
  window.print();
}