"""Integration tests for the Product API endpoints."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from app.models.product import Product
from app.utils.cursor import decode_cursor


def test_first_page_load(test_client, sample_products):
    """Test loading the first page of products."""
    limit = 10
    response = test_client.get(f"/api/v1/products?limit={limit}")
    
    assert response.status_code == 200
    res_data = response.json()
    
    # 1. Verify structure and data size
    assert "products" in res_data
    assert "pagination" in res_data
    assert "snapshot" in res_data
    
    assert len(res_data["products"]) == limit
    
    # Verify pagination metadata
    pagination = res_data["pagination"]
    assert pagination["limit"] == limit
    assert pagination["has_next"] is True
    assert pagination["next_cursor"] is not None
    
    # Verify snapshot metadata
    assert res_data["snapshot"] is not None
    assert res_data["category"] is None


def test_second_page_cursor(test_client, sample_products):
    """Test loading the second page of products using a cursor."""
    limit = 10
    
    # Load first page
    response1 = test_client.get(f"/api/v1/products?limit={limit}")
    assert response1.status_code == 200
    res_data1 = response1.json()
    page1_ids = {p["id"] for p in res_data1["products"]}
    next_cursor = res_data1["pagination"]["next_cursor"]
    snapshot = res_data1["snapshot"]
    
    # Load second page
    response2 = test_client.get(f"/api/v1/products?limit={limit}&cursor={next_cursor}&snapshot={snapshot}")
    assert response2.status_code == 200
    res_data2 = response2.json()
    page2_ids = {p["id"] for p in res_data2["products"]}
    
    # 2. Verify second page has the correct number of items and no overlaps
    assert len(res_data2["products"]) == limit
    assert len(page1_ids.intersection(page2_ids)) == 0
    
    # Verify ordering of products across pages (newest-first: updated_at desc, id desc)
    all_products = res_data1["products"] + res_data2["products"]
    for i in range(len(all_products) - 1):
        curr = all_products[i]
        nxt = all_products[i + 1]
        curr_updated_at = datetime.fromisoformat(curr["updated_at"].replace("Z", "+00:00"))
        nxt_updated_at = datetime.fromisoformat(nxt["updated_at"].replace("Z", "+00:00"))
        assert curr_updated_at >= nxt_updated_at
        if curr_updated_at == nxt_updated_at:
            assert curr["id"] > nxt["id"]


def test_category_filter(test_client, sample_products):
    """Test filtering products by category."""
    category = "Electronics"
    response = test_client.get(f"/api/v1/products?category={category}")
    
    assert response.status_code == 200
    res_data = response.json()
    
    # 3. Verify category filter works and metadata returns correct category
    assert len(res_data["products"]) > 0
    for product in res_data["products"]:
        assert product["category"] == category
    assert res_data["category"] == category


def test_empty_category(test_client, sample_products):
    """Test filtering by an empty/non-existent category."""
    category = "NonExistentCategory"
    response = test_client.get(f"/api/v1/products?category={category}")
    
    assert response.status_code == 200
    res_data = response.json()
    
    # 4. Verify result is empty and has_next is False with None next_cursor
    assert len(res_data["products"]) == 0
    assert res_data["pagination"]["has_next"] is False
    assert res_data["pagination"]["next_cursor"] is None
    assert res_data["category"] == category


def test_invalid_cursor(test_client):
    """Test using an invalid/malformed cursor."""
    snapshot = datetime.utcnow().isoformat()
    response = test_client.get(f"/api/v1/products?cursor=invalid_cursor_string&snapshot={snapshot}")
    
    # 5. Verify invalid cursor returns 400 Bad Request
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Invalid cursor" in response.json()["detail"]


def test_snapshot_consistency(test_client, test_db, sample_products):
    """Test snapshot consistency when new records are added mid-pagination."""
    limit = 10
    
    # Load first page
    response1 = test_client.get(f"/api/v1/products?limit={limit}")
    assert response1.status_code == 200
    res_data1 = response1.json()
    next_cursor = res_data1["pagination"]["next_cursor"]
    snapshot_at_str = res_data1["snapshot"]
    snapshot_at = datetime.fromisoformat(snapshot_at_str.replace("Z", "+00:00"))
    
    # Add a new product with a newer timestamp (which would normally rank first)
    new_product_time = snapshot_at + timedelta(minutes=5)
    new_product = Product(
        name="Newly Added Consistent Product",
        category="Electronics",
        price=Decimal("99.99"),
        created_at=new_product_time,
        updated_at=new_product_time
    )
    test_db.add(new_product)
    test_db.commit()
    
    # Fetch page 2 using the original cursor
    response2 = test_client.get(f"/api/v1/products?limit={limit}&cursor={next_cursor}&snapshot={snapshot_at_str}")
    assert response2.status_code == 200
    res_data2 = response2.json()
    
    # 6. Verify that the new product is NOT returned on the second page
    # because it was created after the snapshot timestamp.
    page2_ids = {p["id"] for p in res_data2["products"]}
    assert new_product.id not in page2_ids
    
    # Verify that the snapshot timestamp remains consistent in page 2 response
    assert res_data2["snapshot"] == snapshot_at_str


def test_duplicate_prevention(test_client, sample_products_with_same_timestamp):
    """Test duplicate prevention when multiple products have the same timestamp."""
    limit = 5
    retrieved_ids = []
    cursor = None
    
    # Retrieve all pages of products with the same timestamp
    has_more = True
    page_count = 0
    
    snapshot = None
    while has_more:
        url = f"/api/v1/products?limit={limit}"
        if cursor:
            url += f"&cursor={cursor}&snapshot={snapshot}"
        response = test_client.get(url)
        assert response.status_code == 200
        res_data = response.json()
        if snapshot is None:
            snapshot = res_data["snapshot"]
        
        page_ids = [p["id"] for p in res_data["products"]]
        retrieved_ids.extend(page_ids)
        
        cursor = res_data["pagination"]["next_cursor"]
        has_more = res_data["pagination"]["has_next"]
        page_count += 1
        
        # Prevent infinite loop in test failure
        assert page_count <= 10
        
    # 7. Verify all 20 products are returned exactly once, meaning no duplicates or gaps
    assert len(retrieved_ids) == 20
    assert len(set(retrieved_ids)) == 20


def test_missing_record_prevention(test_client, test_db, sample_products):
    """Test that deletion of records on page 1 does not skip records on page 2."""
    limit = 10
    
    # 1. Fetch first page
    response1 = test_client.get(f"/api/v1/products?limit={limit}")
    assert response1.status_code == 200
    res_data1 = response1.json()
    page1_products = res_data1["products"]
    next_cursor = res_data1["pagination"]["next_cursor"]
    snapshot = res_data1["snapshot"]
    
    # Determine what the first product on page 2 should be BEFORE deletion
    # We fetch page 2 directly without deleting anything first to find the expected record
    response2_pre = test_client.get(f"/api/v1/products?limit={limit}&cursor={next_cursor}&snapshot={snapshot}")
    assert response2_pre.status_code == 200
    expected_first_on_page2 = response2_pre.json()["products"][0]
    
    # 2. Delete a product from page 1 data in the database
    product_to_delete_id = page1_products[4]["id"]
    product_to_delete = test_db.query(Product).filter(Product.id == product_to_delete_id).first()
    assert product_to_delete is not None
    test_db.delete(product_to_delete)
    test_db.commit()
    
    # 3. Fetch second page using the original next_cursor
    response2_post = test_client.get(f"/api/v1/products?limit={limit}&cursor={next_cursor}&snapshot={snapshot}")
    assert response2_post.status_code == 200
    res_data2 = response2_post.json()
    
    # 8. Verify the first product on page 2 is exactly what was expected (no records were skipped)
    assert res_data2["products"][0]["id"] == expected_first_on_page2["id"]
