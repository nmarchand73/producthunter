#!/usr/bin/env python3
"""
ProductHunt Daily Recap CLI Tool - Main Entry Point

A command-line tool that scrapes ProductHunt daily products and provides
AI-powered analysis for entrepreneurs.
"""

import click
import logging
import sys
import json
from datetime import datetime
from pathlib import Path

from scraper import ProductHuntScraper
from models import create_daily_report
from config import load_config, validate_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('producthunt-recap.log')
    ]
)

logger = logging.getLogger(__name__)


def load_categories_data():
    """Load ProductHunt categories data from JSON file."""
    try:
        categories_file = Path(__file__).parent.parent / "data" / "categories.json"
        with open(categories_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Categories file not found. Using basic category mapping.")
        return {
            "display_to_url_mapping": {
                "engineering & development": "engineering-development",
                "developer tools": "engineering-development",
                "design & creative": "design-creative",
                "work & productivity": "work-productivity"
            },
            "url_to_display_mapping": {
                "engineering-development": "Engineering & Development",
                "design-creative": "Design & Creative",
                "work-productivity": "Work & Productivity"
            }
        }
    except Exception as e:
        logger.error(f"Error loading categories data: {e}")
        return {"display_to_url_mapping": {}, "url_to_display_mapping": {}}


def normalize_category_name(category_name):
    """Convert category names between display format and URL format.
    
    Args:
        category_name: Category name in either format
        
    Returns:
        Normalized category name for ProductHunt URL or display format
    """
    if not category_name:
        return None
    
    categories_data = load_categories_data()
    category_lower = category_name.lower().strip()
    
    # Check if it's already a valid URL-style category
    if category_lower in categories_data.get("url_to_display_mapping", {}):
        return category_lower
    
    # Check display to URL mapping
    if category_lower in categories_data.get("display_to_url_mapping", {}):
        return categories_data["display_to_url_mapping"][category_lower]
    
    # Fallback: basic normalization for unknown categories
    import re
    normalized = re.sub(r'[^\w\s-]', '', category_lower)
    normalized = re.sub(r'\s+', '-', normalized.strip())
    normalized = re.sub(r'-+', '-', normalized)
    return normalized.strip('-')


def get_category_display_name(category_url_name):
    """Get the display name for a category URL name."""
    categories_data = load_categories_data()
    return categories_data.get("url_to_display_mapping", {}).get(category_url_name, category_url_name)


def find_products_by_category(products_data, category_filter):
    """Find products matching a category filter.
    
    Args:
        products_data: List of product dictionaries
        category_filter: Category name in any supported format
        
    Returns:
        List of matching products
    """
    if not category_filter:
        return products_data
    
    # Normalize the filter
    normalized_filter = normalize_category_name(category_filter)
    
    # Find matching products
    filtered_products = []
    for product in products_data:
        product_category = product.get('category', '').lower()
        normalized_product_category = normalize_category_name(product_category)
        
        if normalized_product_category == normalized_filter:
            filtered_products.append(product)
    
    return filtered_products


def display_product_ranking(products_data, title="Product Ranking (by votes)", category_filter=None):
    """Display products ranked by votes in descending order.
    
    Args:
        products_data: List of product dictionaries
        title: Title to display for the ranking
        category_filter: Optional category to filter by (supports both display names and URL-style names)
    """
    # Filter by category if specified
    if category_filter:
        filtered_products = find_products_by_category(products_data, category_filter)
        if not filtered_products:
            available_categories = sorted(set(p.get('category', 'Unknown') for p in products_data))
            click.echo(f"❌ No products found in category '{category_filter}'")
            click.echo(f"📁 Available categories: {', '.join(available_categories)}")
            click.echo(f"💡 Tip: You can also use URL-style names like 'engineering-development' for 'Developer Tools'")
            return
        products_data = filtered_products
        title = f"Product Ranking in '{category_filter}' (by votes)"
    
    click.echo(f"\n🏆 {title}:")
    click.echo("=" * 60)
    
    # Sort products by votes in descending order
    sorted_products = sorted(products_data, key=lambda x: x.get('votes', 0), reverse=True)
    
    for i, product in enumerate(sorted_products, 1):
        votes = product.get('votes', 0)
        name = product.get('name', 'Unknown Product')
        tagline = product.get('tagline', 'No tagline available')
        category = product.get('category', 'Uncategorized')
        url = product.get('url', 'No URL available')
        
        # Truncate tagline if too long
        if len(tagline) > 60:
            tagline = tagline[:57] + "..."
        
        click.echo(f"{i:2}. 🗳️  {votes:3} votes | {name}")
        click.echo(f"    📝 {tagline}")
        click.echo(f"    🏷️  {category}")
        click.echo(f"    🔗 {url}")
        click.echo()


@click.group()
def cli():
    """ProductHunt Daily Recap CLI Tool with AI Analysis."""
    pass


@cli.command()
@click.option('--date', type=str, default=None, 
              help='Specific date to list categories for (YYYY-MM-DD format)')
@click.option('--data-dir', type=click.Path(), default='./data', 
              help='Directory to read data files from')
def categories(date, data_dir):
    """List all available product categories from existing data files."""
    
    # Parse date
    target_date = datetime.now().strftime('%Y-%m-%d') if date is None else date
    
    # Look for data file
    data_path = Path(data_dir)
    data_filename = f"market-intel-{target_date}.json"
    data_filepath = data_path / data_filename
    
    if not data_filepath.exists():
        click.echo(f"❌ No data file found for {target_date}")
        click.echo(f"   Looking for: {data_filepath}")
        
        # List available files
        available_files = list(data_path.glob("market-intel-*.json"))
        if available_files:
            click.echo("\n📁 Available data files:")
            for file in sorted(available_files):
                click.echo(f"   - {file.name}")
        
        sys.exit(1)
    
    try:
        # Load and analyze data
        with open(data_filepath, 'r') as f:
            data = json.load(f)
        
        products = data.get('products', [])
        if not products:
            click.echo(f"❌ No products found in {data_filename}")
            sys.exit(1)
        
        # Count products by category
        category_counts = {}
        for product in products:
            category = product.get('category', 'Unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        click.echo(f"📅 ProductHunt Categories for {target_date}")
        click.echo("🏷️  Available Categories:")
        click.echo("=" * 50)
        
        # Sort by product count (descending)
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        
        for i, (category, count) in enumerate(sorted_categories, 1):
            plural = "product" if count == 1 else "products"
            click.echo(f"{i:2}. {category:<20} ({count} {plural})")
        
        click.echo(f"\n📊 Total: {len(sorted_categories)} categories, {len(products)} products")
        
    except json.JSONDecodeError:
        click.echo(f"❌ Invalid JSON file: {data_filepath}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error reading data: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--date', type=str, default=None, 
              help='Specific date to show ranking for (YYYY-MM-DD format)')
@click.option('--data-dir', type=click.Path(), default='./data', 
              help='Directory to read data files from')
@click.option('--category', type=str, default=None,
              help='Filter products by category using URL-style names (e.g., "engineering-development", "social-media") or display names ("Developer Tools")')
def ranking(date, data_dir, category):
    """Display product ranking from existing data files."""
    
    # Parse date
    target_date = datetime.now().strftime('%Y-%m-%d') if date is None else date
    
    # Look for data file
    data_path = Path(data_dir)
    data_filename = f"market-intel-{target_date}.json"
    data_filepath = data_path / data_filename
    
    if not data_filepath.exists():
        click.echo(f"❌ No data file found for {target_date}")
        click.echo(f"   Looking for: {data_filepath}")
        
        # List available files
        available_files = list(data_path.glob("market-intel-*.json"))
        if available_files:
            click.echo("\n📁 Available data files:")
            for file in sorted(available_files):
                click.echo(f"   - {file.name}")
        
        sys.exit(1)
    
    try:
        # Load and display data
        with open(data_filepath, 'r') as f:
            data = json.load(f)
        
        products = data.get('products', [])
        if not products:
            click.echo(f"❌ No products found in {data_filename}")
            sys.exit(1)
        
        click.echo(f"📅 ProductHunt Ranking for {target_date}")
        
        # Check if category filter will return results before displaying
        if category:
            filtered_products = find_products_by_category(products, category)
            if not filtered_products:
                available_categories = sorted(set(p.get('category', 'Unknown') for p in products))
                click.echo(f"❌ No products found in category '{category}'")
                click.echo(f"📁 Available categories: {', '.join(available_categories)}")
                click.echo(f"💡 Tip: You can also use URL-style names like 'engineering-development' for 'Developer Tools'")
                return
        
        display_product_ranking(products, category_filter=category)
        
        # Show summary
        filtered_products = products
        if category:
            filtered_products = find_products_by_category(products, category)
        
        total_products = len(filtered_products)
        total_votes = sum(p.get('votes', 0) for p in filtered_products)
        avg_votes = total_votes / total_products if total_products > 0 else 0
        
        summary_title = f"📊 Summary for '{category}' category:" if category else "📊 Summary:"
        click.echo(f"\n{summary_title}")
        click.echo(f"   - Total Products: {total_products}")
        click.echo(f"   - Total Votes: {total_votes:,}")
        click.echo(f"   - Average Votes: {avg_votes:.1f}")
        
        if not category:
            # Show available categories
            available_categories = sorted(set(p.get('category', 'Unknown') for p in products))
            click.echo(f"   - Available Categories: {', '.join(available_categories)}")
        
    except json.JSONDecodeError:
        click.echo(f"❌ Invalid JSON file: {data_filepath}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error reading data: {str(e)}")
        sys.exit(1)


@cli.command(name="scrape")
@click.option('--ai-analysis', is_flag=True, default=False, 
              help='Enable AI analysis of products and market trends')
@click.option('--mode', type=click.Choice(['quick', 'detailed', 'market-focus']), 
              default='quick', help='AI analysis depth mode')
@click.option('--date', type=str, default=None, 
              help='Specific date to analyze (YYYY-MM-DD format)')
@click.option('--output-dir', type=click.Path(), default='./data', 
              help='Directory to save output files')
@click.option('--category', type=str, default=None,
              help='Filter ranking by category using URL-style names (e.g., "engineering-development", "social-media") or display names ("Developer Tools")')
@click.option('--quiet', is_flag=True, default=False, 
              help='Suppress output except errors')
@click.option('--verbose', is_flag=True, default=False, 
              help='Enable verbose logging')
def main(ai_analysis, mode, date, output_dir, category, quiet, verbose):
    """ProductHunt Daily Recap CLI Tool with AI Analysis.
    
    Scrapes ProductHunt daily products and optionally analyzes them
    with AI to provide market intelligence for entrepreneurs.
    """
    
    # Configure logging based on flags
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting ProductHunt Daily Recap CLI Tool")
    logger.info(f"AI Analysis: {'Enabled' if ai_analysis else 'Disabled'}")
    
    if ai_analysis:
        logger.info(f"Analysis Mode: {mode}")
    
    # Parse date
    target_date = datetime.now().strftime('%Y-%m-%d') if date is None else date
    logger.info(f"Target Date: {target_date}")
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output Directory: {output_path.absolute()}")
    
    try:
        # Load configuration
        config = load_config()
        validate_config(config)
        
        # Initialize scraper
        scraper = ProductHuntScraper(
            delay=config.scraping_delay,
            max_retries=config.max_retries
        )
        
        # Start scraping
        logger.info("Starting ProductHunt scraping...")
        click.echo("🚀 ProductHunt Daily Recap CLI Tool")
        click.echo(f"📅 Date: {target_date}")
        click.echo(f"🤖 AI Analysis: {'✅ Enabled' if ai_analysis else '❌ Disabled'}")
        
        if ai_analysis:
            click.echo(f"🎯 Mode: {mode}")
        
        click.echo(f"📁 Output: {output_path.absolute()}")
        
        # Scrape products
        click.echo("🔍 Scraping ProductHunt products...")
        products_data = scraper.scrape_daily_products(target_date)
        
        if not products_data:
            click.echo("⚠️  No products found for the specified date")
            logger.warning(f"No products found for date: {target_date}")
            return
        
        click.echo(f"✅ Found {len(products_data)} products")
        
        # Create daily report
        daily_report = create_daily_report(target_date, products_data)
        
        # TODO: Add AI analysis here when implemented
        if ai_analysis:
            click.echo(f"🤖 AI analysis would be performed here (mode: {mode})")
            logger.info(f"AI analysis skipped - not yet implemented")
        
        # Save to file
        output_filename = f"market-intel-{target_date}.json"
        output_filepath = output_path / output_filename
        
        daily_report.save_to_file(str(output_filepath))
        
        click.echo(f"💾 Report saved: {output_filepath}")
        click.echo(f"📊 Market Summary:")
        click.echo(f"   - Total Products: {daily_report.market_summary.total_products}")
        click.echo(f"   - Top Categories: {', '.join(daily_report.market_summary.trending_categories)}")
        
        if daily_report.market_summary.top_product['name']:
            click.echo(f"   - Top Product: {daily_report.market_summary.top_product['name']} ({daily_report.market_summary.top_product['votes']} votes)")
        
        # Always display product ranking (default behavior)
        display_product_ranking(products_data, category_filter=category)
        
        logger.info("ProductHunt scraping completed successfully")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--format', type=click.Choice(['list', 'json', 'detailed']), default='list',
              help='Output format for categories')
def categories(format):
    """List all available ProductHunt categories and subcategories."""
    try:
        categories_data = load_categories_data()
        
        if format == 'json':
            click.echo(json.dumps(categories_data, indent=2))
            return
        
        main_categories = categories_data.get('categories', {})
        
        if format == 'detailed':
            click.echo("🏷️  ProductHunt Categories (Detailed)")
            click.echo("=" * 60)
            
            for url_name, category_info in main_categories.items():
                display_name = category_info.get('display_name', url_name)
                description = category_info.get('description', 'No description available')
                subcategories = category_info.get('subcategories', [])
                
                click.echo(f"\n📁 {display_name}")
                click.echo(f"   URL: {url_name}")
                click.echo(f"   Description: {description}")
                if subcategories:
                    click.echo(f"   Subcategories ({len(subcategories)}): {', '.join(subcategories[:5])}")
                    if len(subcategories) > 5:
                        click.echo(f"   ... and {len(subcategories) - 5} more")
                
        else:  # list format
            click.echo("🏷️  ProductHunt Categories")
            click.echo("=" * 50)
            click.echo("Use these category names with the --category option:")
            click.echo("")
            
            for i, (url_name, category_info) in enumerate(main_categories.items(), 1):
                display_name = category_info.get('display_name', url_name)
                subcategories = category_info.get('subcategories', [])
                subcat_count = len(subcategories)
                
                click.echo(f"{i:2}. {display_name:<25} (URL: {url_name})")
                if subcat_count > 0:
                    click.echo(f"    └─ {subcat_count} subcategories")
            
            click.echo(f"\n📊 Total: {len(main_categories)} main categories")
            click.echo("\n💡 Examples:")
            click.echo("   python src/main.py ranking --category engineering-development")
            click.echo("   python src/main.py ranking --category \"Design & Creative\"")
            click.echo("   python src/main.py scrape --category ai-software")
        
    except Exception as e:
        click.echo(f"❌ Error loading categories: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
