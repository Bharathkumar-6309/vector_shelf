"""Unit tests for cursor utilities."""

import pytest
from datetime import datetime
from app.utils.cursor import create_cursor, decode_cursor


class TestCreateCursor:
    """Tests for create_cursor function."""
    
    def test_create_cursor_basic(self):
        """Test basic cursor creation."""
        updated_at = datetime(2024, 1, 20, 14, 30, 45)
        product_id = 12345
        snapshot_at = datetime(2024, 1, 20, 14, 30, 45)
        
        cursor = create_cursor(updated_at, product_id, snapshot_at)
        
        assert cursor is not None
        assert isinstance(cursor, str)
        # Base64 encoded strings are URL-safe
        assert "+" not in cursor or "=" in cursor
    
    def test_create_cursor_different_timestamps(self):
        """Test cursor with different timestamps."""
        updated_at = datetime(2024, 1, 20, 10, 0, 0)
        product_id = 99999
        snapshot_at = datetime(2024, 1, 20, 15, 0, 0)
        
        cursor = create_cursor(updated_at, product_id, snapshot_at)
        
        assert cursor is not None
        assert isinstance(cursor, str)
    
    def test_create_cursor_consistency(self):
        """Test that same inputs produce same cursor."""
        updated_at = datetime(2024, 1, 20, 14, 30, 45)
        product_id = 12345
        snapshot_at = datetime(2024, 1, 20, 14, 30, 45)
        
        cursor1 = create_cursor(updated_at, product_id, snapshot_at)
        cursor2 = create_cursor(updated_at, product_id, snapshot_at)
        
        assert cursor1 == cursor2


class TestDecodeCursor:
    """Tests for decode_cursor function."""
    
    def test_decode_cursor_basic(self):
        """Test basic cursor decoding."""
        updated_at = datetime(2024, 1, 20, 14, 30, 45)
        product_id = 12345
        snapshot_at = datetime(2024, 1, 20, 14, 30, 45)
        
        cursor = create_cursor(updated_at, product_id, snapshot_at)
        decoded = decode_cursor(cursor)
        
        assert decoded is not None
        assert "updated_at" in decoded
        assert "id" in decoded
        assert "snapshot_at" in decoded
        assert decoded["id"] == product_id
        assert decoded["updated_at"] == updated_at
        assert decoded["snapshot_at"] == snapshot_at
    
    def test_decode_cursor_roundtrip(self):
        """Test that decode reverses create_cursor."""
        updated_at = datetime(2024, 1, 20, 10, 15, 30, 123456)
        product_id = 54321
        snapshot_at = datetime(2024, 1, 20, 10, 20, 0)
        
        cursor = create_cursor(updated_at, product_id, snapshot_at)
        decoded = decode_cursor(cursor)
        
        assert decoded["updated_at"] == updated_at
        assert decoded["id"] == product_id
        assert decoded["snapshot_at"] == snapshot_at
    
    def test_decode_cursor_invalid_base64(self):
        """Test decoding invalid base64 string."""
        with pytest.raises(ValueError, match="Invalid cursor format"):
            decode_cursor("invalid_base64_string!!!")
    
    def test_decode_cursor_invalid_format(self):
        """Test decoding cursor with wrong number of components."""
        # Create a cursor with only 2 components
        cursor = "2024-01-20T14:30:45|12345"
        encoded = cursor.encode().decode()  # Not actually base64, but testing logic
        
        with pytest.raises(ValueError, match="Invalid cursor format"):
            decode_cursor(encoded)
    
    def test_decode_cursor_invalid_timestamp(self):
        """Test decoding cursor with invalid timestamp."""
        # Manually create an invalid cursor
        import base64
        invalid_cursor = base64.b64encode(b"invalid_timestamp|12345|2024-01-20T14:30:45").decode()
        
        with pytest.raises(ValueError, match="Invalid cursor format"):
            decode_cursor(invalid_cursor)
    
    def test_decode_cursor_invalid_id(self):
        """Test decoding cursor with invalid ID."""
        import base64
        invalid_cursor = base64.b64encode(b"2024-01-20T14:30:45|invalid_id|2024-01-20T14:30:45").decode()
        
        with pytest.raises(ValueError, match="Invalid cursor format"):
            decode_cursor(invalid_cursor)
