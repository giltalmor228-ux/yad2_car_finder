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
 *     [--timeout-ms <ms>] [--cdp-url <url>] [--reuse-tab]
 *
 * On success, prints a single JSON line to stdout:
 *   {"html": "...", "title": "...", "listingCount": N}
 *
 * All status/prompt output is written to stderr so stdout only ever
 * contains the final JSON result.
 */

const { chromium } = require('playwright');

const LISTING_SELECTORS = [
  'a[data-nagish="private-item-link"][data-listing-type]',
  'a[data-nagish="private-item-link"]',
  'a[href*="/vehicles/"][href*="item/"]',
];

function parseArgs(argv) {
  const rest = argv.slice(2);
  if (rest.length === 0 || rest[0].startsWith('--')) {
    throw new Error(
      'Usage: node fetch_page.js <url> [--referer <referer>] [--channel <channel>] [--timeout-ms <ms>] [--cdp-url <url>] [--reuse-tab]'
    );
  }

  const args = {
    url: rest[0],
    referer: null,
    channel: 'chrome',
    timeoutMs: 60000,
    cdpUrl: null,
    reuseTab: false,
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
  for (const page of pages) {
    if (page.url().includes('/vehicles/cars') && (await listingCount(page)) > 0) {
      return page;
    }
  }
  for (const page of pages) {
    if (page.url().includes('/vehicles/cars')) {
      return page;
    }
  }
  return pages[0] || null;
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

async function main() {
  const { url, referer, channel, timeoutMs, cdpUrl, reuseTab } = parseArgs(process.argv);

  let browser;
  let launched = false;
  let createdPage = false;
  let page;

  if (cdpUrl) {
    browser = await chromium.connectOverCDP(cdpUrl);
  } else {
    browser = await chromium.launch({ channel, headless: false });
    launched = true;
  }

  try {
    if (cdpUrl) {
      page = await pickExistingPage(browser);
    }

    const alreadyHasListings = page ? (await listingCount(page)) > 0 && page.url().includes('/vehicles/cars') : false;
    const shouldNavigate = !(reuseTab && alreadyHasListings);

    if (!page) {
      const context =
        browser.contexts()[0] || (await browser.newContext({ locale: 'he-IL' }));
      page = await context.newPage();
      createdPage = true;
    }

    if (cdpUrl) {
      process.stderr.write('\nAttached to an already-open Chrome (CDP).\n');
      process.stderr.write(`Using tab: ${page.url()}\n`);
    } else {
      process.stderr.write('\nA visible browser window has opened.\n');
    }

    if (shouldNavigate) {
      process.stderr.write(`Navigating this tab to the search URL...\n`);
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

    process.stderr.write('Waiting for listing cards to appear...\n');
    await waitForListings(page, timeoutMs);

    const html = await page.content();
    const title = await page.title();
    const count = await listingCount(page);
    process.stderr.write(`Found ${count} listing card(s) on ${page.url()}\n`);

    process.stdout.write(`${JSON.stringify({ html, title, listingCount: count })}\n`);
  } finally {
    if (launched) {
      await browser.close();
    } else if (createdPage && page) {
      await page.close();
    }
  }
}

main().catch((err) => {
  process.stderr.write(`Browser collection failed: ${err && err.message ? err.message : err}\n`);
  process.exitCode = 1;
});
