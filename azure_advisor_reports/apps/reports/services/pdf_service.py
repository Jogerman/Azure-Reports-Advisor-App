"""
Playwright-based PDF generation service for Azure Advisor Reports.

This service provides high-quality PDF generation using Playwright (headless browser),
supporting modern CSS, Chart.js visualizations, and professional formatting.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

from django.conf import settings
from playwright.async_api import async_playwright, Browser, Page, Error as PlaywrightError

logger = logging.getLogger(__name__)


class PlaywrightPDFGenerator:
    """
    Generate professional PDFs from HTML using Playwright headless browser.

    Features:
    - Full Chart.js support with automatic chart rendering detection
    - Modern CSS3 and print media queries
    - Custom headers and footers with page numbers
    - Configurable page size, margins, and orientation
    - Smart waiting for dynamic content (charts, images, fonts)
    - Error handling and timeout protection
    """

    # Default PDF generation options - Optimized for smaller file size
    DEFAULT_OPTIONS = {
        'format': 'A4',
        'print_background': True,  # Python Playwright uses snake_case
        'prefer_css_page_size': False,
        'display_header_footer': True,
        'margin': {
            'top': '12mm',
            'right': '10mm',
            'bottom': '12mm',
            'left': '10mm',
        },
        'scale': 0.95,  # Slightly reduce scale to fit more content
    }

    # Default timeout for page operations (60 seconds) - Increased for complex reports
    DEFAULT_TIMEOUT = 60000

    # Timeout for chart rendering detection (15 seconds) - Increased for multiple charts
    CHART_TIMEOUT = 15000

    def __init__(self, headless: bool = True, timeout: int = None):
        """
        Initialize the PDF generator.

        Args:
            headless: Run browser in headless mode (default: True)
            timeout: Default timeout in milliseconds (default: 30000)
        """
        self.headless = headless
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self._browser: Optional[Browser] = None
        self._playwright = None

    async def __aenter__(self):
        """Context manager entry - start Playwright."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-web-security',  # Allow CORS for local resources
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',  # Required for Docker
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',  # Overcome limited resource problems
            ]
        )
        logger.info("Playwright browser launched successfully")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup Playwright."""
        if self._browser:
            await self._browser.close()
            logger.info("Playwright browser closed")
        if self._playwright:
            await self._playwright.stop()

    async def generate_pdf_from_html(
        self,
        html_content: str,
        output_path: str,
        options: Optional[Dict[str, Any]] = None,
        wait_for_charts: bool = True,
        wait_for_fonts: bool = True,
        base_url: Optional[str] = None,
    ) -> str:
        """
        Generate PDF from HTML content.

        Args:
            html_content: HTML string to convert to PDF
            output_path: Output file path for the PDF
            options: PDF generation options (merged with defaults)
            wait_for_charts: Wait for Chart.js charts to render (default: True)
            wait_for_fonts: Wait for web fonts to load (default: True)
            base_url: Base URL for resolving relative paths (default: file://)

        Returns:
            str: Path to generated PDF file

        Raises:
            PlaywrightError: If browser operation fails
            TimeoutError: If page load or chart rendering times out
            Exception: For other unexpected errors
        """
        try:
            logger.info(f"Starting PDF generation: {output_path}")

            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)

            # Merge options with defaults
            pdf_options = {**self.DEFAULT_OPTIONS}
            if options:
                pdf_options.update(options)

            # Create new page
            page = await self._browser.new_page()

            try:
                # Set viewport for consistent rendering - optimized size
                await page.set_viewport_size({'width': 1100, 'height': 1400})

                # Set content with base URL
                if base_url:
                    await page.goto(base_url, wait_until='domcontentloaded', timeout=self.timeout)
                    await page.set_content(html_content, wait_until='networkidle', timeout=self.timeout)
                else:
                    # Use data URL for local HTML
                    await page.set_content(html_content, wait_until='domcontentloaded', timeout=self.timeout)

                logger.info("HTML content loaded into browser")

                # Wait for network to be idle (increased timeout)
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    logger.info("Network idle state reached")
                except PlaywrightError:
                    logger.warning("Network idle timeout - continuing anyway")

                # Wait for DOM to be fully ready
                await page.wait_for_load_state('load', timeout=self.timeout)
                logger.info("DOM load complete")

                # Wait for fonts to load
                if wait_for_fonts:
                    await self._wait_for_fonts(page)

                # Additional wait for any lazy-loaded content
                await page.wait_for_timeout(2000)
                logger.info("Waited for lazy-loaded content")

                # Wait for Chart.js charts to render
                if wait_for_charts:
                    await self._wait_for_charts(page)

                # Wait for all images to load
                await self._wait_for_images(page)

                # Wait for all elements to be visible
                await self._wait_for_elements_visible(page)

                # Additional wait to ensure all animations complete
                # Increased to 4000ms to ensure everything is fully rendered
                await page.wait_for_timeout(4000)
                logger.info("Final wait complete - all content should be rendered")

                logger.info("All animations complete, proceeding with PDF generation")

                # Inject print-ready CSS
                await self._inject_print_css(page)

                # Generate PDF
                logger.info(f"Generating PDF with options: {pdf_options}")
                await page.pdf(path=output_path, **pdf_options)

                logger.info(f"PDF generated successfully: {output_path}")
                return output_path

            finally:
                # Always close the page
                await page.close()

        except PlaywrightError as e:
            logger.error(f"Playwright error during PDF generation: {str(e)}")
            raise
        except TimeoutError as e:
            logger.error(f"Timeout during PDF generation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during PDF generation: {str(e)}")
            raise

    async def _wait_for_charts(self, page: Page) -> None:
        """
        Wait for all Chart.js charts to finish rendering.

        Args:
            page: Playwright page object
        """
        try:
            logger.info("Waiting for Chart.js charts to render...")

            # Inject script to wait for charts - IMPROVED VERSION
            chart_script = """
                () => {
                    return new Promise((resolve) => {
                        if (typeof Chart === 'undefined') {
                            console.log('Chart.js not found, skipping chart wait');
                            resolve();
                            return;
                        }

                        const canvases = document.querySelectorAll('canvas');

                        if (canvases.length === 0) {
                            console.log('No canvas elements found');
                            resolve();
                            return;
                        }

                        console.log(`Found ${canvases.length} canvas elements, waiting for Chart.js rendering...`);

                        let checkCount = 0;
                        const maxChecks = 150; // 15 seconds max (150 * 100ms) - Increased for complex charts

                        const checkCharts = () => {
                            checkCount++;

                            // Check if all canvases are visible and have content
                            const allRendered = Array.from(canvases).every(canvas => {
                                // 1. Canvas must be visible (has dimensions)
                                if (canvas.offsetHeight === 0 || canvas.offsetWidth === 0) {
                                    return false;
                                }

                                // 2. Canvas must have actual drawing context (Chart.js has drawn something)
                                try {
                                    const ctx = canvas.getContext('2d');
                                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

                                    // Check if canvas has any non-transparent pixels
                                    // This confirms Chart.js actually drew something
                                    for (let i = 0; i < imageData.data.length; i += 4) {
                                        const alpha = imageData.data[i + 3];
                                        if (alpha > 0) {
                                            return true; // Found at least one drawn pixel
                                        }
                                    }
                                    return false; // Canvas is blank
                                } catch (e) {
                                    console.warn('Could not check canvas content:', e);
                                    // If we can't check, assume it's rendered after dimensions are set
                                    return true;
                                }
                            });

                            if (allRendered) {
                                console.log(`All ${canvases.length} charts rendered successfully after ${checkCount * 100}ms`);
                                resolve();
                            } else if (checkCount >= maxChecks) {
                                console.warn(`Chart rendering timeout after ${checkCount * 100}ms, proceeding anyway`);
                                resolve();
                            } else {
                                setTimeout(checkCharts, 100);
                            }
                        };

                        // Start checking after initial delay to let Chart.js initialize
                        // Increased delay to give more time for complex charts
                        setTimeout(checkCharts, 1000);
                    });
                }
            """

            await page.evaluate(chart_script)

            logger.info("All charts rendered successfully")

        except Exception as e:
            # Don't fail PDF generation if chart detection fails
            logger.warning(f"Chart rendering detection failed: {str(e)}")

    async def _wait_for_fonts(self, page: Page) -> None:
        """
        Wait for web fonts to load.

        Args:
            page: Playwright page object
        """
        try:
            logger.info("Waiting for fonts to load...")

            font_script = """
                () => {
                    if (document.fonts && document.fonts.ready) {
                        return document.fonts.ready;
                    }
                    return Promise.resolve();
                }
            """

            await page.evaluate(font_script)

            logger.info("Fonts loaded successfully")

        except Exception as e:
            logger.warning(f"Font loading detection failed: {str(e)}")

    async def _wait_for_images(self, page: Page) -> None:
        """
        Wait for all images to fully load.

        Args:
            page: Playwright page object
        """
        try:
            logger.info("Waiting for images to load...")

            image_script = """
                () => {
                    return new Promise((resolve) => {
                        const images = Array.from(document.images);

                        if (images.length === 0) {
                            console.log('No images found');
                            resolve();
                            return;
                        }

                        console.log(`Found ${images.length} images, waiting for them to load...`);

                        const loadedImages = images.filter(img => img.complete && img.naturalHeight !== 0);

                        if (loadedImages.length === images.length) {
                            console.log('All images already loaded');
                            resolve();
                            return;
                        }

                        let loadedCount = loadedImages.length;
                        const totalImages = images.length;

                        const checkAllLoaded = () => {
                            if (loadedCount >= totalImages) {
                                console.log(`All ${totalImages} images loaded successfully`);
                                resolve();
                            }
                        };

                        images.forEach((img) => {
                            if (img.complete && img.naturalHeight !== 0) {
                                return; // Already loaded
                            }

                            img.addEventListener('load', () => {
                                loadedCount++;
                                checkAllLoaded();
                            });

                            img.addEventListener('error', () => {
                                console.warn('Image failed to load:', img.src);
                                loadedCount++; // Count as "done" even if failed
                                checkAllLoaded();
                            });
                        });

                        // Timeout fallback
                        setTimeout(() => {
                            console.warn(`Image loading timeout after 5s (${loadedCount}/${totalImages} loaded)`);
                            resolve();
                        }, 5000);
                    });
                }
            """

            await page.evaluate(image_script)

            logger.info("All images loaded successfully")

        except Exception as e:
            logger.warning(f"Image loading detection failed: {str(e)}")

    async def _wait_for_elements_visible(self, page: Page) -> None:
        """
        Wait for all major content elements to be visible and have dimensions.

        Args:
            page: Playwright page object
        """
        try:
            logger.info("Waiting for all elements to be visible...")

            visibility_script = """
                () => {
                    return new Promise((resolve) => {
                        const selectors = [
                            '.chart-container',
                            '.recommendation-card',
                            'table',
                            'canvas',
                            '.content-section',
                            '.report-section'
                        ];

                        let checkCount = 0;
                        const maxChecks = 50; // 5 seconds max

                        const checkVisibility = () => {
                            checkCount++;

                            const allVisible = selectors.every(selector => {
                                const elements = document.querySelectorAll(selector);

                                if (elements.length === 0) {
                                    return true; // No elements with this selector, that's OK
                                }

                                // Check if all elements with this selector are visible
                                return Array.from(elements).every(el => {
                                    const rect = el.getBoundingClientRect();
                                    const style = window.getComputedStyle(el);

                                    return (
                                        rect.width > 0 &&
                                        rect.height > 0 &&
                                        style.display !== 'none' &&
                                        style.visibility !== 'hidden' &&
                                        style.opacity !== '0'
                                    );
                                });
                            });

                            if (allVisible) {
                                console.log(`All content elements visible after ${checkCount * 100}ms`);
                                resolve();
                            } else if (checkCount >= maxChecks) {
                                console.warn(`Element visibility check timeout after ${checkCount * 100}ms`);
                                resolve();
                            } else {
                                setTimeout(checkVisibility, 100);
                            }
                        };

                        setTimeout(checkVisibility, 500);
                    });
                }
            """

            await page.evaluate(visibility_script)

            logger.info("All elements are visible")

        except Exception as e:
            logger.warning(f"Element visibility detection failed: {str(e)}")

    async def _inject_print_css(self, page: Page) -> None:
        """
        Inject print-friendly CSS to hide interactive elements.

        Args:
            page: Playwright page object
        """
        try:
            print_css = """
                @media print {
                    button, .btn, .no-print, [onclick] {
                        display: none !important;
                    }

                    * {
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                        color-adjust: exact !important;
                    }

                    .chart-container, .recommendation-card, table {
                        page-break-inside: avoid;
                        break-inside: avoid;
                    }

                    table {
                        width: 100%;
                    }

                    canvas {
                        max-width: 100%;
                        height: auto !important;
                        image-rendering: optimizeSpeed !important;
                    }

                    /* Optimize chart rendering for smaller file size */
                    .chart-wrapper canvas {
                        image-rendering: -webkit-optimize-contrast !important;
                    }

                    /* Reduce unnecessary spacing */
                    p {
                        margin: 0.3em 0 !important;
                    }

                    ul, ol {
                        margin: 0.5em 0 !important;
                        padding-left: 1.5em !important;
                    }
                }
            """

            await page.add_style_tag(content=print_css)
            logger.info("Print CSS injected successfully")
        except Exception as e:
            logger.warning(f"Failed to inject print CSS: {str(e)}")


class SyncPlaywrightPDFGenerator:
    """
    Synchronous wrapper for PlaywrightPDFGenerator.

    Provides a sync interface for Django views that can't use async/await.
    Uses asyncio.run() to execute async operations.
    """

    def __init__(self, headless: bool = True, timeout: int = None):
        """
        Initialize the sync PDF generator.

        Args:
            headless: Run browser in headless mode (default: True)
            timeout: Default timeout in milliseconds (default: 30000)
        """
        self.headless = headless
        self.timeout = timeout

    def generate_pdf_from_html(
        self,
        html_content: str,
        output_path: str,
        options: Optional[Dict[str, Any]] = None,
        wait_for_charts: bool = True,
        wait_for_fonts: bool = True,
        base_url: Optional[str] = None,
    ) -> str:
        """
        Generate PDF from HTML content (synchronous).

        Args:
            html_content: HTML string to convert to PDF
            output_path: Output file path for the PDF
            options: PDF generation options (merged with defaults)
            wait_for_charts: Wait for Chart.js charts to render (default: True)
            wait_for_fonts: Wait for web fonts to load (default: True)
            base_url: Base URL for resolving relative paths (default: file://)

        Returns:
            str: Path to generated PDF file
        """
        return asyncio.run(self._generate_async(
            html_content=html_content,
            output_path=output_path,
            options=options,
            wait_for_charts=wait_for_charts,
            wait_for_fonts=wait_for_fonts,
            base_url=base_url,
        ))

    async def _generate_async(
        self,
        html_content: str,
        output_path: str,
        options: Optional[Dict[str, Any]] = None,
        wait_for_charts: bool = True,
        wait_for_fonts: bool = True,
        base_url: Optional[str] = None,
    ) -> str:
        """Internal async method to generate PDF."""
        async with PlaywrightPDFGenerator(headless=self.headless, timeout=self.timeout) as generator:
            return await generator.generate_pdf_from_html(
                html_content=html_content,
                output_path=output_path,
                options=options,
                wait_for_charts=wait_for_charts,
                wait_for_fonts=wait_for_fonts,
                base_url=base_url,
            )


# Convenience function for one-off PDF generation
def generate_pdf(
    html_content: str,
    output_path: str,
    options: Optional[Dict[str, Any]] = None,
    wait_for_charts: bool = True,
    wait_for_fonts: bool = True,
    base_url: Optional[str] = None,
    headless: bool = True,
) -> str:
    """
    Convenience function to generate PDF from HTML.

    Args:
        html_content: HTML string to convert to PDF
        output_path: Output file path for the PDF
        options: PDF generation options
        wait_for_charts: Wait for Chart.js charts to render (default: True)
        wait_for_fonts: Wait for web fonts to load (default: True)
        base_url: Base URL for resolving relative paths
        headless: Run browser in headless mode (default: True)

    Returns:
        str: Path to generated PDF file
    """
    generator = SyncPlaywrightPDFGenerator(headless=headless)
    return generator.generate_pdf_from_html(
        html_content=html_content,
        output_path=output_path,
        options=options,
        wait_for_charts=wait_for_charts,
        wait_for_fonts=wait_for_fonts,
        base_url=base_url,
    )
