from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from contextlib import contextmanager, asynccontextmanager
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class Product(BaseModel):
    id: int
    cost: Optional[float] = None
    category: Optional[str] = None
    name: Optional[str] = None
    brand: Optional[str] = None
    retail_price: Optional[float] = None
    # Corrected: 'department' should be a string (the department name)
    # as it's likely stored as VARCHAR in the 'products' table.
    department: Optional[str] 
    sku: Optional[str] = None
    distribution_center_id: Optional[int] = None

class PaginationInfo(BaseModel):
    current_page: int
    total_pages: int
    total_products: int
    has_next_page: bool
    has_prev_page: bool
    limit: int
    offset: int

class ProductsResponse(BaseModel):
    success: bool
    data: dict

class ErrorResponse(BaseModel):
    success: bool
    error: str

class Department(BaseModel):
    id: int
    name: str
    product_count: int

class DepartmentList(BaseModel):
    departments: List[Department]

# Note: This Pydantic model is not directly used for the return type of
# /api/departments/{dept_id}/products if you only return IDs.
# It's kept for consistency with other parts of the application.
class DepartmentProducts(BaseModel):
    department: str
    products: List[Product]

# Database configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'your_database'), # Ensure this matches your actual DB name
    'user': os.getenv('DB_USER', 'your_username'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),
    'port': os.getenv('DB_PORT', '5432')
}

# Connection pool
connection_pool = None

# Use lifespan for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global connection_pool
    try:
        connection_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=20,
            **DATABASE_CONFIG
        )
        logger.info("Connected to PostgreSQL database")
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise
        
    yield  # This is where the application runs
    
    # Shutdown
    if connection_pool:
        connection_pool.closeall()
        logger.info("Database connections closed")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Products API",
    description="PostgreSQL Products API with pagination",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    "http://localhost:3000",    # React default
    "http://localhost:3001",
    "http://localhost:8080",    # Vue.js default
    "http://localhost:8081", 
    "http://localhost:4200",    # Angular default
    "http://localhost:5173",    # Vite default
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080", 
    "http://127.0.0.1:4200",
    "http://127.0.0.1:5173",
    # Add your production/staging domains
    # "https://yourdomain.com",
    # "https://www.yourdomain.com",
    # "https://api.yourdomain.com",
]

# Environment-based origins
def get_origins():
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env == "production":
        return [
            # Add only your production domains here
            # "https://yourdomain.com",
            # "https://www.yourdomain.com",
        ]
    elif env == "development":
        return origins + ["*"]  # Allow all in development
    else:
        return origins

# Choose your preferred approach
allowed_origins = get_origins()

# Add CORS middleware with comprehensive configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=[
        "GET", 
        "POST", 
        "PUT", 
        "DELETE", 
        "OPTIONS", 
        "PATCH", 
        "HEAD"
    ],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-API-Key",
        "Cache-Control",
        "X-CSRF-Token",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
    ],
    expose_headers=[
        "X-Total-Count",
        "X-Page-Count",
        "X-Per-Page", 
        "Content-Range",
        "X-Content-Range",
    ],
    max_age=3600,  # Cache preflight for 1 hour
)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    connection = None
    try:
        connection = connection_pool.getconn()
        yield connection
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection_pool.putconn(connection)

def get_product_count():
    """Get total count of products"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM products")
                result = cursor.fetchone()
                return result[0] if result else 0
    except psycopg2.Error as e:
        logger.error(f"Database error getting product count: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting product count: {e}")
        raise

def get_products_paginated(limit: int, offset: int):
    """Get products with pagination"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Modified to join with departments to get the department name
                query = """
                    SELECT p.id, p.cost, p.category, p.name, p.brand, p.retail_price, 
                           d.department_name as department, p.sku, p.distribution_center_id
                    FROM products p
                    LEFT JOIN departments d ON p.department = d.id  -- Assuming p.department in products table is the department ID
                    ORDER BY p.id ASC 
                    LIMIT %s OFFSET %s
                """
                cursor.execute(query, (limit, offset))
                return cursor.fetchall()
    except psycopg2.Error as e:
        logger.error(f"Database error getting paginated products: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting paginated products: {e}")
        raise

def get_product_by_id(product_id: int):
    """Get single product by ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Modified to join with departments to get the department name
                query = """
                    SELECT p.id, p.cost, p.category, p.name, p.brand, p.retail_price, 
                           d.department_name as department, p.sku, p.distribution_center_id
                    FROM products p
                    LEFT JOIN departments d ON p.department = d.id -- Assuming p.department in products table is the department ID
                    WHERE p.id = %s
                """
                cursor.execute(query, (product_id,))
                return cursor.fetchone()
    except psycopg2.Error as e:
        logger.error(f"Database error getting product by ID {product_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting product by ID {product_id}: {e}")
        raise

def get_all_departments():
    """
    Get all departments including their pre-calculated product count.
    This now directly selects from the 'departments' table.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT id, department_name as name, product_count
                    FROM departments
                    ORDER BY id
                """
                cursor.execute(query)
                return cursor.fetchall()
    except psycopg2.Error as e:
        logger.error(f"Database error getting departments: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting departments: {e}")
        raise

def get_department_by_id(dept_id: int):
    """
    Get a specific department by ID, including its pre-calculated product count.
    This now directly selects from the 'departments' table.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT id, department_name as name, product_count
                    FROM departments
                    WHERE id = %s
                """
                cursor.execute(query, (dept_id,))
                return cursor.fetchone()
    except psycopg2.Error as e:
        logger.error(f"Database error getting department {dept_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting department {dept_id}: {e}")
        raise

def get_products_by_department(dept_id: int):
    """Get all products in a department"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT p.id, p.cost, p.category, p.name, p.brand, p.retail_price,
                           d.department_name as department, -- Select department name from departments table
                           p.sku, p.distribution_center_id
                    FROM products p
                    JOIN departments d ON p.department = d.id -- Join on department ID
                    WHERE d.id = %s
                    ORDER BY p.id
                """
                cursor.execute(query, (dept_id,))
                return cursor.fetchall()
    except psycopg2.Error as e:
        logger.error(f"Database error getting products for department {dept_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting products for department {dept_id}: {e}")
        raise

@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {"message": "Products API", "version": "1.0.0"}

@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        return {
            "status": "OK", 
            "database": "connected",
            "timestamp": "2025-07-31T00:00:00Z"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "ERROR",
                "database": "disconnected",
                "error": str(e)
            }
        )

@app.get("/api/products", response_model=ProductsResponse)
async def get_products(
    page: int = Query(1, ge=1, description="Page number (minimum 1)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page (1-100)")
):
    """
    Get all products with pagination
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 10, max: 100)
    """
    # Additional validation for extreme values
    if page > 1000000:  # Prevent extremely large page numbers
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Page number is too large. Maximum allowed page is 1,000,000."
            }
        )
    
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get total count and products
        total_products = get_product_count()
        
        # Handle case when page exceeds available pages
        if total_products > 0:
            total_pages = (total_products + limit - 1) // limit
            if page > total_pages:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "success": False,
                        "error": f"Page {page} not found. Total available pages: {total_pages}."
                    }
                )
        else:
            # No products in database
            return ProductsResponse(
                success=True,
                data={
                    "products": [],
                    "pagination": {
                        "current_page": page,
                        "total_pages": 0,
                        "total_products": 0,
                        "has_next_page": False,
                        "has_prev_page": False,
                        "limit": limit,
                        "offset": offset
                    }
                }
            )
        
        products = get_products_paginated(limit, offset)
        
        # Calculate pagination metadata
        total_pages = (total_products + limit - 1) // limit  # Ceiling division
        has_next_page = page < total_pages
        has_prev_page = page > 1
        
        # Convert products to list of dictionaries
        products_list = []
        for product in products:
            product_dict = dict(product)
            # Convert datetime objects to strings if they exist
            if product_dict.get('created_at'):
                product_dict['created_at'] = str(product_dict['created_at'])
            if product_dict.get('updated_at'):
                product_dict['updated_at'] = str(product_dict['updated_at'])
            products_list.append(product_dict)
        
        return ProductsResponse(
            success=True,
            data={
                "products": products_list,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_products": total_products,
                    "has_next_page": has_next_page,
                    "has_prev_page": has_prev_page,
                    "limit": limit,
                    "offset": offset
                }
            }
        )
        
    except HTTPException:
        raise
    except psycopg2.Error as e:
        logger.error(f"Database error fetching products: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Database error occurred while fetching products."
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching products: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "An unexpected error occurred."
            }
        )

@app.get("/api/products/{product_id}", response_model=dict)
async def get_product(product_id: int):
    """
    Get single product by ID
    
    - **product_id**: Product ID
    """
    # Validate product ID
    if product_id <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid product ID. Product ID must be a positive integer."
            }
        )
    
    # Check for extremely large IDs that might cause issues
    if product_id > 2147483647:  # PostgreSQL INTEGER max value
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Product ID is too large."
            }
        )
    
    try:
        product = get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": f"Product with ID {product_id} not found."
                }
            )
        
        # Convert to dictionary and handle datetime
        product_dict = dict(product)
        if product_dict.get('created_at'):
            product_dict['created_at'] = str(product_dict['created_at'])
        if product_dict.get('updated_at'):
            product_dict['updated_at'] = str(product_dict['updated_at'])
        
        return {
            "success": True,
            "data": product_dict
        }
        
    except HTTPException:
        raise
    except psycopg2.Error as e:
        logger.error(f"Database error fetching product {product_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Database error occurred while fetching product."
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching product {product_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "An unexpected error occurred."
            }
        )

@app.get("/api/departments")
async def get_departments():
    """Get all departments with product count"""
    try:
        departments = get_all_departments()
        return {"departments": [dict(dept) for dept in departments]}
    except Exception as e:
        logger.error(f"Error fetching departments: {e}")
        raise HTTPException(status_code=500, detail="Error fetching departments")

@app.get("/api/departments/{dept_id}")
async def get_department(dept_id: int):
    """Get specific department details"""
    try:
        department = get_department_by_id(dept_id)
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        return dict(department)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching department {dept_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching department")

@app.get("/api/departments/{dept_id}/products")
async def get_department_products(dept_id: int):
    """Get all products in a department"""
    try:
        department = get_department_by_id(dept_id)
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        products = get_products_by_department(dept_id)
        
        # Convert products to list of dictionaries (full details)
        products_list = []
        for product in products:
            product_dict = dict(product)
            # Convert datetime objects to strings if they exist
            if product_dict.get('created_at'):
                product_dict['created_at'] = str(product_dict['created_at'])
            if product_dict.get('updated_at'):
                product_dict['updated_at'] = str(product_dict['updated_at'])
            products_list.append(product_dict)

        return {
            "department": department['name'], # Return department NAME
            "products": products_list         # Return list of FULL product objects
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching products for department {dept_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching department products")

@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Invalid input parameters",
            "details": exc.errors() if hasattr(exc, 'errors') else str(exc)
        }
    )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint not found"
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )
