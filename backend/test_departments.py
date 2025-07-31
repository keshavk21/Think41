import requests
import json

# Base URL for your API
BASE_URL = "http://localhost:8000"

def test_departments_api():
    """Test all department endpoints"""
    
    print("Testing Department APIs")
    print("=" * 50)
    
    # Test 1: Get all departments
    print("\n1. Testing GET /api/departments")
    try:
        response = requests.get(f"{BASE_URL}/api/departments")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Get specific department (assuming department ID 1 exists)
    print("\n2. Testing GET /api/departments/1")
    try:
        response = requests.get(f"{BASE_URL}/api/departments/1")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Get products in department
    print("\n3. Testing GET /api/departments/1/products")
    try:
        response = requests.get(f"{BASE_URL}/api/departments/1/products")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Department: {data.get('department')}")
            print(f"Number of products: {len(data.get('products', []))}")
            # Show first 2 products only
            products = data.get('products', [])[:2]
            print(f"Sample products: {json.dumps(products, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Test non-existent department
    print("\n4. Testing GET /api/departments/999 (non-existent)")
    try:
        response = requests.get(f"{BASE_URL}/api/departments/999")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_departments_api()