"""
Professional Daraz Review Scraper Engine - Manual Filter Mode
- Let's you manually apply the star filter
- Then scraper takes over and scrapes all pages
- Press 'Q' to stop gracefully
- Saves to CSV in real-time
"""

import time
import csv
import re
from datetime import datetime
from typing import List
import logging

# For browser automation
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from core.scraper.interfaces.scraper_interface import ScraperInterface
from core.scraper.dto.product import Product
from core.scraper.dto.scraped_review import ScrapedReview

# For keyboard detection
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    import msvcrt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ScraperEngine(ScraperInterface):
    """Daraz scraper with manual filter mode"""
    
    def __init__(self, job_state=None, auto_start: bool = True):
        """
        Initialize the scraper engine.
        Browser resources are created only when scraping starts.
        """
        self._driver = None
        self.csv_filename = None
        self.job_state = job_state
        self.auto_start = auto_start
        
    def _init_csv(self):
        """Initialize CSV file with headers"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f"product_reviews_{timestamp}.csv"
        
        with open(self.csv_filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # writer.writerow(['Review Number', 'Review'])
        
        logger.info(f"CSV file created: {self.csv_filename}")
        
    def _save_review_to_csv(self, review_text: str, index: int):
        """Save a single review to CSV"""
        try:
            with open(self.csv_filename, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([index, review_text])
        except Exception as e:
            logger.error(f"Error saving review: {e}")
        
    def _setup_browser(self, headless: bool):
        """Setup Chrome browser"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
            
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self._driver = webdriver.Chrome(options=chrome_options)
        self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self._driver.set_page_load_timeout(10)
        
    def _check_stop(self) -> bool:
        """Check if user pressed 'Q' (CLI mode) or API requested stop (Web mode)."""
        if self.job_state and getattr(self.job_state, "stop_requested", False):
            logger.info("Job stop requested programmatically via API ('Finish Scraping'). Stopping...")
            return True

        # Only check server physical keyboard when running directly in CLI mode without job_state
        if self.job_state is None:
            if KEYBOARD_AVAILABLE:
                try:
                    if keyboard.is_pressed('q') or keyboard.is_pressed('Q'):
                        logger.info("User pressed 'Q' on server keyboard. Stopping...")
                        return True
                except Exception:
                    pass
            else:
                try:
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key in [b'q', b'Q']:
                            logger.info("User pressed 'Q' on server keyboard. Stopping...")
                            return True
                except Exception:
                    pass
        return False
    
    def _wait_for_manual_filter(self):
        """
        Wait for user to manually apply the star filter or auto-continue if called via API.
        """
        if getattr(self, "auto_start", True) or self.job_state is not None:
            logger.info("Auto start enabled for API execution mode. Proceeding with review scraping...")
            time.sleep(2)
            return True

        print("\n" + "=" * 80)
        print("MANUAL FILTER MODE")
        print("=" * 80)
        print("\nThe browser is now open with your product page.")
        print("\nPlease follow these steps:")
        print("1. Find the 'Reviews' section")
        print("2. Click on the star filter (e.g., '1 Star' or 'All Stars')")
        print("3. Wait for the page to refresh with filtered reviews")
        print("4. Make sure you can see the filtered reviews")
        print("\nIMPORTANT: Click on the filter you want to scrape")
        print("   - For 1-star reviews: Click '1 Star'")
        print("   - For 2-star reviews: Click '2 Star'")
        print("   - For all reviews: Click 'All Stars' or don't click any filter")
        print("\nWhen you're ready, type 'start' in the console and press Enter")
        print("   OR type 'quit' to exit")
        print("=" * 80)
        
        while True:
            user_input = input("\nEnter command (start/quit): ").strip().lower()
            if user_input == 'start':
                print("\nContinuing with scraping...")
                time.sleep(2)
                return True
            elif user_input == 'quit':
                print("\nExiting scraper...")
                return False
            else:
                print("Invalid command. Please type 'start' or 'quit'")
    
    def _get_total_pages(self) -> int:
        """Get total number of review pages"""
        try:
            # Wait for pagination to load
            time.sleep(3)
            
            # Try to find total pages from pagination
            pagination_selectors = [
                '.next-pagination-item',
                '.pagination-item',
                'button[class*="pagination-item"]',
                '.next-pagination-list button'
            ]
            
            max_page = 1
            
            for selector in pagination_selectors:
                try:
                    items = self._driver.find_elements(By.CSS_SELECTOR, selector)
                    for item in items:
                        try:
                            text = item.text.strip()
                            if text.isdigit():
                                page_num = int(text)
                                if page_num > max_page:
                                    max_page = page_num
                        except:
                            continue
                    
                    if max_page > 1:
                        logger.info(f"Found {max_page} total pages")
                        return max_page
                except:
                    continue
            
            # Alternative: Try to find total from text
            try:
                page_source = self._driver.page_source
                # Look for patterns like "Page 1 of 138" or "1-20 of 4978"
                patterns = [
                    r'Page\s+(\d+)\s+of\s+(\d+)',
                    r'(\d+)-(\d+)\s+of\s+(\d+)',
                    r'of\s+(\d+)\s+pages?',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, page_source, re.IGNORECASE)
                    if match:
                        # Get the last number (total pages)
                        total = int(match.group(-1))
                        if total > 1:
                            logger.info(f"Found {total} total pages")
                        return total
            except:
                pass
            
            return 1
            
        except Exception as e:
            logger.error(f"Error getting total pages: {e}")
            return 1
    
    def _extract_reviews_from_page(self) -> List[str]:
        """Extract reviews from current page"""
        comments = []
        
        try:
            # Wait for content to load
            time.sleep(2)
            
            # Try multiple selectors for review content
            selectors = [
                '.review-content',
                '.item-content .content',
                '.pdp-review-item .review-content',
                '.content .content',
                'div.content',
                '.review-item .content',
                '.pdp-review-item .content',
                '.item-review .content',
                '.review-text',
                '.comment-text'
            ]
            
            for selector in selectors:
                try:
                    elements = self._driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 3:
                            # Clean the text
                            text = ' '.join(text.split())
                            # Skip if it's just metadata
                            skip_words = ['stars', 'star', 'rating', 'verified', 'purchase']
                            if not any(word in text.lower() for word in skip_words):
                                comments.append(text)
                    if comments:
                        logger.info(f"Found {len(comments)} comments with selector: {selector}")
                        break
                except:
                    continue
            
            return comments
            
        except Exception as e:
            logger.error(f"Error extracting comments: {e}")
            return []
    
    def _go_to_page(self, page_num: int) -> bool:
        """Navigate to a specific page using JavaScript"""
        try:
            # Try to find and click the page number
            page_buttons = self._driver.find_elements(By.CSS_SELECTOR, 
                '.next-pagination-item, .pagination-item, button[class*="pagination-item"]')
            
            for button in page_buttons:
                try:
                    if button.text.strip() == str(page_num):
                        if button.is_displayed() and button.is_enabled():
                            # Use JavaScript to click (bypasses interception)
                            self._driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            time.sleep(0.5)
                            self._driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            logger.info(f"Navigated to page {page_num}")
                            return True
                except:
                    continue
            
            # Alternative: Try to use next button
            try:
                next_buttons = self._driver.find_elements(By.CSS_SELECTOR, 
                    '.next-pagination-item.next, .pagination-next, button[class*="next"]:not([disabled])')
                
                for btn in next_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        self._driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        time.sleep(0.5)
                        self._driver.execute_script("arguments[0].click();", btn)
                        time.sleep(3)
                        logger.info(f"Clicked next button")
                        return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"Error navigating to page {page_num}: {e}")
            return False
    
    def scrape_product(self, product_url: str) -> Product:

        self._init_csv()
        self._setup_browser(headless=False)

        unique_review_texts: set[str] = set()
        review_count = 0
        consecutive_empty_pages = 0
        reviews: list[ScrapedReview] = []
        
        metadata = {"title": "Daraz Product", "category": "Electronics", "seller": "Daraz Flagship Store", "overallRating": 4.5, "totalReviews": 0, "imageUrl": "", "platform": "Daraz"}

        try:
            # Open product page
            logger.info(f"Opening product page: {product_url}")
            self._driver.get(product_url)
            time.sleep(4)

            metadata = self._extract_metadata_from_driver(product_url)
            if self.job_state:
                self.job_state.product_preview = metadata

            # Wait for user to apply filter manually
            if not self._wait_for_manual_filter():
                self._driver.quit()
                self._driver = None
                return Product(
                    product_id="",
                    product_name=metadata.get("title", ""),
                    product_url=product_url,
                    category=metadata.get("category", "General"),
                    seller_name=metadata.get("seller", "Daraz Flagship Store"),
                    overall_rating=float(metadata.get("overallRating", 0.0)),
                    total_reviews=int(metadata.get("totalReviews", 0)),
                    image_url=metadata.get("imageUrl", ""),
                    platform=metadata.get("platform", "Daraz"),
                    reviews=reviews
                )

            # Get total pages
            total_pages = self._get_total_pages()
            logger.info(f"Total pages to scrape: {total_pages}")

            if total_pages <= 1:
                logger.warning("Only 1 page found or couldn't detect pagination")

            print("\n" + "=" * 70)
            print("Scraping in progress... Press 'Q' to stop")
            print(f"Total pages: {total_pages}")
            print("=" * 70 + "\n")

            current_page = 1
            if self.job_state:
                self.job_state.total_pages = total_pages
                self.job_state.add_log("SCRAPER", f"Detected total pages to scrape: {total_pages}")

            while current_page <= total_pages:
                # Check if user wants to stop
                if self._check_stop():
                    if self.job_state:
                        self.job_state.add_log("SCRAPER", f"Scraper stop requested. Stopping review collection at page {current_page}.")
                    break

                # If not on the right page, navigate
                if current_page > 1:
                    if not self._go_to_page(current_page):
                        logger.warning(f"Could not navigate to page {current_page}")
                        consecutive_empty_pages += 1
                        if consecutive_empty_pages >= 3:
                            logger.info("Stopping: Too many navigation failures")
                            break
                        current_page += 1
                        continue
                    else:
                        consecutive_empty_pages = 0

                # Extract reviews from current page
                page_review_texts = self._extract_reviews_from_page()

                if page_review_texts:
                    new_count = 0
                    for review_text in page_review_texts:
                        if review_text not in unique_review_texts:
                            unique_review_texts.add(review_text)
                            review_count += 1
                            new_count += 1
                            review = ScrapedReview(
                                review_text=review_text,
                                rating=None,
                                reviewer=None,
                                review_date=None
                            )
                            reviews.append(review)
                            self._save_review_to_csv(
                                review_text,
                                review_count
                            )

                    logger.info(f"Created {new_count} ScrapedReview objects.")
                    consecutive_empty_pages = 0

                    if self.job_state:
                        self.job_state.current_page = current_page
                        self.job_state.reviews_collected = review_count
                        pct = min(65, int(10 + (current_page / max(1, total_pages)) * 55))
                        self.job_state.progress_percent = pct
                        self.job_state.add_log("SCRAPER", f"Scraped page {current_page}/{total_pages} - Collected {new_count} new reviews (Total: {review_count})")

                    # Show progress every 10 pages
                    if current_page % 10 == 0:
                        print(f"Progress: Page {current_page}/{total_pages}, {review_count} reviews scraped")
                else:
                    logger.warning(f"No reviews found on page {current_page}")
                    consecutive_empty_pages += 1
                    if self.job_state:
                        self.job_state.add_log("SCRAPER", f"No reviews found on page {current_page}")

                    # If we hit 5 consecutive empty pages, stop
                    if consecutive_empty_pages >= 5:
                        logger.info(f"Stopping: No reviews for {consecutive_empty_pages} consecutive pages")
                        break

                current_page += 1
                time.sleep(2)

            logger.info(f"Scraping complete! Total reviews: {review_count}")
            if self.job_state:
                self.job_state.add_log("SCRAPER", f"Review scraping finished! Total reviews collected: {review_count}")

        except Exception as e:
            logger.error(f"Error during scraping: {e}")

        finally:
            if self._driver:
                self._driver.quit()
                self._driver = None

        logger.info("Scraping completed successfully.")
        return Product(
            product_id="",
            product_name=metadata.get("title", ""),
            product_url=product_url,
            category=metadata.get("category", "General"),
            seller_name=metadata.get("seller", "Daraz Flagship Store"),
            overall_rating=float(metadata.get("overallRating", 0.0)),
            total_reviews=int(metadata.get("totalReviews", review_count)),
            image_url=metadata.get("imageUrl", ""),
            platform=metadata.get("platform", "Daraz"),
            reviews=reviews
        )

    def _parse_title_from_url(self, url: str) -> str:
        """Helper to parse clean product title from Daraz URL slug"""
        try:
            match = re.search(r'/products/([^/-]+(?:-[^/-]+)*)(?:-i\d+)?\.html', url)
            if match:
                slug = match.group(1)
                words = slug.split('-')
                clean_title = ' '.join(w.capitalize() for w in words if len(w) > 0)
                if len(clean_title) > 5:
                    return clean_title
        except Exception:
            pass
        return "Daraz Verified Product"

    def _extract_metadata_from_driver(self, product_url: str) -> dict:
        fallback_title = self._parse_title_from_url(product_url)
        title = fallback_title
        image_url = ""
        seller = "N/A"
        rating = 0.0
        total_reviews = 0
        category = "N/A"

        if not self._driver:
            return {
                "productUrl": product_url,
                "title": title,
                "imageUrl": "",
                "seller": "N/A",
                "overallRating": 0.0,
                "totalReviews": 0,
                "platform": "Daraz",
                "category": "N/A"
            }

        page_source = ""
        try:
            page_source = self._driver.page_source or ""
        except Exception:
            pass

        # --- 1. Title Extraction ---
        title_selectors = ["h1.pdp-mod-product-badge-title", "h1.pdp-product-title", "h1", ".pdp-mod-product-badge-title"]
        for sel in title_selectors:
            try:
                elem = self._driver.find_element(By.CSS_SELECTOR, sel)
                if elem and elem.text.strip():
                    title = elem.text.strip()
                    break
            except Exception:
                continue

        if title == fallback_title and page_source:
            match = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', page_source, re.IGNORECASE)
            if not match:
                match = re.search(r'<title>([^<]+)</title>', page_source, re.IGNORECASE)
            if match and len(match.group(1).strip()) > 3:
                raw_t = match.group(1).strip()
                clean_t = re.sub(r'\s*\|\s*Daraz.*$', '', raw_t, flags=re.IGNORECASE).strip()
                if clean_t:
                    title = clean_t

        # --- 2. Image URL Extraction ---
        if page_source:
            img_match = re.search(r'<meta\s+(?:property|name)=["\']og:image["\']\s+content=["\']([^"\']+)["\']', page_source, re.IGNORECASE)
            if not img_match:
                img_match = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+(?:property|name)=["\']og:image["\']', page_source, re.IGNORECASE)
            if img_match and img_match.group(1).startswith("http"):
                image_url = img_match.group(1).strip()

        if not image_url:
            img_selectors = [
                ".pdp-mod-common-image",
                ".gallery-preview-panel img",
                "img.gallery-preview-panel__image",
                "img[src*='lazcdn']",
                "img[src*='slatic']",
                "img[src*='daraz']"
            ]
            for sel in img_selectors:
                try:
                    elem = self._driver.find_element(By.CSS_SELECTOR, sel)
                    if elem:
                        src = elem.get_attribute("src") or elem.get_attribute("data-src")
                        if src and src.startswith("http"):
                            image_url = src
                            break
                except Exception:
                    continue

        # --- 3. Seller Name Extraction ---
        seller_selectors = [
            ".seller-name__detail-name",
            ".seller-name__detail",
            ".seller-name",
            ".pdp-seller-info-name",
            "a[href*='shop']",
            "a[href*='seller']"
        ]
        for sel in seller_selectors:
            try:
                elem = self._driver.find_element(By.CSS_SELECTOR, sel)
                if elem and elem.text.strip():
                    seller = elem.text.strip()
                    break
            except Exception:
                continue

        if seller == "N/A" and page_source:
            seller_match = re.search(r'"sellerName"\s*:\s*"([^"]+)"', page_source)
            if not seller_match:
                seller_match = re.search(r'"storeName"\s*:\s*"([^"]+)"', page_source)
            if not seller_match:
                seller_match = re.search(r'class="[^"]*seller-name[^"]*"[^>]*>([^<]+)<', page_source, re.IGNORECASE)
            if seller_match and seller_match.group(1).strip():
                seller = seller_match.group(1).strip()

        # --- 4. Overall Rating Extraction ---
        rating_selectors = [".score-average", ".pdp-review-summary__score", "span.score-average"]
        for sel in rating_selectors:
            try:
                elem = self._driver.find_element(By.CSS_SELECTOR, sel)
                if elem and elem.text.strip():
                    match = re.search(r'\d+(?:\.\d+)?', elem.text.strip())
                    if match:
                        rating = float(match.group())
                        break
            except Exception:
                continue

        if rating == 0.0 and page_source:
            r_match = re.search(r'"ratingValue"\s*:\s*"?([\d\.]+)"?', page_source)
            if not r_match:
                r_match = re.search(r'([\d\.]+)\s*/\s*5', page_source)
            if r_match:
                try:
                    r_val = float(r_match.group(1))
                    if 0.0 <= r_val <= 5.0:
                        rating = r_val
                except Exception:
                    pass

        # --- 5. Total Reviews Extraction ---
        count_selectors = [".pdp-review-summary__link", ".count", ".score-total", "a[href*='rating-review']"]
        for sel in count_selectors:
            try:
                elem = self._driver.find_element(By.CSS_SELECTOR, sel)
                if elem and elem.text.strip():
                    match = re.search(r'\d+', elem.text.strip())
                    if match:
                        total_reviews = int(match.group())
                        break
            except Exception:
                continue

        if total_reviews == 0 and page_source:
            rev_match = re.search(r'"reviewCount"\s*:\s*"?(\d+)"?', page_source)
            if not rev_match:
                rev_match = re.search(r'"ratingCount"\s*:\s*"?(\d+)"?', page_source)
            if not rev_match:
                rev_match = re.search(r'(\d+)\s*(?:Ratings|Reviews|ratings|reviews)', page_source)
            if rev_match:
                try:
                    total_reviews = int(rev_match.group(1))
                except Exception:
                    pass

        # --- 6. Category Extraction ---
        try:
            crumbs = self._driver.find_elements(By.CSS_SELECTOR, ".breadcrumb_item, .pdp-breadcrumb a, .breadcrumb a")
            if crumbs and len(crumbs) > 1:
                cat_text = crumbs[-1].text.strip() or crumbs[-2].text.strip()
                if cat_text and cat_text.lower() != "home":
                    category = cat_text
        except Exception:
            pass

        if category == "N/A" and page_source:
            cat_match = re.search(r'"category"\s*:\s*"([^"]+)"', page_source)
            if cat_match and cat_match.group(1).strip():
                category = cat_match.group(1).strip()

        return {
            "productUrl": product_url,
            "title": title,
            "imageUrl": image_url,
            "seller": seller,
            "overallRating": rating,
            "totalReviews": total_reviews,
            "platform": "Daraz",
            "category": category
        }

    def extract_product_preview(self, product_url: str) -> dict:
        """
        Extracts product preview information (title, image, rating, seller, etc.) without scraping reviews.
        """
        fallback_title = self._parse_title_from_url(product_url)
        fallback_data = {
            "productUrl": product_url,
            "title": fallback_title,
            "imageUrl": "",
            "seller": "N/A",
            "overallRating": 0.0,
            "totalReviews": 0,
            "platform": "Daraz",
            "category": "N/A"
        }

        try:
            self._setup_browser(headless=True)
            if self._driver:
                self._driver.set_page_load_timeout(10)

            logger.info(f"Extracting product preview for: {product_url}")
            try:
                self._driver.get(product_url)
            except Exception as nav_err:
                if "timeout" in str(nav_err).lower() or "timed out" in str(nav_err).lower():
                    logger.warning(f"Page load timed out for {product_url}, continuing with metadata extraction.")
                else:
                    raise nav_err
            time.sleep(3)
            try:
                self._driver.execute_script("window.scrollTo(0, 350);")
                time.sleep(1)
            except Exception:
                pass

            meta = self._extract_metadata_from_driver(product_url)
            # Rejection rule for category / directory / 404 / fake product pages
            clean_title = (meta.get("title") or "").strip().lower()
            clean_seller = (meta.get("seller") or "").strip().lower()
            rating = float(meta.get("overallRating") or 0.0)
            reviews = int(meta.get("totalReviews") or 0)

            invalid_titles = ["error", "404", "page not found", "not found", "products", "catalog", "category", "daraz products", "search", "daraz verified product"]
            invalid_sellers = ["become a seller", "become a seller!", "n/a", "none"]

            is_title_bad = clean_title in invalid_titles or "404" in clean_title or clean_title.startswith("error")
            is_seller_bad = clean_seller in invalid_sellers

            if is_title_bad or is_seller_bad or (rating == 0.0 and reviews == 0 and (is_seller_bad or clean_title in [fallback_title.lower(), "products"])):
                raise ValueError("Failed to fetch product details from the provided URL. The link points to a non-existent or inactive product page (404 Error).")

            return meta
        except Exception as e:
            logger.error(f"Error extracting product preview: {e}")
            if isinstance(e, ValueError) or "product details" in str(e) or "404 Error" in str(e) or "category/directory page" in str(e):
                raise
            raise ValueError(f"Failed to extract product details: {str(e)}")
        finally:
            if self._driver:
                try:
                    self._driver.quit()
                except Exception:
                    pass
                self._driver = None