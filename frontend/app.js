// Configuration
const API_BASE_URL = 'http://localhost:8000';
let currentPage = 1;
const itemsPerPage = 12;

// DOM Elements
const loadingEl = document.getElementById('loading');
const productsContainer = document.getElementById('products-container');
const paginationEl = document.getElementById('pagination');
const errorContainer = document.getElementById('error-container');
const productsListView = document.getElementById('products-list-view');
const productDetailView = document.getElementById('product-detail-view');
const backBtn = document.querySelector('.back-btn');

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    loadProducts();
});

// Load products from API
async function loadProducts() {
    try {
        showLoading(true);
        clearError();

        const response = await fetch(`${API_BASE_URL}/api/products?page=${currentPage}&limit=${itemsPerPage}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            displayProducts(data.data.products);
            updatePagination(data.data.pagination);
        } else {
            throw new Error(data.error || 'Failed to load products');
        }

    } catch (error) {
        console.error('Error loading products:', error);
        showError('Failed to load products. Please check if the API server is running on http://localhost:8000');
    } finally {
        showLoading(false);
    }
}

// Display products in grid
function displayProducts(products) {
    if (!products || products.length === 0) {
        productsContainer.innerHTML = `
            <div class="empty-state">
                <h3>No Products Found</h3>
                <p>There are no products available at the moment.</p>
            </div>
        `;
        productsContainer.style.display = 'block';
        return;
    }

    const productsHTML = products.map(product => `
        <div class="product-card" onclick="viewProduct(${product.id})">
            <div class="product-name">${product.name || 'Unnamed Product'}</div>
            <div class="product-info">
                <div class="product-field">
                    <span class="field-label">Category:</span>
                    <span class="field-value">${product.category || 'N/A'}</span>
                </div>
                <div class="product-field">
                    <span class="field-label">Brand:</span>
                    <span class="field-value">${product.brand || 'N/A'}</span>
                </div>
                <div class="product-field">
                    <span class="field-label">Department:</span>
                    <span class="field-value">${product.department || 'N/A'}</span>
                </div>
                <div class="product-field">
                    <span class="field-label">Price:</span>
                    <span class="field-value price">$${(parseFloat(product.retail_price) || 0).toFixed(2)}</span>
                </div>
                <div class="product-field">
                    <span class="field-label">SKU:</span>
                    <span class="field-value">${product.sku || 'N/A'}</span>
                </div>
            </div>
        </div>
    `).join('');

    productsContainer.innerHTML = productsHTML;
    productsContainer.style.display = 'grid';
}

// View individual product
async function viewProduct(productId) {
    try {
        showLoading(true);
        clearError();

        const response = await fetch(`${API_BASE_URL}/api/products/${productId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            displayProductDetail(data.data);
            showProductDetail();
        } else {
            throw new Error(data.error || 'Failed to load product details');
        }

    } catch (error) {
        console.error('Error loading product:', error);
        showError('Failed to load product details');
    } finally {
        showLoading(false);
    }
}

// Display product detail
function displayProductDetail(product) {
    const detailHTML = `
        <div class="detail-header">
            <h2 class="detail-title">${product.name || 'Unnamed Product'}</h2>
            <span class="detail-id">Product ID: ${product.id}</span>
        </div>
        <div class="detail-grid">
            <div class="detail-field">
                <div class="detail-field-label">Category</div>
                <div class="detail-field-value">${product.category || 'Not specified'}</div>
            </div>
            <div class="detail-field">
                <div class="detail-field-label">Brand</div>
                <div class="detail-field-value">${product.brand || 'Not specified'}</div>
            </div>
            <div class="detail-field">
                <div class="detail-field-label">Department</div>
                <div class="detail-field-value">${product.department || 'Not specified'}</div>
            </div>
            <div class="detail-field">
                <div class="detail-field-label">SKU</div>
                <div class="detail-field-value">${product.sku || 'Not specified'}</div>
            </div>
            <div class="detail-field">
                <div class="detail-field-label">Cost</div>
                <div class="detail-field-value price">$${(parseFloat(product.cost) || 0).toFixed(2)}</div>
            </div>
            <div class="detail-field">
                <div class="detail-field-label">Retail Price</div>
                <div class="detail-field-value price">$${(parseFloat(product.retail_price) || 0).toFixed(2)}</div>
            </div>
            <div class="detail-field">
                <div class="detail-field-label">Distribution Center ID</div>
                <div class="detail-field-value">${product.distribution_center_id || 'Not specified'}</div>
            </div>
        </div>
    `;

    document.getElementById('product-detail-content').innerHTML = detailHTML;
}

// Update pagination
function updatePagination(pagination) {
    const pageInfo = document.getElementById('page-info');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    pageInfo.textContent = `Page ${pagination.current_page} of ${pagination.total_pages}`;
    prevBtn.disabled = !pagination.has_prev_page;
    nextBtn.disabled = !pagination.has_next_page;

    paginationEl.style.display = pagination.total_pages > 1 ? 'flex' : 'none';
}

// Change page
function changePage(direction) {
    currentPage += direction;
    loadProducts();
}

// Show/Hide views
function showProductDetail() {
    productsListView.style.display = 'none';
    productDetailView.style.display = 'block';
    backBtn.style.display = 'block';
}

function showProductsList() {
    productsListView.style.display = 'block';
    productDetailView.style.display = 'none';
    backBtn.style.display = 'none';
}

// Utility functions
function showLoading(show) {
    loadingEl.style.display = show ? 'flex' : 'none';
    if (show) {
        productsContainer.style.display = 'none';
        paginationEl.style.display = 'none';
    }
}

function showError(message) {
    errorContainer.innerHTML = `
        <div class="error">
            <h3>Error</h3>
            <p>${message}</p>
        </div>
    `;
}

function clearError() {
    errorContainer.innerHTML = '';
}