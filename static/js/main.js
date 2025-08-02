// Main JavaScript for Personal Finance Tracker

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // File upload preview
    const fileInput = document.getElementById('receipt');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    let preview = document.getElementById('receipt-preview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.id = 'receipt-preview';
                        preview.className = 'receipt-preview';
                        fileInput.parentNode.appendChild(preview);
                    }
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Transaction type toggle
    const transactionTypeSelect = document.getElementById('transaction_type');
    if (transactionTypeSelect) {
        transactionTypeSelect.addEventListener('change', function() {
            const amountInput = document.getElementById('amount');
            const amountLabel = document.querySelector('label[for="amount"]');
            
            if (this.value === 'income') {
                amountInput.classList.remove('border-danger');
                amountInput.classList.add('border-success');
                amountLabel.textContent = 'Income Amount';
            } else {
                amountInput.classList.remove('border-success');
                amountInput.classList.add('border-danger');
                amountLabel.textContent = 'Expense Amount';
            }
        });
    }

    // Search functionality for transactions
    const searchInput = document.getElementById('transaction-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const transactionRows = document.querySelectorAll('.transaction-row');
            
            transactionRows.forEach(function(row) {
                const description = row.querySelector('.transaction-description').textContent.toLowerCase();
                const category = row.querySelector('.transaction-category').textContent.toLowerCase();
                
                if (description.includes(searchTerm) || category.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Chart initialization (if Chart.js is loaded)
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
});

// Chart initialization function
function initializeCharts() {
    // Monthly spending chart
    const monthlyChartCanvas = document.getElementById('monthlyChart');
    if (monthlyChartCanvas) {
        const ctx = monthlyChartCanvas.getContext('2d');
        
        // This would be populated with actual data from the backend
        const monthlyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Income',
                    data: [1200, 1900, 3000, 5000, 2000, 3000],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }, {
                    label: 'Expenses',
                    data: [1000, 1500, 2000, 3000, 1800, 2500],
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Category pie chart
    const categoryChartCanvas = document.getElementById('categoryChart');
    if (categoryChartCanvas) {
        const ctx = categoryChartCanvas.getContext('2d');
        
        const categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Food', 'Transportation', 'Entertainment', 'Bills', 'Other'],
                datasets: [{
                    data: [300, 150, 200, 400, 100],
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#4BC0C0',
                        '#9966FF'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function showLoading(element) {
    element.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
    element.disabled = true;
}

function hideLoading(element, originalText) {
    element.innerHTML = originalText;
    element.disabled = false;
}

// API helper functions
async function fetchTransactions() {
    try {
        const response = await fetch('/api/transactions');
        if (!response.ok) {
            throw new Error('Failed to fetch transactions');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching transactions:', error);
        return [];
    }
}

// Export functions for use in other scripts
window.FinanceTracker = {
    formatCurrency,
    showLoading,
    hideLoading,
    fetchTransactions
};
