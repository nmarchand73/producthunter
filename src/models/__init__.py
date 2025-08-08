"""
Data models for ProductHunt data structures.

Defines the JSON schema and data validation for products and market data.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime
import json


@dataclass
class Product:
    """Data model for a ProductHunt product."""
    name: str
    tagline: str
    votes: int
    comments: int
    url: str
    maker: str
    category: str
    launched_at: str
    competitive_score: Optional[float] = None
    ai_analysis: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MarketSummary:
    """Data model for market summary with AI analysis."""
    total_products: int
    trending_categories: List[str]
    top_product: Dict
    ai_market_analysis: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DailyReport:
    """Complete daily report structure."""
    date: str
    market_summary: MarketSummary
    products: List[Product]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "date": self.date,
            "market_summary": self.market_summary.to_dict(),
            "products": [product.to_dict() for product in self.products]
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def save_to_file(self, filepath: str) -> None:
        """Save report to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())


def create_daily_report(date: str, products_data: List[Dict]) -> DailyReport:
    """Create a DailyReport from raw product data.
    
    Args:
        date: Date string in YYYY-MM-DD format
        products_data: List of product dictionaries
        
    Returns:
        DailyReport instance
    """
    # Convert raw data to Product objects
    products = [Product(**product_data) for product_data in products_data]
    
    # Calculate market summary
    total_products = len(products)
    
    # Get trending categories (top 3 by frequency)
    category_counts = {}
    for product in products:
        category = product.category
        category_counts[category] = category_counts.get(category, 0) + 1
    
    trending_categories = sorted(category_counts.keys(), 
                               key=lambda x: category_counts[x], 
                               reverse=True)[:3]
    
    # Find top product by votes
    top_product_obj = max(products, key=lambda p: p.votes) if products else None
    top_product = {
        "name": top_product_obj.name if top_product_obj else "",
        "votes": top_product_obj.votes if top_product_obj else 0,
        "category": top_product_obj.category if top_product_obj else ""
    }
    
    # Create market summary
    market_summary = MarketSummary(
        total_products=total_products,
        trending_categories=trending_categories,
        top_product=top_product
    )
    
    # Create and return daily report
    return DailyReport(
        date=date,
        market_summary=market_summary,
        products=products
    )
