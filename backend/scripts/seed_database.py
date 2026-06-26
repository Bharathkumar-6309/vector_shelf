#!/usr/bin/env python3
"""
Production-quality seed script for generating 200,000 products.
Uses bulk insertion with PostgreSQL optimizations for maximum performance.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Tuple
from dataclasses import dataclass

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from faker import Faker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('seed_database.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
TOTAL_PRODUCTS = 200_000
BATCH_SIZE = 10_000  # Optimal batch size for PostgreSQL
CATEGORIES = [
    'Electronics',
    'Fashion',
    'Books',
    'Sports',
    'Home',
    'Beauty',
    'Automotive',
    'Toys'
]

@dataclass
class Product:
    """Data class for product generation."""
    name: str
    category: str
    price: float
    created_at: datetime
    updated_at: datetime


class DatabaseConnection:
    """Manages PostgreSQL database connection."""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection with performance optimizations."""
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        logger.info("Connecting to database...")
        self.conn = psycopg2.connect(
            db_url,
            connect_timeout=30,
            options="-c statement_timeout=300000"  # 5 minute timeout
        )
        self.cursor = self.conn.cursor()
        
        # Set connection parameters for bulk operations
        self.cursor.execute("SET synchronous_commit = OFF")
        self.cursor.execute("SET wal_level = minimal")
        self.cursor.execute("SET max_wal_senders = 0")
        
        logger.info("Database connected successfully")
        
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")


class ProductGenerator:
    """Generates product data using Faker."""
    
    def __init__(self):
        self.faker = Faker()
        # Seed for reproducibility
        Faker.seed(12345)
        
    def generate_product(self, index: int) -> Product:
        """Generate a single product with realistic data."""
        category = self.faker.random_element(CATEGORIES)
        
        # Generate product-specific data based on category
        if category == 'Electronics':
            name = self.faker.word() + ' ' + self.faker.word() + ' ' + self.faker.random_element(['Pro', 'Max', 'Ultra', 'Lite'])
            price = self.faker.pyfloat(min_value=50, max_value=2000, right_digits=2)
        elif category == 'Fashion':
            name = self.faker.word() + ' ' + self.faker.random_element(['Shirt', 'Pants', 'Dress', 'Jacket', 'Shoes'])
            price = self.faker.pyfloat(min_value=20, max_value=500, right_digits=2)
        elif category == 'Books':
            name = self.faker.sentence(nb_words=4)[:-1]  # Remove period
            price = self.faker.pyfloat(min_value=10, max_value=100, right_digits=2)
        elif category == 'Sports':
            name = self.faker.word() + ' ' + self.faker.random_element(['Ball', 'Gear', 'Equipment', 'Kit'])
            price = self.faker.pyfloat(min_value=30, max_value=800, right_digits=2)
        elif category == 'Home':
            name = self.faker.word() + ' ' + self.faker.random_element(['Furniture', 'Decor', 'Appliance', 'Set'])
            price = self.faker.pyfloat(min_value=25, max_value=1500, right_digits=2)
        elif category == 'Beauty':
            name = self.faker.word() + ' ' + self.faker.random_element(['Cream', 'Serum', 'Oil', 'Mask'])
            price = self.faker.pyfloat(min_value=15, max_value=300, right_digits=2)
        elif category == 'Automotive':
            name = self.faker.word() + ' ' + self.faker.random_element(['Part', 'Accessory', 'Tool', 'Kit'])
            price = self.faker.pyfloat(min_value=20, max_value=1000, right_digits=2)
        else:  # Toys
            name = self.faker.word() + ' ' + self.faker.random_element(['Toy', 'Game', 'Puzzle', 'Set'])
            price = self.faker.pyfloat(min_value=10, max_value=200, right_digits=2)
        
        # Generate timestamps spread over the last year
        days_ago = self.faker.random_int(min=0, max=365)
        created_at = datetime.now() - timedelta(days=days_ago)
        updated_at = created_at + timedelta(
            days=self.faker.random_int(min=0, max=days_ago),
            hours=self.faker.random_int(min=0, max=23)
        )
        
        return Product(
            name=name,
            category=category,
            price=price,
            created_at=created_at,
            updated_at=updated_at
        )
    
    def generate_batch(self, start_index: int, batch_size: int) -> List[Tuple]:
        """Generate a batch of products as tuples for bulk insertion."""
        products = []
        for i in range(start_index, start_index + batch_size):
            product = self.generate_product(i)
            products.append((
                product.name,
                product.category,
                product.price,
                product.created_at,
                product.updated_at
            ))
        return products


class ProductSeeder:
    """Handles bulk insertion of products into PostgreSQL."""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.generator = ProductGenerator()
        
    def prepare_table(self):
        """Prepare table for bulk insertion by disabling indexes and constraints."""
        logger.info("Preparing table for bulk insertion...")
        
        # Disable triggers and indexes temporarily
        self.db.cursor.execute("ALTER TABLE products DISABLE TRIGGER ALL")
        self.db.cursor.execute("SET session_replication_role = 'replica'")
        
        logger.info("Table prepared - indexes and triggers disabled")
        
    def restore_table(self):
        """Restore table indexes and constraints after insertion."""
        logger.info("Restoring table indexes and constraints...")
        
        # Re-enable triggers and indexes
        self.db.cursor.execute("SET session_replication_role = 'origin'")
        self.db.cursor.execute("ALTER TABLE products ENABLE TRIGGER ALL")
        
        # Analyze table to update statistics
        self.db.cursor.execute("ANALYZE products")
        
        logger.info("Table restored - indexes and constraints re-enabled")
        
    def insert_batch(self, products: List[Tuple]):
        """Insert a batch of products using execute_values for best bulk insert performance."""
        query = """
            INSERT INTO products (name, category, price, created_at, updated_at)
            VALUES %s
        """
        
        execute_values(
            self.db.cursor,
            query,
            products,
            template="(%s, %s, %s, %s, %s)",
            page_size=1000
        )
        
    def seed(self):
        """Seed database with 200,000 products using bulk insertion."""
        start_time = time.time()
        
        try:
            self.prepare_table()
            
            # Calculate number of batches
            num_batches = (TOTAL_PRODUCTS + BATCH_SIZE - 1) // BATCH_SIZE
            
            logger.info(f"Starting insertion of {TOTAL_PRODUCTS:,} products in {num_batches} batches")
            logger.info(f"Batch size: {BATCH_SIZE:,}")
            
            for batch_num in range(num_batches):
                batch_start = time.time()
                start_index = batch_num * BATCH_SIZE
                remaining = TOTAL_PRODUCTS - start_index
                current_batch_size = min(BATCH_SIZE, remaining)
                
                # Generate batch data
                products = self.generator.generate_batch(start_index, current_batch_size)
                
                # Insert batch
                self.insert_batch(products)
                
                # Commit after each batch
                self.db.conn.commit()
                
                # Log progress
                batch_time = time.time() - batch_start
                elapsed = time.time() - start_time
                inserted = start_index + current_batch_size
                progress = (inserted / TOTAL_PRODUCTS) * 100
                rate = inserted / elapsed if elapsed > 0 else 0
                
                logger.info(
                    f"Batch {batch_num + 1}/{num_batches} | "
                    f"Inserted: {inserted:,}/{TOTAL_PRODUCTS:,} ({progress:.1f}%) | "
                    f"Batch time: {batch_time:.2f}s | "
                    f"Elapsed: {elapsed:.1f}s | "
                    f"Rate: {rate:,.0f} products/sec"
                )
            
            self.restore_table()
            
            total_time = time.time() - start_time
            logger.info(f"✓ Successfully inserted {TOTAL_PRODUCTS:,} products in {total_time:.2f}s")
            logger.info(f"Average insertion rate: {TOTAL_PRODUCTS / total_time:,.0f} products/sec")
            
        except Exception as e:
            self.db.conn.rollback()
            logger.error(f"Error during seeding: {e}")
            raise


def verify_insertion(db_connection: DatabaseConnection):
    """Verify that the correct number of products were inserted."""
    logger.info("Verifying insertion...")
    
    db_connection.cursor.execute("SELECT COUNT(*) FROM products")
    count = db_connection.cursor.fetchone()[0]
    
    logger.info(f"Total products in database: {count:,}")
    
    if count == TOTAL_PRODUCTS:
        logger.info("✓ Verification successful")
    else:
        logger.error(f"✗ Verification failed: expected {TOTAL_PRODUCTS:,}, got {count:,}")
        sys.exit(1)
    
    # Show category distribution
    db_connection.cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM products 
        GROUP BY category 
        ORDER BY count DESC
    """)
    
    logger.info("Category distribution:")
    for row in db_connection.cursor.fetchall():
        logger.info(f"  {row[0]}: {row[1]:,}")


def main():
    """Main entry point for the seed script."""
    logger.info("=" * 60)
    logger.info("Product Database Seeding Script")
    logger.info("=" * 60)
    logger.info(f"Target: {TOTAL_PRODUCTS:,} products")
    logger.info(f"Categories: {len(CATEGORIES)}")
    logger.info(f"Batch size: {BATCH_SIZE:,}")
    logger.info("=" * 60)
    
    db_connection = None
    try:
        # Connect to database
        db_connection = DatabaseConnection()
        db_connection.connect()
        
        # Seed products
        seeder = ProductSeeder(db_connection)
        seeder.seed()
        
        # Verify insertion
        verify_insertion(db_connection)
        
        logger.info("=" * 60)
        logger.info("Seeding completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if db_connection:
            db_connection.disconnect()


if __name__ == "__main__":
    main()
