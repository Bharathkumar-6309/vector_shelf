"""Cursor encoding and decoding utilities for pagination."""

import base64
from datetime import datetime
from typing import Dict


def create_cursor(updated_at: datetime, id: int, snapshot_at: datetime) -> str:
    """
    Create a cursor string from pagination parameters.
    
    Args:
        updated_at: Last item's updated timestamp
        id: Last item's ID
        snapshot_at: Snapshot timestamp for consistency
        
    Returns:
        Base64-encoded cursor string
    """
    cursor_string = f"{updated_at.isoformat()}|{id}|{snapshot_at.isoformat()}"
    return base64.b64encode(cursor_string.encode()).decode()


def decode_cursor(cursor: str) -> Dict[str, any]:
    """
    Decode a cursor string into its components.
    
    Args:
        cursor: Base64-encoded cursor string
        
    Returns:
        Dictionary with updated_at, id, and snapshot_at
        
    Raises:
        ValueError: If cursor is invalid or malformed
    """
    try:
        cursor_string = base64.b64decode(cursor).decode()
        parts = cursor_string.split("|")
        
        if len(parts) != 3:
            raise ValueError("Cursor must contain 3 components")
        
        updated_at_str, id_str, snapshot_at_str = parts
        
        return {
            "updated_at": datetime.fromisoformat(updated_at_str),
            "id": int(id_str),
            "snapshot_at": datetime.fromisoformat(snapshot_at_str)
        }
    except Exception as e:
        raise ValueError(f"Invalid cursor format: {e}")
