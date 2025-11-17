#!/usr/bin/env node
/**
 * Browser Capture Tool
 * Uses Puppeteer for browser automation and web page capture
 */

const fs = require('fs');
const path = require('path');
const { program } = require('commander');

// Check if puppeteer is available
let puppeteer;
try {
    puppeteer = require('puppeteer');
} catch (e) {
    console.error('Error: puppeteer is not installed.');
    console.error('Install it with: npm install puppeteer');
    process.exit(1);
}

class BrowserCapture {
    constructor(outputDir = './screenshots') {
        this.outputDir = outputDir;
        this.ensureDirectory(outputDir);
    }

    ensureDirectory(dir) {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
    }

    generateFilename(prefix = 'webpage', extension = 'png') {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        return `${prefix}_${timestamp}.${extension}`;
    }

    async captureWebPage(url, options = {}) {
        const {
            outputPath = null,
            fullPage = true,
            viewport = { width: 1920, height: 1080 },
            waitForSelector = null,
            waitTime = 0,
            format = 'png',
            quality = 90,
            javascript = true,
            userAgent = null
        } = options;

        let browser;
        const output = outputPath || path.join(this.outputDir, this.generateFilename('webpage', format));

        try {
            // Launch browser
            browser = await puppeteer.launch({
                headless: 'new',
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });

            const page = await browser.newPage();

            // Set viewport
            await page.setViewport(viewport);

            // Set custom user agent if provided
            if (userAgent) {
                await page.setUserAgent(userAgent);
            }

            // Disable JavaScript if requested
            if (!javascript) {
                await page.setJavaScriptEnabled(false);
            }

            // Navigate to URL
            await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

            // Wait for specific selector if provided
            if (waitForSelector) {
                await page.waitForSelector(waitForSelector, { timeout: 10000 });
            }

            // Additional wait time
            if (waitTime > 0) {
                await new Promise(resolve => setTimeout(resolve, waitTime));
            }

            // Take screenshot
            const screenshotOptions = {
                path: output,
                fullPage: fullPage
            };

            if (format === 'jpeg' || format === 'jpg') {
                screenshotOptions.type = 'jpeg';
                screenshotOptions.quality = quality;
            } else {
                screenshotOptions.type = 'png';
            }

            await page.screenshot(screenshotOptions);

            // Get page metadata
            const title = await page.title();
            const finalUrl = page.url();
            const dimensions = await page.evaluate(() => ({
                width: document.documentElement.scrollWidth,
                height: document.documentElement.scrollHeight,
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight
            }));

            await browser.close();

            return {
                success: true,
                path: path.resolve(output),
                url: finalUrl,
                title: title,
                dimensions: dimensions,
                format: format,
                fullPage: fullPage,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            if (browser) {
                await browser.close();
            }
            return {
                success: false,
                error: error.message,
                url: url
            };
        }
    }

    async captureElement(url, selector, options = {}) {
        const {
            outputPath = null,
            viewport = { width: 1920, height: 1080 },
            waitTime = 0,
            format = 'png',
            padding = 0
        } = options;

        let browser;
        const output = outputPath || path.join(this.outputDir, this.generateFilename('element', format));

        try {
            browser = await puppeteer.launch({
                headless: 'new',
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });

            const page = await browser.newPage();
            await page.setViewport(viewport);
            await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

            // Wait for element
            await page.waitForSelector(selector, { timeout: 10000 });

            if (waitTime > 0) {
                await new Promise(resolve => setTimeout(resolve, waitTime));
            }

            // Find element and screenshot
            const element = await page.$(selector);

            if (!element) {
                throw new Error(`Element not found: ${selector}`);
            }

            await element.screenshot({
                path: output,
                type: format === 'jpeg' || format === 'jpg' ? 'jpeg' : 'png'
            });

            const boundingBox = await element.boundingBox();

            await browser.close();

            return {
                success: true,
                path: path.resolve(output),
                url: url,
                selector: selector,
                boundingBox: boundingBox,
                format: format,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            if (browser) {
                await browser.close();
            }
            return {
                success: false,
                error: error.message,
                url: url,
                selector: selector
            };
        }
    }

    async extractPageContent(url, options = {}) {
        const {
            includeHtml = true,
            includeText = true,
            includeLinks = true,
            includeImages = true,
            outputPath = null
        } = options;

        let browser;

        try {
            browser = await puppeteer.launch({
                headless: 'new',
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });

            const page = await browser.newPage();
            await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

            const content = await page.evaluate((opts) => {
                const result = {
                    title: document.title,
                    url: window.location.href
                };

                if (opts.includeHtml) {
                    result.html = document.documentElement.outerHTML;
                }

                if (opts.includeText) {
                    result.text = document.body.innerText;
                }

                if (opts.includeLinks) {
                    result.links = Array.from(document.querySelectorAll('a[href]'))
                        .map(a => ({ text: a.innerText.trim(), href: a.href }))
                        .filter(link => link.text);
                }

                if (opts.includeImages) {
                    result.images = Array.from(document.querySelectorAll('img[src]'))
                        .map(img => ({ alt: img.alt, src: img.src, width: img.width, height: img.height }));
                }

                return result;
            }, { includeHtml, includeText, includeLinks, includeImages });

            await browser.close();

            // Save to file if requested
            if (outputPath) {
                fs.writeFileSync(outputPath, JSON.stringify(content, null, 2));
            }

            return {
                success: true,
                content: content,
                outputPath: outputPath ? path.resolve(outputPath) : null,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            if (browser) {
                await browser.close();
            }
            return {
                success: false,
                error: error.message,
                url: url
            };
        }
    }
}

// CLI Interface
if (require.main === module) {
    program
        .name('browser-capture')
        .description('Browser automation and web page capture tool')
        .version('1.0.0');

    program
        .command('page <url>')
        .description('Capture full web page screenshot')
        .option('-o, --output <path>', 'Output file path')
        .option('-w, --width <number>', 'Viewport width', '1920')
        .option('-h, --height <number>', 'Viewport height', '1080')
        .option('--no-fullpage', 'Capture only viewport (not full page)')
        .option('-s, --selector <selector>', 'Wait for CSS selector before capturing')
        .option('-t, --wait <ms>', 'Additional wait time in milliseconds', '0')
        .option('-f, --format <format>', 'Output format (png, jpeg)', 'png')
        .option('-q, --quality <number>', 'JPEG quality (1-100)', '90')
        .option('--no-javascript', 'Disable JavaScript')
        .option('--user-agent <string>', 'Custom user agent')
        .option('-d, --dir <path>', 'Output directory', './screenshots')
        .option('--json', 'Output result as JSON')
        .action(async (url, options) => {
            const capturer = new BrowserCapture(options.dir);
            const result = await capturer.captureWebPage(url, {
                outputPath: options.output,
                fullPage: options.fullpage,
                viewport: { width: parseInt(options.width), height: parseInt(options.height) },
                waitForSelector: options.selector,
                waitTime: parseInt(options.wait),
                format: options.format,
                quality: parseInt(options.quality),
                javascript: options.javascript,
                userAgent: options.userAgent
            });

            if (options.json) {
                console.log(JSON.stringify(result, null, 2));
            } else {
                if (result.success) {
                    console.log(`✓ Screenshot saved to: ${result.path}`);
                    console.log(`  URL: ${result.url}`);
                    console.log(`  Title: ${result.title}`);
                    console.log(`  Dimensions: ${result.dimensions.width}x${result.dimensions.height}`);
                } else {
                    console.error(`✗ Error: ${result.error}`);
                    process.exit(1);
                }
            }
        });

    program
        .command('element <url> <selector>')
        .description('Capture specific element from web page')
        .option('-o, --output <path>', 'Output file path')
        .option('-w, --width <number>', 'Viewport width', '1920')
        .option('-h, --height <number>', 'Viewport height', '1080')
        .option('-t, --wait <ms>', 'Additional wait time in milliseconds', '0')
        .option('-f, --format <format>', 'Output format (png, jpeg)', 'png')
        .option('-d, --dir <path>', 'Output directory', './screenshots')
        .option('--json', 'Output result as JSON')
        .action(async (url, selector, options) => {
            const capturer = new BrowserCapture(options.dir);
            const result = await capturer.captureElement(url, selector, {
                outputPath: options.output,
                viewport: { width: parseInt(options.width), height: parseInt(options.height) },
                waitTime: parseInt(options.wait),
                format: options.format
            });

            if (options.json) {
                console.log(JSON.stringify(result, null, 2));
            } else {
                if (result.success) {
                    console.log(`✓ Element screenshot saved to: ${result.path}`);
                    console.log(`  Selector: ${result.selector}`);
                } else {
                    console.error(`✗ Error: ${result.error}`);
                    process.exit(1);
                }
            }
        });

    program
        .command('extract <url>')
        .description('Extract content from web page (HTML, text, links, images)')
        .option('-o, --output <path>', 'Save content to JSON file')
        .option('--no-html', 'Exclude HTML')
        .option('--no-text', 'Exclude text content')
        .option('--no-links', 'Exclude links')
        .option('--no-images', 'Exclude images')
        .option('--json', 'Output result as JSON')
        .action(async (url, options) => {
            const capturer = new BrowserCapture();
            const result = await capturer.extractPageContent(url, {
                includeHtml: options.html,
                includeText: options.text,
                includeLinks: options.links,
                includeImages: options.images,
                outputPath: options.output
            });

            if (options.json || !options.output) {
                console.log(JSON.stringify(result, null, 2));
            } else {
                if (result.success) {
                    console.log(`✓ Content extracted and saved to: ${result.outputPath}`);
                    console.log(`  Title: ${result.content.title}`);
                    if (result.content.links) {
                        console.log(`  Links: ${result.content.links.length}`);
                    }
                    if (result.content.images) {
                        console.log(`  Images: ${result.content.images.length}`);
                    }
                } else {
                    console.error(`✗ Error: ${result.error}`);
                    process.exit(1);
                }
            }
        });

    program.parse();
}

module.exports = BrowserCapture;
