const API_BASE_URL = 'http://localhost:8000/api';
const contentDiv = document.getElementById('content');
const loadingIndicator = document.getElementById('loading-indicator');
const errorMessageDiv = document.getElementById('error-message');
const errorTextSpan = document.getElementById('error-text');

// Function to show loading indicator
function showLoading() {
    loadingIndicator.classList.remove('hidden');
    errorMessageDiv.classList.add('hidden');
    contentDiv.innerHTML = ''; // Clear content
}

// Function to hide loading indicator
function hideLoading() {
    loadingIndicator.classList.add('hidden');
}

// Function to display an error message
function showError(message) {
    hideLoading();
    errorMessageDiv.classList.remove('hidden');
    errorTextSpan.textContent = message;
}

// Function to fetch data from the API
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.error || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        showError(`Failed to load data: ${error.message}`);
        return null;
    }
}

// Function to render all departments
async function renderDepartments() {
    showLoading();
    const data = await fetchData(`${API_BASE_URL}/departments`);
    hideLoading();

    if (data && data.departments) {
        contentDiv.innerHTML = `
            <h2 class="text-2xl font-bold text-gray-800 mb-4">All Departments</h2>
            <div id="departments-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                ${data.departments.map(dept => `
                    <div class="department-card p-4 rounded-lg shadow-md bg-white hover:bg-indigo-50 transition-colors" 
                         data-dept-id="${dept.id}" data-dept-name="${dept.name}">
                        <h3 class="text-xl font-semibold text-indigo-700">${dept.name}</h3>
                        <p class="text-gray-600">Products: ${dept.product_count}</p>
                    </div>
                `).join('')}
            </div>
        `;
        // Add event listeners to department cards
        document.querySelectorAll('.department-card').forEach(card => {
            card.addEventListener('click', () => {
                const deptId = card.dataset.deptId;
                const deptName = card.dataset.deptName;
                // Update URL and render products
                history.pushState({ deptId: deptId }, '', `?department=${deptId}`);
                renderDepartmentProducts(deptId, deptName);
            });
        });
    } else if (data) {
        showError("No departments found or unexpected data format.");
    }
}

// Function to render products for a specific department
async function renderDepartmentProducts(deptId, deptName = 'Unknown Department') {
    showLoading();
    const departmentData = await fetchData(`${API_BASE_URL}/departments/${deptId}`);
    const productsData = await fetchData(`${API_BASE_URL}/departments/${deptId}/products`);
    hideLoading();

    if (departmentData && productsData) {
        const actualDeptName = departmentData.name || deptName; // Use actual name from API if available
        const productCount = departmentData.product_count || 0;

        contentDiv.innerHTML = `
            <button id="back-to-departments" class="button-primary mb-4">
                &larr; Back to Departments
            </button>
            <h2 class="text-2xl font-bold text-gray-800 mb-2">${actualDeptName} Department</h2>
            <p class="text-gray-600 mb-4">Total Products: ${productCount}</p>
            <div id="products-list" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                ${productsData.products.length > 0 ? 
                    productsData.products.map(product => `
                        <div class="product-card p-4 rounded-lg shadow-md bg-white">
                            <h3 class="text-lg font-semibold text-gray-800">${product.name} (ID: ${product.id})</h3>
                            <p class="text-gray-600">Brand: ${product.brand || 'N/A'}</p>
                            <p class="text-gray-600">Category: ${product.category || 'N/A'}</p>
                            <p class="text-gray-700 font-bold">Price: $${(product.retail_price || 0).toFixed(2)}</p>
                        </div>
                    `).join('')
                    : '<p class="text-gray-600">No products found for this department.</p>'
                }
            </div>
        `;
        document.getElementById('back-to-departments').addEventListener('click', () => {
            history.pushState({}, '', '/'); // Go back to root URL
            renderDepartments();
        });
    } else if (departmentData === null || productsData === null) {
        // Error message already handled by fetchData
    } else {
        showError("Failed to load department or product data.");
    }
}

// Handle browser history navigation (back/forward buttons)
window.addEventListener('popstate', (event) => {
    const params = new URLSearchParams(window.location.search);
    const deptId = params.get('department');
    if (deptId) {
        renderDepartmentProducts(deptId);
    } else {
        renderDepartments();
    }
});

// Initial page load logic
document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const deptId = params.get('department');
    if (deptId) {
        renderDepartmentProducts(deptId);
    } else {
        renderDepartments();
    }
});
