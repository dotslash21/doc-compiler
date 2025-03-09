import argparse
import logging
import sys
from datetime import datetime

from config import OPENAI_API_KEY, OPENAI_API_MODEL
from consolidator import ContentConsolidator
from crawler import WebCrawler
from logger import setup_logging


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Compile documentation from web pages")
    parser.add_argument("url", help="Entry point URL for crawling")
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Maximum crawling depth (default: 2)",
    )
    parser.add_argument(
        "--output",
        default=f"./output/{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        help="Output markdown file path (default: output.md)",
    )
    return parser.parse_args()


def main() -> int:
    """Main execution function."""
    # Parse arguments and setup logging
    args = parse_arguments()
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Initialize and run the crawler
        logger.info(f"Starting crawler for {args.url} with max depth {args.depth}")
        crawler = WebCrawler(args.url, args.depth)
        pages = crawler.crawl()

        if not pages:
            logger.error("No pages were successfully crawled")
            return 1

        logger.info(f"Successfully crawled {len(pages)} pages")

        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY environment variable not set")
            return 1

        # Initialize and run the consolidator
        logger.info("Starting content consolidation")
        consolidator = ContentConsolidator(OPENAI_API_KEY, OPENAI_API_MODEL)
        markdown_content = consolidator.consolidate(pages)

        # Write the output
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.info(f"Successfully wrote consolidated content to {args.output}")
        return 0

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
