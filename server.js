"use strict";
const express = require("express");
const { chromium } = require("playwright");
const dns = require("dns").promises;
const net = require("net");
const tls = require("tls");

const app = express();
app.use(express.json({ limit: "2mb" }));

const MODE = process.env.SCRAPE_MODE || "deep";
const MAX_PAGES = parseInt(process.env.MAX_PAGES || "60", 10);
const MAX_DEPTH = parseInt(process.env.MAX_DEPTH || "4", 10);
const NAV_TIMEOUT_MS = parseInt(process.env.NAV_TIMEOUT_MS || "45000", 10);
const CONCURRENCY = parseInt(process.env.CONCURRENCY || "3", 10);
const USER_AGENT = process.env.USER_AGENT ||
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36";

// ─────────────────────────────────────────────
// MARITIME DEPARTMENT CLASSIFICATION
// ─────────────────────────────────────────────
const MARITIME_DEPARTMENTS = {
  technical: {
    keywords: [
      "technical","tech","fleet","superintendent","supt","engineer","engineering",
      "maintenance","drydock","dry-dock","hseq","qhsse","qse","dpa",
      "vetting","inspection","class","classification","ism","isps",
      "operations","ops","crewing","crew","manning","nautical",
      "fleetops","techops","navtech","fleetmgr","techsupt","marinesupt",
      "shipmanager","vesselops","shipops"
    ],
    pageKeywords: [
      "technical","fleet","operations","management","superintendent",
      "drydock","maintenance","hseq","crewing","manning","vetting"
    ],
    priority: 1
  },
  purchasing: {
    keywords: [
      "purch","purchase","purchasing","procure","procurement","buyer",
      "supply","spares","stores","vendor","rfq","po","spareparts",
      "spare","parts","supplychain","supply-chain","logistics","warehouse",
      "stock","chandler","storekeeper","provisions","provisions-dept",
      "spare-parts","procurement-dept"
    ],
    pageKeywords: [
      "procurement","purchasing","supply","spares","stores","vendor",
      "logistics","spare-parts","warehouse","chandler","provisions"
    ],
    priority: 2
  },
  commercial: {
    keywords: [
      "commercial","chartering","charter","fixture","cargo","freight",
      "trading","operator","post-fixture","voyage","bunker","bunkering",
      "claims","insurance","legal","finance","accounting","accounts",
      "charterops","voyageops","postfixture","bunkerdesk","bunkers",
      "ops-commercial","tradingdesk"
    ],
    pageKeywords: [
      "commercial","chartering","trading","bunker","claims","finance"
    ],
    priority: 3
  },
  management: {
    keywords: [
      "director","manager","ceo","coo","cto","president","vice",
      "head","chief","gm","general-manager","md","managing",
      "generalmanager","vp","exec","executive"
    ],
    pageKeywords: [
      "management","leadership","team","about","company"
    ],
    priority: 4
  },
  general: {
    keywords: [
      "info","contact","office","admin","mail","reception",
      "press","marketing","hr","career","careers","hello","enquiry",
      "inquiry","general","support","service"
    ],
    pageKeywords: [
      "contact","about","imprint","legal"
    ],
    priority: 5
  }
};

// ─────────────────────────────────────────────
// ANTISPAM LAYER
// ─────────────────────────────────────────────
const SPAM_WORDS_SUBJECT = [
  "free","guarantee","guaranteed","winner","won","prize","click here",
  "buy now","limited time","act now","urgent","congratulations",
  "million dollars","make money","earn extra","no cost","risk free"
];
const SPAM_WORDS_BODY = [
  "unsubscribe","opt-out","opt out","click below","click here",
  "bulk","mass email","mailing list","email marketing"
];

function antispamCheck(subject = "", body = "") {
  const issues = [];
  const subjectLower = subject.toLowerCase();
  const bodyLower = body.toLowerCase();
  for (const word of SPAM_WORDS_SUBJECT)
    if (subjectLower.includes(word)) issues.push(`spam_word_subject: "${word}"`);
  for (const word of SPAM_WORDS_BODY)
    if (bodyLower.includes(word)) issues.push(`spam_word_body: "${word}"`);
  const capsRatio = subject.replace(/[^A-Z]/g, "").length / (subject.length || 1);
  if (capsRatio > 0.3) issues.push("excessive_caps");
  if (subject.length > 80) issues.push("subject_too_long");
  if (subject.length < 5) issues.push("subject_too_short");
  const linkCount = (body.match(/https?:\/\//g) || []).length;
  if (linkCount > 3) issues.push(`too_many_links: ${linkCount}`);
  return { passed: issues.length === 0, score: Math.max(0, 100 - issues.length * 15), issues };
}

// ─────────────────────────────────────────────
// MX CACHE
// ─────────────────────────────────────────────
const mxCache = new Map();

async function getMxHost(domain) {
  if (mxCache.has(domain)) return mxCache.get(domain);
  try {
    const records = await dns.resolveMx(domain);
    if (!records || !records.length) { mxCache.set(domain, null); return null; }
    const host = records.sort((a, b) => a.priority - b.priority)[0].exchange;
    mxCache.set(domain, host);
    return host;
  } catch {
    mxCache.set(domain, null);
    return null;
  }
}

// ─────────────────────────────────────────────
// SMTP VERIFY — Multi-port, STARTTLS, TLS, multi-line response
// ─────────────────────────────────────────────
async function smtpVerifyOnPort(email, mxHost, port, timeoutMs = 12000) {
  return new Promise((resolve) => {
    const domain = email.split("@")[1];
    const fakeNames = ["jsmith", "mwilliams", "tbrown", "kjones", "rgarcia"];
    const fakeName = fakeNames[Math.floor(Math.random() * fakeNames.length)];
    const fakeEmail = `${fakeName}${Math.floor(Math.random() * 900 + 100)}@${domain}`;

    let resolved = false;
    const done = (result) => {
      if (!resolved) {
        resolved = true;
        try { getActiveSocket()?.destroy(); } catch {}
        resolve({ ...result, port });
      }
    };

    // STATE: 0=BANNER 1=EHLO 2=STARTTLS_CMD 3=EHLO2 4=MAILFROM 5=RCPT_REAL 6=RCPT_FAKE
    let state = 0;
    let rawSock = null;
    let tlsSock = null;
    const getActiveSocket = () => tlsSock || rawSock;
    let buf = "";

    const sendCmd = (cmd) => {
      const s = getActiveSocket();
      if (s && !s.destroyed) s.write(cmd);
    };

    const handleFinalCode = (code) => {
      // 421 = greylisting (temp reject, not invalid)
      if (state === 5 && code === 421) {
        return done({ valid: true, reason: "greylisted", catchAll: false });
      }
      if (code >= 500) {
        if (state === 5) return done({ valid: false, reason: `rcpt_rejected_${code}`, catchAll: false });
        return done({ valid: false, reason: `smtp_error_${code}`, catchAll: false });
      }
      if (code >= 400) {
        return done({ valid: false, reason: `temp_error_${code}`, catchAll: false });
      }

      switch (state) {
        case 0: // BANNER
          if (code === 220) { state = 1; sendCmd("EHLO maritimeintel.com\r\n"); }
          break;
        case 1: // EHLO
          if (code === 250) {
            if (port === 587) {
              state = 2; sendCmd("STARTTLS\r\n");
            } else {
              state = 4; sendCmd("MAIL FROM:<probe@maritimeintel.com>\r\n");
            }
          }
          break;
        case 2: // STARTTLS_CMD
          if (code === 220) {
            state = 3;
            const upgraded = tls.connect({
              socket: rawSock,
              servername: mxHost,
              rejectUnauthorized: false
            });
            tlsSock = upgraded;
            upgraded.on("data", dataHandler);
            upgraded.on("error", () => done({ valid: false, reason: "tls_error", catchAll: false }));
            upgraded.once("secureConnect", () => {
              state = 3; sendCmd("EHLO maritimeintel.com\r\n");
            });
          } else {
            // STARTTLS not supported — proceed plain
            state = 4; sendCmd("MAIL FROM:<probe@maritimeintel.com>\r\n");
          }
          break;
        case 3: // EHLO2 (post-STARTTLS)
          if (code === 250) { state = 4; sendCmd("MAIL FROM:<probe@maritimeintel.com>\r\n"); }
          break;
        case 4: // MAILFROM
          if (code === 250) { state = 5; sendCmd(`RCPT TO:<${email}>\r\n`); }
          break;
        case 5: // RCPT_REAL
          if (code === 250 || code === 251) {
            state = 6; sendCmd(`RCPT TO:<${fakeEmail}>\r\n`);
          } else {
            done({ valid: false, reason: `rcpt_rejected_${code}`, catchAll: false });
          }
          break;
        case 6: { // RCPT_FAKE (catch-all test)
          const catchAll = (code === 250 || code === 251);
          sendCmd("QUIT\r\n");
          done({ valid: true, reason: "verified", catchAll });
          break;
        }
      }
    };

    const dataHandler = (d) => {
      buf += d.toString();
      let crlf;
      while ((crlf = buf.indexOf("\r\n")) !== -1) {
        const line = buf.slice(0, crlf);
        buf = buf.slice(crlf + 2);
        if (!line) continue;
        const code = parseInt(line.slice(0, 3), 10);
        if (isNaN(code)) continue;
        // Multi-line SMTP: line[3] === "-" means continuation, wait for final
        const isContinuation = line[3] === "-";
        if (!isContinuation) handleFinalCode(code);
      }
    };

    const onError = () => done({ valid: false, reason: "connection_error", catchAll: false });
    const onTimeout = () => done({ valid: false, reason: "timeout", catchAll: false });

    if (port === 465) {
      // Implicit TLS (SMTPS)
      const sock = tls.connect({ host: mxHost, port: 465, rejectUnauthorized: false, servername: mxHost });
      tlsSock = sock;
      sock.setTimeout(timeoutMs);
      sock.on("timeout", onTimeout);
      sock.on("error", onError);
      sock.on("data", dataHandler);
    } else {
      // Plain TCP — port 25 or 587 (587 upgrades via STARTTLS)
      const sock = net.createConnection(port, mxHost);
      rawSock = sock;
      sock.setTimeout(timeoutMs);
      sock.on("timeout", onTimeout);
      sock.on("error", onError);
      sock.on("data", dataHandler);
    }
  });
}

// Port order: 25 first (most reliable for RCPT verify), then 465, 587
async function smtpVerify(email, domain) {
  const mxHost = await getMxHost(domain);
  if (!mxHost) return { valid: false, reason: "no_mx", catchAll: false };

  const ports = [25, 465, 587];
  for (const port of ports) {
    const result = await smtpVerifyOnPort(email, mxHost, port, 12000);
    if (result.reason !== "connection_error" && result.reason !== "timeout") {
      return { ...result, port };
    }
  }
  return { valid: false, reason: "all_ports_failed", catchAll: false };
}

// ─────────────────────────────────────────────
// DEPARTMENT CLASSIFICATION (improved matching)
// ─────────────────────────────────────────────
function classifyDepartment(email, sourceUrls = []) {
  const rawLocal = (email.split("@")[0] || "").toLowerCase();
  const local = rawLocal.replace(/[._-]/g, "");
  const urlsText = sourceUrls.join(" ").toLowerCase();

  for (const [dept, config] of Object.entries(MARITIME_DEPARTMENTS)) {
    for (const kw of config.keywords) {
      const kwNorm = kw.replace(/[._-]/g, "");
      if (local === kwNorm)
        return { department: dept, confidence_bonus: 0.35, signal: "local_exact" };
      if (local.startsWith(kwNorm) || local.endsWith(kwNorm))
        return { department: dept, confidence_bonus: 0.28, signal: "local_prefix_suffix" };
      if (local.includes(kwNorm))
        return { department: dept, confidence_bonus: 0.20, signal: "local_contains" };
    }
  }

  for (const [dept, config] of Object.entries(MARITIME_DEPARTMENTS)) {
    for (const kw of config.pageKeywords) {
      if (urlsText.includes(kw))
        return { department: dept, confidence_bonus: 0.12, signal: "url_keyword" };
    }
  }

  return { department: "unknown", confidence_bonus: 0, signal: "none" };
}

// ─────────────────────────────────────────────
// EMAIL SCORING (multi-source bonus)
// ─────────────────────────────────────────────
function scoreEmail(email, baseHost, sourceUrls = []) {
  const endsCompany = email.endsWith(`@${baseHost}`);
  let score = 0.30;
  if (endsCompany) score += 0.25;

  const { department, confidence_bonus } = classifyDepartment(email, sourceUrls);
  score += confidence_bonus;

  // Multi-source bonus: found on multiple different pages
  const uniqueSources = new Set(sourceUrls).size;
  if (uniqueSources >= 2) score += 0.10;
  if (uniqueSources >= 3) score += 0.10;

  if (department === "general") score += 0.05;
  if (department === "unknown") score -= 0.05;

  score = Math.max(0, Math.min(1, score));
  return {
    email,
    department,
    confidence: parseFloat(score.toFixed(2)),
    sources: sourceUrls.slice(0, 5),
    source_count: uniqueSources
  };
}

// ─────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────
function uniq(arr) { return Array.from(new Set(arr)); }

// Decode CloudFlare email protection (data-cfemail attribute)
function decodeCFEmail(hex) {
  try {
    const r = parseInt(hex.slice(0, 2), 16);
    let result = "";
    for (let i = 2; i < hex.length; i += 2) {
      result += String.fromCharCode(parseInt(hex.slice(i, i + 2), 16) ^ r);
    }
    return result;
  } catch { return ""; }
}

function normalizeText(t) {
  return (t || "")
    .replace(/&#x40;/gi, "@")
    .replace(/&#64;/gi, "@")
    .replace(/&amp;/gi, "&")
    .replace(/\[dot\]/gi, ".")
    .replace(/\(dot\)/gi, ".")
    .replace(/\s+dot\s+/gi, ".")
    .replace(/\s*\(at\)\s*/gi, "@")
    .replace(/\s*\[at\]\s*/gi, "@")
    .replace(/\s+at\s+/gi, "@")
    .replace(/\s*_at_\s*/gi, "@")
    .replace(/\s*__at__\s*/gi, "@");
}

function extractEmailsFromText(t) {
  const text = normalizeText(String(t || "")).toLowerCase();
  const out = [];
  let m;
  const re = /([a-z0-9._%+-]+)@([a-z0-9.-]+\.[a-z]{2,})/gi;
  while ((m = re.exec(text)) !== null) {
    const email = (m[1] + "@" + m[2]).toLowerCase();
    // Filter binary/asset file false positives
    if (!email.match(/@.*\.(png|jpg|gif|svg|ico|css|js|woff|ttf)$/i)) out.push(email);
  }
  return out;
}

// Extract emails from data-* attributes and CloudFlare obfuscation
function extractDataEmails(html) {
  const emails = [];
  const dataEmailRe = /data-email=["']([^"'@\s]{2,}@[^"'@\s]{2,})["']/gi;
  let m;
  while ((m = dataEmailRe.exec(html)) !== null) {
    emails.push(...extractEmailsFromText(m[1]));
  }
  const cfRe = /data-cfemail=["']([0-9a-f]+)["']/gi;
  while ((m = cfRe.exec(html)) !== null) {
    const decoded = decodeCFEmail(m[1]);
    if (decoded.includes("@")) emails.push(decoded.toLowerCase());
  }
  return emails;
}

// Extract mailto: links — most reliable email source
function extractMailtoEmails(html) {
  const emails = [];
  const mailtoRe = /href=["']mailto:([^"'?&\s]+)["']/gi;
  let m;
  while ((m = mailtoRe.exec(html)) !== null) {
    const raw = decodeURIComponent(m[1]).toLowerCase().trim();
    if (raw.includes("@")) emails.push(raw);
  }
  return emails;
}

function isSameHost(url, baseHost) {
  try { return new URL(url).hostname.replace(/^www\./, "") === baseHost; } catch { return false; }
}

function absolutize(href, baseUrl) {
  try { return new URL(href, baseUrl).toString(); } catch { return null; }
}

function extractLinks(html, baseUrl, baseHost) {
  const links = [];
  const hrefRe = /href=["']([^"']+)["']/gi;
  let m;
  while ((m = hrefRe.exec(html)) !== null) {
    const raw = m[1];
    if (!raw || raw.startsWith("javascript:") || raw.startsWith("mailto:")) continue;
    const abs = absolutize(raw, baseUrl);
    if (!abs || !isSameHost(abs, baseHost)) continue;
    links.push(abs.split("#")[0]);
  }
  return uniq(links);
}

const KEYWORDS_PAGES = [
  "contact","contact-us","contacts","about","company","team","management",
  "fleet","operations","technical","tech-management","technical-management",
  "procurement","purchasing","purchase","supplier","suppliers","spares",
  "stores","spare","parts","hseq","safety","quality","vendor","supply-chain",
  "commercial","chartering","crewing","manning","careers","people",
  "chandler","provisions","bunker","vetting","imprint"
];

function prioritizeLinks(links) {
  const scored = links.map(u => {
    const lu = u.toLowerCase();
    let s = 0;
    for (const k of KEYWORDS_PAGES) if (lu.includes(k)) s += 5;
    if (lu.endsWith(".pdf")) s += 9;
    return { u, s };
  });
  scored.sort((a, b) => b.s - a.s);
  return scored.map(x => x.u);
}

// ─────────────────────────────────────────────
// SITEMAP PARSER
// ─────────────────────────────────────────────
async function fetchSitemapUrls(home, baseHost, context) {
  const candidates = [
    `${home}/sitemap.xml`,
    `${home}/sitemap_index.xml`,
    `${home}/robots.txt`
  ];
  const urls = [];
  for (const url of candidates) {
    let page;
    try {
      page = await context.newPage();
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 15000 });
      const content = await page.content();
      const locRe = /<loc>\s*(https?:\/\/[^<]+)\s*<\/loc>/gi;
      let m;
      while ((m = locRe.exec(content)) !== null) {
        const u = m[1].trim();
        if (isSameHost(u, baseHost)) urls.push(u);
      }
      const sitemapRe = /^Sitemap:\s*(https?:\/\/.+)$/gim;
      while ((m = sitemapRe.exec(content)) !== null) {
        const sitemapUrl = m[1].trim();
        if (!candidates.includes(sitemapUrl)) candidates.push(sitemapUrl);
      }
    } catch {}
    finally { if (page) await page.close(); }
  }
  return uniq(urls).slice(0, 100);
}

// ─────────────────────────────────────────────
// PAGE FETCHER (networkidle + scroll + data attrs)
// ─────────────────────────────────────────────
async function fetchPage(url, context) {
  const page = await context.newPage();
  try {
    const isPdf = url.toLowerCase().endsWith(".pdf");
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT_MS });

    if (!isPdf && MODE === "deep") {
      try {
        await page.waitForLoadState("networkidle", { timeout: 8000 });
      } catch {}

      await page.evaluate(async () => {
        await new Promise(resolve => {
          let total = 0;
          const dist = 400;
          const timer = setInterval(() => {
            window.scrollBy(0, dist);
            total += dist;
            if (total >= document.body.scrollHeight) { clearInterval(timer); resolve(); }
          }, 80);
          setTimeout(() => { clearInterval(timer); resolve(); }, 3000);
        });
      }).catch(() => {});
    }

    const content = await page.content();
    const text = await page.evaluate(() => document.body ? document.body.innerText : "").catch(() => "");
    const altEmails = await page.evaluate(() => {
      const texts = [];
      document.querySelectorAll("img[alt]").forEach(img => texts.push(img.getAttribute("alt") || ""));
      document.querySelectorAll("[data-email]").forEach(el => texts.push(el.getAttribute("data-email") || ""));
      return texts.join(" ");
    }).catch(() => "");

    return { content, text, altEmails };
  } catch {
    return { content: "", text: "", altEmails: "" };
  } finally {
    await page.close();
  }
}

function extractAllEmails(content, text, altEmails) {
  return uniq([
    ...extractMailtoEmails(content),   // mailto: links (most reliable)
    ...extractDataEmails(content),     // data-email + CloudFlare CF
    ...extractEmailsFromText(content), // raw HTML
    ...extractEmailsFromText(text),    // innerText
    ...extractEmailsFromText(altEmails)
  ]);
}

// ─────────────────────────────────────────────
// SCRAPE ROUTE
// ─────────────────────────────────────────────
app.post("/scrape", async (req, res) => {
  const { domain, start_url } = req.body || {};
  if (!domain && !start_url) return res.status(400).json({ error: "domain or start_url required" });

  const baseHost = (domain || new URL(start_url).hostname).replace(/^www\./, "");
  const home = start_url || `https://${baseHost}`;

  const seed_paths = [
    "/contact", "/contact-us", "/contacts", "/about/contact",
    "/imprint", "/legal-notice",
    "/procurement", "/purchasing", "/supply-chain", "/suppliers", "/vendor",
    "/operations", "/technical", "/fleet", "/shipmanagement", "/management",
    "/commercial", "/chartering", "/crewing", "/manning",
    "/team", "/people", "/about-us", "/about/team",
    "/hseq", "/safety", "/vetting", "/bunker", "/finance"
  ];

  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage"]
  });
  const context = await browser.newContext({
    userAgent: USER_AGENT,
    viewport: { width: 1366, height: 768 },
    extraHTTPHeaders: { "accept-language": "en-US,en;q=0.9" }
  });

  const visited = new Set();
  const queue = [{ url: home, depth: 0 }];

  for (const p of seed_paths) {
    try { queue.push({ url: new URL(p, home).toString(), depth: 1 }); } catch {}
  }

  try {
    const sitemapUrls = await fetchSitemapUrls(home, baseHost, context);
    for (const u of sitemapUrls) queue.push({ url: u, depth: 1 });
  } catch {}

  const sources = [];
  const pdfLinks = new Set();
  const emailToSources = new Map();

  // Concurrent worker pool — 3 pages in parallel
  async function worker() {
    while (visited.size < MAX_PAGES) {
      let item = null;
      while (queue.length > 0) {
        const candidate = queue.shift();
        if (!candidate) continue;
        if (visited.has(candidate.url)) continue;
        visited.add(candidate.url);
        item = candidate;
        break;
      }
      if (!item) break;

      const { content, text, altEmails } = await fetchPage(item.url, context);
      const found = extractAllEmails(content, text, altEmails);

      for (const e of found) {
        if (!emailToSources.has(e)) emailToSources.set(e, new Set());
        emailToSources.get(e).add(item.url);
      }

      if (item.url.toLowerCase().endsWith(".pdf")) pdfLinks.add(item.url);
      sources.push({ url: item.url, depth: item.depth });

      if (item.depth < MAX_DEPTH) {
        const links = prioritizeLinks(extractLinks(content, item.url, baseHost));
        const take = MODE === "deep" ? 30 : 10;
        for (const u of links.slice(0, take)) {
          if (!visited.has(u)) queue.push({ url: u, depth: item.depth + 1 });
        }
      }
    }
  }

  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));

  await context.close();
  await browser.close();

  const emails = uniq(Array.from(emailToSources.keys()));
  const ranked = emails
    .map(e => scoreEmail(e, baseHost, Array.from(emailToSources.get(e) || []).slice(0, 10)))
    .sort((a, b) => b.confidence - a.confidence);

  const names = req.body.names || [];
  const patternEmails = [];
  if (names.length > 0) {
    for (const fullName of names) {
      const parts = fullName.trim().toLowerCase().split(/\s+/);
      if (parts.length < 2) continue;
      const first = parts[0].replace(/[^a-z]/g, "");
      const last = parts[parts.length - 1].replace(/[^a-z]/g, "");
      const fi = first[0];
      const li = last[0];
      const patterns = [
        `${first}.${last}@${baseHost}`,
        `${fi}.${last}@${baseHost}`,
        `${first}${last}@${baseHost}`,
        `${first}@${baseHost}`,
        `${last}@${baseHost}`,
        `${fi}${last}@${baseHost}`,
        `${first}.${li}@${baseHost}`
      ];
      for (const candidate of patterns) {
        const result = await smtpVerify(candidate, baseHost);
        patternEmails.push({
          email: candidate,
          name: fullName,
          smtp_verified: result.valid,
          catch_all: result.catchAll,
          verify_port: result.port || null,
          verify_reason: result.reason,
          confidence: result.valid && !result.catchAll ? 0.90 : result.valid ? 0.60 : 0.25,
          department: classifyDepartment(candidate).department,
          source: "pattern_generator"
        });
        if (result.valid && !result.catchAll) break;
      }
    }
  }

  const buckets = {
    technical:   ranked.filter(x => x.department === "technical").slice(0, 20),
    purchasing:  ranked.filter(x => x.department === "purchasing").slice(0, 20),
    commercial:  ranked.filter(x => x.department === "commercial").slice(0, 20),
    management:  ranked.filter(x => x.department === "management").slice(0, 20),
    general:     ranked.filter(x => x.department === "general").slice(0, 20),
    unknown:     ranked.filter(x => x.department === "unknown").slice(0, 20)
  };

  res.json({
    mode: MODE,
    domain: baseHost,
    start_url: home,
    pages_visited: visited.size,
    total_emails: ranked.length,
    sources: sources.slice(0, 300),
    pdf_links: Array.from(pdfLinks).slice(0, 80),
    results: ranked.slice(0, 80),
    pattern_emails: patternEmails,
    buckets
  });
});

// ─────────────────────────────────────────────
// COMMON MARITIME PATTERN GENERATOR
// Probes 35 standard maritime role prefixes via SMTP
// ─────────────────────────────────────────────
const MARITIME_COMMON_PREFIXES = [
  "purchasing","procurement","spares","stores","supply","buyer","rfq","vendor","logistics",
  "technical","tech","fleet","superintendent","dpa","hseq","vetting","crewing","crew","manning",
  "commercial","chartering","operations","bunker","bunkers","freight","trading",
  "info","contact","office","admin","reception","mail","general","enquiries","enquiry",
  "director","manager","ceo","coo","management"
];

app.post("/generate-patterns", async (req, res) => {
  const { domain } = req.body || {};
  if (!domain) return res.status(400).json({ error: "domain required" });
  const baseHost = domain.replace(/^www\./, "");

  const results = [];
  for (const prefix of MARITIME_COMMON_PREFIXES) {
    const email = `${prefix}@${baseHost}`;
    const result = await smtpVerify(email, baseHost);
    const classification = classifyDepartment(email);
    results.push({
      email,
      department: classification.department,
      smtp_verified: result.valid,
      catch_all: result.catchAll,
      verify_port: result.port || null,
      verify_reason: result.reason,
      confidence: result.valid && !result.catchAll ? 0.95 : result.valid ? 0.65 : 0.10
    });
    await new Promise(r => setTimeout(r, 200));
  }

  const valid = results.filter(r => r.smtp_verified && !r.catch_all);
  res.json({
    domain: baseHost,
    total_probed: results.length,
    valid_count: valid.length,
    results: results.sort((a, b) => b.confidence - a.confidence)
  });
});

// ─────────────────────────────────────────────
// SMTP VERIFY — single email
// ─────────────────────────────────────────────
app.post("/verify-email", async (req, res) => {
  const { email } = req.body || {};
  if (!email) return res.status(400).json({ error: "email required" });
  const domain = email.split("@")[1];
  if (!domain) return res.status(400).json({ error: "invalid email" });

  const result = await smtpVerify(email, domain);
  const classification = classifyDepartment(email);
  res.json({
    email,
    valid: result.valid,
    catch_all: result.catchAll,
    reason: result.reason,
    port_used: result.port || null,
    department: classification.department,
    confidence: result.valid && !result.catchAll ? 0.95 : result.valid ? 0.65 : 0.10
  });
});

// ─────────────────────────────────────────────
// BULK VERIFY — up to 100 emails
// ─────────────────────────────────────────────
app.post("/verify-bulk", async (req, res) => {
  const { emails } = req.body || {};
  if (!emails || !Array.isArray(emails)) return res.status(400).json({ error: "emails array required" });
  if (emails.length > 100) return res.status(400).json({ error: "max 100 emails per request" });

  const results = [];
  for (const email of emails) {
    const domain = email.split("@")[1];
    if (!domain) { results.push({ email, valid: false, reason: "invalid_format" }); continue; }
    const result = await smtpVerify(email, domain);
    const classification = classifyDepartment(email);
    results.push({
      email,
      valid: result.valid,
      catch_all: result.catchAll,
      reason: result.reason,
      port_used: result.port || null,
      department: classification.department,
      confidence: result.valid && !result.catchAll ? 0.95 : result.valid ? 0.65 : 0.10
    });
    await new Promise(r => setTimeout(r, 300));
  }

  const valid = results.filter(r => r.valid && !r.catch_all);
  const catchAll = results.filter(r => r.valid && r.catch_all);
  const invalid = results.filter(r => !r.valid);

  res.json({
    total: results.length,
    valid_count: valid.length,
    catch_all_count: catchAll.length,
    invalid_count: invalid.length,
    results
  });
});

// ─────────────────────────────────────────────
// ANTISPAM CHECK
// ─────────────────────────────────────────────
app.post("/antispam-check", async (req, res) => {
  const { subject, body } = req.body || {};
  if (!subject && !body) return res.status(400).json({ error: "subject or body required" });
  res.json(antispamCheck(subject || "", body || ""));
});

// ─────────────────────────────────────────────
// FIND NAMES (LinkedIn via DuckDuckGo)
// ─────────────────────────────────────────────
app.post("/find-names", async (req, res) => {
  const { company_name, roles } = req.body || {};
  if (!company_name) return res.status(400).json({ error: "company_name required" });

  const targetRoles = roles || [
    "Technical Superintendent", "Fleet Manager", "Purchasing Manager",
    "DPA", "Technical Manager", "Marine Superintendent",
    "Procurement Manager", "Commercial Manager", "Crewing Manager"
  ];

  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-dev-shm-usage"] });
  const context = await browser.newContext({ userAgent: USER_AGENT, viewport: { width: 1366, height: 768 } });
  const found = [];

  for (const role of targetRoles) {
    const query = encodeURIComponent(`site:linkedin.com/in "${company_name}" "${role}"`);
    const url = `https://html.duckduckgo.com/html/?q=${query}`;
    let page;
    try {
      page = await context.newPage();
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 15000 });
      await page.waitForTimeout(1500);
      const results = await page.evaluate(() => {
        const items = [];
        document.querySelectorAll(".result__a, .result__title a, a.result__url").forEach(a => {
          const text = a.innerText || "";
          const href = a.href || "";
          if (href && href.includes("linkedin.com/in/")) items.push({ title: text, url: href });
        });
        return items;
      });
      for (const r of results) {
        const nameMatch = r.title.match(/^([A-Z][a-z]+ [A-Z][a-zA-Z\-]+)/);
        if (nameMatch) found.push({ name: nameMatch[1], role, linkedin_url: r.url });
      }
    } catch {}
    finally { if (page) await page.close(); }
  }

  await context.close();
  await browser.close();

  const seen = new Set();
  const unique = found.filter(x => { if (seen.has(x.name)) return false; seen.add(x.name); return true; });
  res.json({ company_name, total: unique.length, names: unique });
});

// ─────────────────────────────────────────────
// HEALTH
// ─────────────────────────────────────────────
app.get("/health", (_, res) => res.json({ ok: true, version: "v3", service: "maritime-email-scraper" }));

app.listen(3012, () => console.log("maritime-email-scraper v3 on :3012"));
