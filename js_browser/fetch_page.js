#!/usr/bin/env node
'use strict';

/**
 * User-assisted browser collector for Yad2 Car Finder Bot.
 *
 * Either launches a visible Chrome window, or attaches to a Chrome instance
 * the user already started with --remote-debugging-port. After navigation it
 * waits until listing cards appear, then snapshots the page. It does not
 * automate or bypass verification/captchas.
 *
 * Usage:
 *   node fetch_page.js <url> [--referer <referer>] [--channel <channel>]
 *     [--timeout-ms <ms>] [--cdp-url <url>] [--reuse-tab] [--html-out <path>]
 *
 * On success, prints a single JSON line to stdout:
 *   {"title": "...", "listingCount": N, "htmlPath": "..."}
 * The page HTML is written to --html-out (required for large Yad2 pages so the
 * stdout pipe does not fill and hang).
 */

const fs = require('fs');
const { chromium } = require('playwright');

const LISTING_SELECTORS = [
  'a[data-nagish="private-item-link"][data-listing-type]',
  'a[data-nagish="private-item-link"]',
  'a[href*="/vehicles/"][href*="item/"]',
];

const DETAIL_READY_SELECTORS = [
  'script#__NEXT_DATA__',
  'section[data-testid="additional-info"]',
  'p[data-testid="vehicle-description"]',
];

function parseArgs(argv) {
  const rest = argv.slice(2);
  if (rest.length === 0 || rest[0].startsWith('--')) {
    throw new Error(
      'Usage: node fetch_page.js <url> [--referer <referer>] [--channel <channel>] [--timeout-ms <ms>] [--cdp-url <url>] [--reuse-tab] [--html-out <path>] [--page-kind search|detail]'
    );
  }

  const args = {
    url: rest[0],
    referer: null,
    channel: 'chrome',
    timeoutMs: 60000,
    cdpUrl: null,
    reuseTab: false,
    htmlOut: null,
    pageKind: 'search',
  };

  for (let i = 1; i < rest.length; i += 1) {
    const flag = rest[i];
    const value = rest[i + 1];
    if (flag === '--referer') {
      args.referer = value;
      i += 1;
    } else if (flag === '--channel') {
      args.channel = value;
      i += 1;
    } else if (flag === '--timeout-ms') {
      args.timeoutMs = parseInt(value, 10);
      i += 1;
    } else if (flag === '--cdp-url') {
      args.cdpUrl = value;
      i += 1;
    } else if (flag === '--reuse-tab') {
      args.reuseTab = true;
    } else if (flag === '--html-out') {
      args.htmlOut = value;
      i += 1;
    } else if (flag === '--page-kind') {
      args.pageKind = value;
      i += 1;
    } else {
      throw new Error(`Unknown argument: ${flag}`);
    }
  }

  return args;
}

async function listingCount(page) {
  let total = 0;
  for (const selector of LISTING_SELECTORS) {
    total += await page.locator(selector).count();
  }
  return total;
}

async function pickExistingPage(browser) {
  const pages = [];
  for (const context of browser.contexts()) {
    pages.push(...context.pages());
  }

  const usable = pages.filter((page) => {
    const url = page.url() || '';
    return (
      url.startsWith('http://') ||
      url.startsWith('https://') ||
      url === 'about:blank'
    );
  });

  for (const page of usable) {
    if (page.url().includes('/vehicles/cars') && (await listingCount(page)) > 0) {
      return page;
    }
  }
  for (const page of usable) {
    if (page.url().includes('yad2.co.il')) {
      return page;
    }
  }
  for (const page of usable) {
    if (page.url().includes('/vehicles/cars')) {
      return page;
    }
  }
  return usable[0] || pages[0] || null;
}

async function waitForListings(page, timeoutMs) {
  const started = Date.now();
  const heartbeat = setInterval(() => {
    process.stderr.write(`Still waiting... ${page.url()}\n`);
  }, 5000);

  try {
    await page.waitForFunction(
      (selectors) => selectors.some((selector) => document.querySelector(selector)),
      LISTING_SELECTORS,
      { timeout: timeoutMs }
    );
  } catch (_err) {
    process.stderr.write(
      `Timed out after ${Math.round((Date.now() - started) / 1000)}s waiting for listing cards on ${page.url()}\n`
    );
  } finally {
    clearInterval(heartbeat);
  }
}

async function waitForDetail(page, timeoutMs) {
  const started = Date.now();
  const heartbeat = setInterval(() => {
    process.stderr.write(`Still waiting for detail... ${page.url()}\n`);
  }, 5000);

  try {
    await page.waitForFunction(
      (selectors) => {
        if (selectors.some((selector) => document.querySelector(selector))) {
          const script = document.querySelector('script#__NEXT_DATA__');
          if (!script || !script.textContent) return true;
          // Prefer pages that already hydrated listing JSON with km.
          return script.textContent.includes('"km"') || script.textContent.includes('additional-info');
        }
        return false;
      },
      DETAIL_READY_SELECTORS,
      { timeout: timeoutMs }
    );
  } catch (_err) {
    process.stderr.write(
      `Timed out after ${Math.round((Date.now() - started) / 1000)}s waiting for detail content on ${page.url()}\n`
    );
  } finally {
    clearInterval(heartbeat);
  }
}

async function main() {
  const { url, referer, channel, timeoutMs, cdpUrl, reuseTab, htmlOut, pageKind } = parseArgs(process.argv);
  if (!htmlOut) {
    throw new Error('--html-out <path> is required');
  }
  if (pageKind !== 'search' && pageKind !== 'detail') {
    throw new Error(`Unknown --page-kind: ${pageKind}`);
  }

  let browser;
  let page;

  if (cdpUrl) {
    browser = await chromium.connectOverCDP(cdpUrl);
  } else {
    browser = await chromium.launch({ channel, headless: false });
  }

  try {
    if (cdpUrl) {
      page = await pickExistingPage(browser);
    }

    const alreadyHasListings = page ? (await listingCount(page)) > 0 && page.url().includes('/vehicles/cars') : false;
    const shouldNavigate = !(reuseTab && alreadyHasListings && pageKind === 'search');

    if (!page) {
      const context =
        browser.contexts()[0] || (await browser.newContext({ locale: 'he-IL' }));
      page = await context.newPage();
    }

    if (cdpUrl) {
      process.stderr.write('\nAttached to an already-open Chrome (CDP).\n');
      process.stderr.write(`Using tab: ${page.url()}\n`);
    } else {
      process.stderr.write('\nA visible browser window has opened.\n');
    }

    if (shouldNavigate) {
      process.stderr.write(`Navigating this tab to the ${pageKind} URL...\n`);
      const gotoOptions = { waitUntil: 'domcontentloaded', timeout: timeoutMs };
      if (referer) {
        gotoOptions.referer = referer;
      }
      await page.goto(url, gotoOptions);
      await page.bringToFront();
      process.stderr.write(`Now at: ${page.url()}\n`);
    } else {
      process.stderr.write('Search listings already visible; skipping navigation.\n');
    }

    if (pageKind === 'detail') {
      process.stderr.write('Waiting for detail content to appear...\n');
      await waitForDetail(page, timeoutMs);
    } else {
      process.stderr.write('Waiting for listing cards to appear...\n');
      await waitForListings(page, timeoutMs);
    }

    const html = await page.content();
    const title = await page.title();
    const count = pageKind === 'detail' ? 0 : await listingCount(page);
    if (pageKind === 'detail') {
      process.stderr.write(`Captured detail page on ${page.url()}\n`);
    } else {
      process.stderr.write(`Found ${count} listing card(s) on ${page.url()}\n`);
    }

    fs.writeFileSync(htmlOut, html, 'utf8');
    process.stdout.write(`${JSON.stringify({ title, listingCount: count, htmlPath: htmlOut, pageKind })}\n`);
  } finally {
    // For connectOverCDP, close() disconnects without quitting the user's Chrome.
    // Leaving the connection open keeps the Node process alive indefinitely.
    await browser.close();
  }
}

main().catch((err) => {
  process.stderr.write(`Browser collection failed: ${err && err.message ? err.message : err}\n`);
  process.exitCode = 1;
});
