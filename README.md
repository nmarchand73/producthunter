# ProductHunt Daily Recap CLI Tool with AI Analysis

A Python command-line tool that automatically scrapes ProductHunt website daily to capture and save product information in JSON format, enhanced with Anthropic Claude AI analysis for deep company insights, specifically designed for entrepreneurs to track market trends and competitive landscape.

## 🚀 Features

- **Daily Market Intelligence**: Automatically capture ProductHunt's daily featured products
- **AI-Powered Company Analysis**: Leverage Anthropic Claude for deep company and market insights
- **Structured Data Export**: Save insights in JSON format with comprehensive AI analysis
- **Simple CLI Operation**: One-command execution with optional AI analysis modes
- **Entrepreneur-Focused**: Designed for competitive intelligence and strategic decision-making

## 📦 Installation

### Prerequisites
- Python 3.8+
- Anthropic API key (for AI analysis)

### Setup

```bash
# Clone the repository
git clone https://github.com/nmarchand73/producthunter.git
cd producthunter

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Anthropic API key
```

## 🔧 Configuration

Create a `.env` file from `.env.example` and configure:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
AI_ANALYSIS_MODE=quick
MAX_DAILY_AI_COST=10.00
OUTPUT_DIR=./data
```

## 💻 Usage

### Basic Commands

```bash
# Basic scraping without AI analysis
python src/main.py

# With AI analysis (quick mode)
python src/main.py --ai-analysis

# Detailed AI analysis
python src/main.py --ai-analysis --mode detailed

# Quiet mode for automation
python src/main.py --ai-analysis --quiet

# Custom date and output directory
python src/main.py --date 2025-08-07 --output-dir ./custom-data
```

### Command Options

- `--ai-analysis`: Enable AI analysis of products and market trends
- `--mode [quick|detailed|market-focus]`: Set AI analysis depth (default: quick)
- `--date YYYY-MM-DD`: Analyze specific date (default: today)
- `--output-dir PATH`: Custom output directory (default: ./data)
- `--quiet`: Suppress output except errors
- `--verbose`: Enable detailed logging

## 📊 Output Format

The tool generates daily JSON files named `market-intel-YYYY-MM-DD.json` containing:

- **Market Summary**: AI-generated trends, opportunities, and competitive landscape
- **Product Details**: Complete product information with AI company analysis
- **Competitive Intelligence**: Threat assessment and strategic recommendations

## 🔄 Development Status

**Current Phase**: Phase 1 - Core Foundation ✅

### Completed ✅
- [x] Project setup with virtual environment
- [x] Basic CLI structure with Click
- [x] Configuration management with environment variables
- [x] Basic logging setup
- [x] Core file structure and data models

### In Progress 🚧
- [ ] ProductHunt scraping implementation
- [ ] JSON output generation
- [ ] Data validation and error handling

### Upcoming 📋
- [ ] AI integration with Anthropic Claude
- [ ] Enhanced data structures with AI analysis
- [ ] Production polish and testing

## 🛠️ Development

### Project Structure

```
producthunter/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # CLI entry point
│   ├── scraper.py           # ProductHunt scraping logic
│   ├── config.py            # Configuration management
│   └── models/
│       └── __init__.py      # Data models and JSON structure
├── data/                    # Output directory for JSON files
├── tests/                   # Unit tests
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── debug_scraper.py        # Development debugging tools
└── README.md               # This file
```

### Running Tests

```bash
# Run tests (when implemented)
python -m pytest tests/

# Run with coverage
python -m pytest --cov=src tests/
```

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues or questions:
1. Check existing issues in the repository
2. Create a new issue with detailed description
3. Include error logs and system information

---

**Status**: Phase 1 Complete - Basic CLI structure and project foundation ready for scraping implementation.
