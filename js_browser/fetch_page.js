#!/usr/bin/env node
'use strict';

/**
 * User-assisted browser collector for Yad2 Car Finder Bot.
 *
 * Either launches a visible Chrome window, or attaches to a Chrome instance
 * the user already started with --remote-debugging-port. After navigation it
 * waits until listing cards appear, the visible count stabilizes, and scrolls
 * to load more feed cards, then snapshots the page. It does not automate or
 * bypass verification/captchas.
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

// Strict selector used for counting private cards.
const PRIMARY_LISTING_SELECTOR =
  'a[data-nagish="private-item-link"][data-listing-type]';

// All main-feed card types the user sees (private + agency/platinum/ultra).
const FEED_LISTING_SELECTORS = [
  PRIMARY_LISTING_SELECTOR,
  'a[data-nagish="agent-item-link"][data-listing-type]',
  'a[data-nagish="agent-item-no-footer-link"][data-listing-type]',
  'a[data-listing-type="ultra-plus"]',
];

// Broader fallbacks only for "any cards present?" detection on odd pages.
const LISTING_READY_SELECTORS = [
  ...FEED_LISTING_SELECTORS,
  'a[data-nagish="private-item-link"]',
  'a[href*="/vehicles/"][href*="item/"]',
];

const DETAIL_READY_SELECTORS = [
  'script#__NEXT_DATA__',
  'section[data-testid="additional-info"]',
  'p[data-testid="vehicle-description"]',
];

// After the first card appears, keep polling until the count is unchanged
// for STABLE_POLLS consecutive checks (or until SETTLE_MS elapses).
const SETTLE_MS = 10000;
const STABLE_POLL_MS = 500;
const STABLE_POLLS = 4; // 2s of unchanged count

// Scroll to load more feed cards (lazy / infinite scroll).
const SCROLL_PAUSE_MS = 900;
const MAX_SCROLL_ROUNDS = 15;
const NO_GROWTH_ROUNDS = 3; // stop after this many scrolls with no new cards
const SCROLL_BUDGET_MS = 25000;

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

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function normalizeSearchParam(value) {
  return String(value || '')
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean)
    .sort()
    .join(',');
}

function searchUrlsMatch(currentUrl, targetUrl) {
  /** True when both URLs are the same Yad2 search (ignore tracking params). */
  try {
    const current = new URL(currentUrl);
    const target = new URL(targetUrl);
    if (current.origin !== target.origin || current.pathname !== target.pathname) {
      return false;
    }
    const ignore = new Set([
      'opened-from',
      'component-type',
      'spot',
      'location',
      'pagination',
      'yad2_source',
    ]);
    const keys = new Set([
      ...current.searchParams.keys(),
      ...target.searchParams.keys(),
    ]);
    for (const key of keys) {
      if (ignore.has(key)) continue;
      const left = normalizeSearchParam(current.searchParams.get(key));
      const right = normalizeSearchParam(target.searchParams.get(key));
      if (left !== right) return false;
    }
    return true;
  } catch (_err) {
    return false;
  }
}

async function listingCount(page) {
  // Count unique hrefs across private + agency feed card types.
  return page.evaluate((selectors) => {
    const hrefs = new Set();
    for (const selector of selectors) {
      for (const el of document.querySelectorAll(selector)) {
        const href = el.getAttribute('href') || el.getAttribute('data-testid') || '';
        if (href) hrefs.add(href);
      }
    }
    return hrefs.size;
  }, FEED_LISTING_SELECTORS);
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
      LISTING_READY_SELECTORS,
      { timeout: timeoutMs }
    );
  } catch (_err) {
    process.stderr.write(
      `Timed out after ${Math.round((Date.now() - started) / 1000)}s waiting for listing cards on ${page.url()}\n`
    );
    return;
  } finally {
    clearInterval(heartbeat);
  }

  // Cards often hydrate in waves (organic + platinum). Wait until the visible
  // count stops changing before scrolling for more.
  let remaining = Math.max(0, timeoutMs - (Date.now() - started));
  const settleBudget = Math.min(SETTLE_MS, remaining || SETTLE_MS);
  await waitForListingCountStable(page, settleBudget);

  remaining = Math.max(0, timeoutMs - (Date.now() - started));
  const scrollBudget = Math.min(SCROLL_BUDGET_MS, remaining || SCROLL_BUDGET_MS);
  if (scrollBudget >= SCROLL_PAUSE_MS * 2) {
    await scrollToLoadMoreListings(page, scrollBudget);
    // Brief re-settle after the last scroll batch.
    await waitForListingCountStable(page, Math.min(SETTLE_MS, 3000));
  }
}

async function waitForListingCountStable(page, settleMs) {
  const deadline = Date.now() + settleMs;
  let last = -1;
  let stablePolls = 0;
  let best = 0;

  process.stderr.write('Waiting for listing list to stabilize...\n');

  while (Date.now() < deadline) {
    const n = await listingCount(page);
    best = Math.max(best, n);

    if (n > 0 && n === last) {
      stablePolls += 1;
      if (stablePolls >= STABLE_POLLS) {
        process.stderr.write(`Listing list stabilized at ${n} card(s).\n`);
        return n;
      }
    } else {
      if (n !== last && n > 0) {
        process.stderr.write(`Listings still loading... ${n} card(s)\n`);
      }
      last = n;
      stablePolls = 0;
    }

    await sleep(STABLE_POLL_MS);
  }

  // Soft extra: give React one short beat after the settle window.
  await sleep(STABLE_POLL_MS);
  const finalCount = await listingCount(page);
  process.stderr.write(
    `Settle window ended with ${finalCount} card(s)` +
      (best > finalCount ? ` (saw up to ${best}).\n` : '.\n')
  );
  return finalCount;
}

async function scrollToLoadMoreListings(page, budgetMs) {
  const deadline = Date.now() + budgetMs;
  let previous = await listingCount(page);
  let noGrowth = 0;

  process.stderr.write(
    `Scrolling to load more listings (start=${previous} card(s))...\n`
  );

  for (let round = 1; round <= MAX_SCROLL_ROUNDS; round += 1) {
    if (Date.now() >= deadline) {
      process.stderr.write('Scroll budget exhausted.\n');
      break;
    }

    await page.evaluate(() => {
      const step = Math.max(window.innerHeight || 800, 600);
      window.scrollBy(0, step);
      // Also nudge common feed containers in case the window itself does not scroll.
      const nodes = document.querySelectorAll(
        '[data-testid*="feed"], main, #__next, [class*="feed"]'
      );
      for (const node of nodes) {
        if (node && node.scrollHeight > node.clientHeight + 40) {
          node.scrollTop = Math.min(node.scrollTop + step, node.scrollHeight);
        }
      }
    });

    await sleep(SCROLL_PAUSE_MS);
    const current = await listingCount(page);

    if (current > previous) {
      process.stderr.write(
        `Scroll ${round}/${MAX_SCROLL_ROUNDS}: ${previous} → ${current} card(s)\n`
      );
      previous = current;
      noGrowth = 0;
    } else {
      noGrowth += 1;
      process.stderr.write(
        `Scroll ${round}/${MAX_SCROLL_ROUNDS}: still ${current} card(s) ` +
          `(no growth ${noGrowth}/${NO_GROWTH_ROUNDS})\n`
      );
      if (noGrowth >= NO_GROWTH_ROUNDS) {
        process.stderr.write('No more new cards after scrolling; stopping.\n');
        break;
      }
    }
  }

  // Return to top so the snapshot matches a normal page view (DOM still keeps
  // cards that were already mounted).
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(200);

  const finalCount = await listingCount(page);
  process.stderr.write(`After scroll-load: ${finalCount} card(s)\n`);
  return finalCount;
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

    const onTargetSearch =
      page &&
      pageKind === 'search' &&
      searchUrlsMatch(page.url(), url) &&
      (await listingCount(page)) > 0;
    // Only skip navigation when REUSE_TAB is set AND the tab is already on
    // this exact search URL with listings. Never reuse a different group's page.
    const shouldNavigate = !(reuseTab && onTargetSearch);

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
