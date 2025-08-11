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
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
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
                if (amountLabel) amountLabel.textContent = 'Income Amount';
            } else {
                amountInput.classList.remove('border-success');
                amountInput.classList.add('border-danger');
                if (amountLabel) amountLabel.textContent = 'Expense Amount';
            }
        });
    }

    // Enhanced search functionality for transactions
    const searchInput = document.getElementById('transaction-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const transactionRows = document.querySelectorAll('.transaction-row');
            
            transactionRows.forEach(function(row) {
                const description = row.querySelector('.transaction-description').textContent.toLowerCase();
                const category = row.querySelector('.transaction-category').textContent.toLowerCase();
                const amount = row.querySelector('.transaction-amount').textContent.toLowerCase();
                
                if (description.includes(searchTerm) || 
                    category.includes(searchTerm) || 
                    amount.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Initialize filter buttons
    const filterButtons = document.querySelectorAll('.btn-group button');
    if (filterButtons.length > 0) {
        filterButtons[0].classList.add('active'); // Set "All" as default active
    }

    // Chart initialization (if Chart.js is loaded)
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }

    // Add loading states to download buttons
    const downloadButtons = document.querySelectorAll('a[href*="download_receipt"]');
    downloadButtons.forEach(button => {
        button.addEventListener('click', function() {
            const icon = this.querySelector('i');
            const originalClass = icon.className;
            icon.className = 'fas fa-spinner fa-spin';
            
            // Reset icon after download attempt
            setTimeout(() => {
                icon.className = originalClass;
            }, 3000);
        });
    });

    // Confirm delete functionality
    const deleteButtons = document.querySelectorAll('button[onclick*="confirmDelete"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            // The onclick attribute will handle the modal display
        });
    });
});

// Transaction filtering function
function filterTransactions(type) {
    const rows = document.querySelectorAll('.transaction-row');
    const buttons = document.querySelectorAll('.btn-group button');
    
    // Update button states
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Filter rows
    rows.forEach(row => {
        if (type === 'all' || row.dataset.type === type) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    
    // Update visible count
    const visibleRows = document.querySelectorAll('.transaction-row[style=""], .transaction-row:not([style])');
    console.log(`Showing ${visibleRows.length} transactions`);
}

// Confirm delete function
function confirmDelete(transactionId, description, amount, date) {
    // Update modal content
    const detailsElement = document.getElementById('transactionDetails');
    if (detailsElement) {
        detailsElement.innerHTML = `
            <strong>${description}</strong><br>
            Amount: $${parseFloat(amount).toFixed(2)}<br>
            Date: ${date}
        `;
    }
    
    // Update form action
    const deleteForm = document.getElementById('deleteForm');
    if (deleteForm) {
        deleteForm.action = `/delete_transaction/${transactionId}`;
    }
    
    // Show modal
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    deleteModal.show();
}

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
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }, {
                    label: 'Expenses',
                    data: [1000, 1500, 2000, 3000, 1800, 2500],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Monthly Income vs Expenses'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            }
                        }
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
                labels: ['Food & Dining', 'Transportation', 'Entertainment', 'Bills & Utilities', 'Other'],
                datasets: [{
                    data: [300, 150, 200, 400, 100],
                    backgroundColor: [
                        '#ff6b6b',
                        '#4ecdc4',
                        '#45b7d1',
                        '#f9ca24',
                        '#a0a0a0'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Expenses by Category'
                    },
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
    const originalText = element.innerHTML;
    element.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
    element.disabled = true;
    
    return function hideLoading() {
        element.innerHTML = originalText;
        element.disabled = false;
    };
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
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
        showNotification('Failed to load transactions', 'danger');
        return [];
    }
}

async function deleteTransactionAPI(transactionId) {
    try {
        const response = await fetch(`/delete_transaction/${transactionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            showNotification('Transaction deleted successfully', 'success');
            // Reload page or remove row from table
            location.reload();
        } else {
            throw new Error('Failed to delete transaction');
        }
    } catch (error) {
        console.error('Error deleting transaction:', error);
        showNotification('Failed to delete transaction', 'danger');
    }
}

// Form enhancement functions
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }
    });
    
    return isValid;
}

function resetForm(form) {
    form.reset();
    form.classList.remove('was-validated');
    form.querySelectorAll('.is-valid, .is-invalid').forEach(field => {
        field.classList.remove('is-valid', 'is-invalid');
    });
}

// Export functions for use in other scripts
window.FinanceTracker = {
    formatCurrency,
    showLoading,
    showNotification,
    fetchTransactions,
    deleteTransactionAPI,
    validateForm,
    resetForm,
    filterTransactions,
    confirmDelete
};
