#!/usr/bin/env python3
"""
Daily Privacy & AI Governance Law News Search
Scans RSS feeds from privacy, legal, regulatory, and tech policy publications
for news on data privacy, AI governance, enforcement, and compliance.

Coverage:
- US Privacy Law: CCPA/CPRA, state laws, FTC, HIPAA, GLBA, COPPA
- EU & Global Privacy: GDPR, EDPB, DPA enforcement, cross-border transfers
- AI Governance: EU AI Act, NIST AI RMF, algorithmic accountability, AI audits
- Enforcement: FTC actions, DPA fines, AG settlements, class actions
- Data Breaches: incident response, breach notification, ransomware
- Adtech: tracking, cookies, consent, behavioral advertising

Results saved to: privacy_ai_results/YYYY-MM-DD.md
"""

import feedparser
import os
from datetime import datetime, timedelta
from pathlib import Path
import re
import html
import ssl
import certifi
import urllib.request

# Fix SSL certificate issues on macOS
ssl_context = ssl.create_default_context(cafile=certifi.where())

OUTPUT_DIR = Path(__file__).parent / "privacy_ai_results"

# ---------------------------------------------------------------------------
# RSS FEEDS
# ---------------------------------------------------------------------------

RSS_FEEDS = [
    # --- Privacy-focused publications ---
    ("https://fpf.org/feed/", "Future of Privacy Forum"),
    ("https://privacyinternational.org/rss.xml", "Privacy International"),
    ("https://noyb.eu/en/rss", "noyb"),  # EU privacy enforcement org

    # --- Tech & AI Policy ---
    ("https://techcrunch.com/feed/", "TechCrunch"),
    ("https://www.wired.com/feed/rss", "Wired"),
    ("https://feeds.arstechnica.com/arstechnica/index", "Ars Technica"),
    ("https://themarkup.org/feeds/rss.xml", "The Markup"),
    ("https://www.eff.org/rss/updates.xml", "EFF"),

    # --- Investigative / Advocacy ---
    ("https://epic.org/feed/", "EPIC"),
    ("https://krebsonsecurity.com/feed/", "Krebs on Security"),

    # --- Cybersecurity / Breach ---
    ("https://www.darkreading.com/rss.xml", "Dark Reading"),

]

# ---------------------------------------------------------------------------
# PRIVACY & AI GOVERNANCE KEYWORDS
# ---------------------------------------------------------------------------

# Core privacy law terms — any of these signal relevance
PRIVACY_LAW_TERMS = [
    "privacy law", "data privacy", "data protection", "personal data",
    "personal information", "privacy regulation", "privacy policy",
    "consumer privacy", "privacy rights", "right to privacy",
    "gdpr", "ccpa", "cpra", "hipaa", "glba", "coppa", "ferpa", "bipa",
    "virginia consumer data protection", "colorado privacy act",
    "connecticut data privacy", "texas data privacy", "utah consumer privacy",
    "comprehensive privacy", "state privacy law", "privacy act",
    "data subject", "data controller", "data processor", "lawful basis",
    "consent management", "opt-out", "opt-in", "right to erasure",
    "right to deletion", "data minimization", "purpose limitation",
    "privacy notice", "privacy by design",
]

# AI governance and regulation terms
AI_GOVERNANCE_TERMS = [
    "eu ai act", "artificial intelligence act", "ai regulation", "ai governance",
    "nist ai rmf", "nist ai", "ai risk management", "algorithmic accountability",
    "algorithmic fairness", "ai audit", "ai auditing", "conformity assessment",
    "high-risk ai", "ai liability", "responsible ai", "trustworthy ai",
    "ai ethics", "explainable ai", "xai", "model transparency", "model card",
    "foundation model", "large language model", "llm", "generative ai",
    "chatgpt", "gpt", "claude", "gemini", "ai system", "automated decision",
    "algorithmic decision", "profiling", "ai bias", "ai fairness",
    "deepfake", "synthetic media", "biometric", "facial recognition",
    "ai safety", "ai oversight", "ai policy", "ai bill",
    "differential privacy", "federated learning", "privacy-preserving",
]

# Enforcement and regulatory action terms
ENFORCEMENT_TERMS = [
    "ftc", "federal trade commission", "cfpb", "consumer financial protection",
    "department of justice", "doj", "hhs ocr", "attorney general",
    "edpb", "european data protection board", "ico", "information commissioner",
    "cnil", "supervisory authority", "data protection authority", "dpa",
    "enforcement action", "civil penalty", "fine", "gdpr fine", "settlement",
    "consent decree", "consent order", "class action", "lawsuit", "litigation",
    "complaint", "investigation", "inquiry", "enforcement", "violation",
    "noncompliance", "breach of", "injunction",
]

# Data breach and security terms
BREACH_TERMS = [
    "data breach", "breach notification", "security incident", "ransomware",
    "cyberattack", "cyber incident", "hack", "leaked data", "data leak",
    "exposed records", "unauthorized access", "credential stuffing",
    "phishing", "social engineering", "identity theft", "incident response",
    "notif", "records exposed",
]

# Adtech and tracking terms
ADTECH_TERMS = [
    "adtech", "advertising technology", "behavioral advertising",
    "cookie", "tracking pixel", "third-party tracking", "cross-site tracking",
    "fingerprinting", "device fingerprint", "cookie consent", "cookie banner",
    "consent management platform", "cmp", "targeted advertising", "retargeting",
    "data broker", "people search", "lead generation", "email list",
    "real-time bidding", "rtb", "programmatic advertising", "ad targeting",
]

# Policy and legislation terms
POLICY_TERMS = [
    "privacy bill", "privacy legislation", "congress", "senate", "house",
    "rulemaking", "proposed rule", "final rule", "agency guidance", "guidance",
    "executive order", "presidential", "white house", "policy",
    "american privacy rights act", "apra", "adppa", "federal privacy",
    "preemption", "safe harbor", "adequacy decision", "standard contractual",
    "scc", "binding corporate rules", "bcr", "schrems",
]

# Corporate compliance and governance terms
COMPLIANCE_TERMS = [
    "privacy program", "data governance", "privacy officer", "cpo", "dpo",
    "data protection officer", "privacy impact assessment", "pia", "dpia",
    "records of processing", "privacy audit", "privacy assessment",
    "vendor management", "third-party risk", "data sharing agreement",
    "data processing agreement", "dpa agreement",
]

# Combine all terms for general relevance checking
ALL_PRIVACY_AI_TERMS = (
    PRIVACY_LAW_TERMS
    + AI_GOVERNANCE_TERMS
    + ENFORCEMENT_TERMS
    + BREACH_TERMS
    + ADTECH_TERMS
    + POLICY_TERMS
    + COMPLIANCE_TERMS
)


def fetch_feed(url):
    """Fetch RSS feed with proper SSL handling."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        )
        response = urllib.request.urlopen(req, context=ssl_context, timeout=10)
        return feedparser.parse(response.read())
    except Exception as e:
        print(f"    Error fetching: {e}")
        return None


def contains_terms(text, terms):
    """Return True if text contains any of the provided terms (case-insensitive)."""
    text_lower = text.lower()
    return any(term in text_lower for term in terms)


def is_relevant(entry, source_name):
    """
    Relevance filter: article must cover privacy or AI governance.
    Strategy:
    - Privacy/AI-focused sources (IAPP, CPO, FPF, EPIC, EFF, Lawfare, FTC):
      any mention of a core term qualifies
    - Tech press (TechCrunch, Wired, Ars, The Markup): same, broad coverage
    - Wire services (Reuters): needs a clear privacy/AI governance term
    """
    title = entry.get("title", "")
    summary = entry.get("summary", "")
    text = f"{title} {summary}"

    has_relevant = contains_terms(text, ALL_PRIVACY_AI_TERMS)

    # Privacy/AI-dedicated sources — trust them, just check relevance
    dedicated_sources = {
        "iapp", "cpo magazine", "future of privacy forum", "privacy international",
        "epic", "eff", "ftc", "lawfare", "the markup", "krebs", "brookings",
    }
    if any(ds in source_name.lower() for ds in dedicated_sources):
        return has_relevant

    # Tech press: require clear privacy or AI term
    return has_relevant


def parse_date(entry):
    """Parse the published date from a feed entry."""
    for attr in ["published_parsed", "updated_parsed"]:
        if hasattr(entry, attr) and getattr(entry, attr):
            try:
                return datetime(*getattr(entry, attr)[:6])
            except Exception:
                pass
    return None


def is_recent(entry, hours=48):
    """Check if article is within the last N hours."""
    pub_date = parse_date(entry)
    if not pub_date:
        return True  # include if date unknown
    cutoff = datetime.now() - timedelta(hours=hours)
    return pub_date > cutoff


def clean_html(text):
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", str(text))
    text = html.unescape(text)
    return text.strip()


def categorize(entry):
    """Assign a thematic category to the article."""
    text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()

    # Enforcement first — high signal
    if any(t in text for t in [
        "fine", "penalty", "settlement", "consent decree", "enforcement action",
        "class action", "lawsuit", "sued", "litigation", "complaint filed",
        "violation", "gdpr fine", "ftc action", "edpb decision",
    ]):
        return "Enforcement & Fines"

    # AI governance
    if any(t in text for t in [
        "eu ai act", "artificial intelligence act", "ai regulation", "ai governance",
        "nist ai", "algorithmic accountability", "ai audit", "conformity assessment",
        "high-risk ai", "ai liability", "ai policy", "ai bill", "ai oversight",
        "responsible ai", "trustworthy ai", "ai ethics", "explainable ai",
    ]):
        return "AI Governance & Regulation"

    # EU & global privacy
    if any(t in text for t in [
        "gdpr", "edpb", "ico", "cnil", "adequacy", "standard contractual",
        "schrems", "european data protection", "eu privacy", "uk gdpr",
        "binding corporate rules", "data transfer", "supervisory authority",
    ]):
        return "EU & Global Privacy"

    # Data breaches
    if any(t in text for t in [
        "data breach", "breach notification", "ransomware", "cyberattack",
        "data leak", "exposed records", "unauthorized access", "security incident",
    ]):
        return "Data Breaches & Security"

    # Adtech
    if any(t in text for t in [
        "adtech", "cookie", "tracking pixel", "behavioral advertising",
        "data broker", "targeted advertising", "real-time bidding", "rtb",
        "consent management", "fingerprinting",
    ]):
        return "Adtech & Consumer Privacy"

    # US privacy law
    if any(t in text for t in [
        "ccpa", "cpra", "hipaa", "glba", "coppa", "bipa", "ftc",
        "state privacy law", "american privacy", "federal privacy", "apra",
        "virginia", "colorado privacy", "connecticut", "utah privacy",
        "texas privacy", "attorney general",
    ]):
        return "US Privacy Law"

    # Policy & legislation
    if any(t in text for t in [
        "legislation", "bill", "congress", "senate", "rulemaking", "proposed rule",
        "final rule", "guidance", "executive order", "white house", "policy",
    ]):
        return "Policy & Legislation"

    # Corporate practice
    if any(t in text for t in [
        "privacy officer", "cpo", "dpo", "privacy program", "data governance",
        "privacy audit", "dpia", "pia", "vendor", "third-party risk",
        "data processing agreement", "compliance program",
    ]):
        return "Corporate Practice & Compliance"

    return "General Privacy & AI"


def fetch_all_feeds():
    """Fetch all RSS feeds and filter for relevant privacy/AI governance articles."""
    print("=" * 60)
    print("Privacy & AI Governance Daily News Search")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Searching RSS feeds for privacy and AI governance articles...\n")

    all_articles = {}

    for feed_url, source_name in RSS_FEEDS:
        print(f"Fetching: {source_name}...")
        feed = fetch_feed(feed_url)

        if not feed or not feed.entries:
            print(f"    No entries found")
            continue

        print(f"    {len(feed.entries)} entries in feed")
        count = 0

        for entry in feed.entries:
            if is_recent(entry) and is_relevant(entry, source_name):
                title = clean_html(entry.get("title", "No title"))
                if title and title not in all_articles:
                    all_articles[title] = {
                        "title": title,
                        "link": entry.get("link", ""),
                        "source": source_name,
                        "published": parse_date(entry),
                        "summary": clean_html(entry.get("summary", ""))[:500],
                        "category": categorize(entry),
                    }
                    count += 1

        if count > 0:
            print(f"    Found {count} relevant articles")

    # Sort by date (newest first)
    articles = sorted(
        all_articles.values(),
        key=lambda x: x["published"] if x["published"] else datetime.min,
        reverse=True,
    )

    return articles


def group_by_category(articles):
    """Group articles by thematic category."""
    groups = {}
    for article in articles:
        cat = article["category"]
        if cat not in groups:
            groups[cat] = []
        groups[cat].append(article)
    return groups


# Category display order (aligned with IAPP credential domains)
CATEGORY_ORDER = [
    "Enforcement & Fines",
    "US Privacy Law",
    "EU & Global Privacy",
    "AI Governance & Regulation",
    "Data Breaches & Security",
    "Adtech & Consumer Privacy",
    "Policy & Legislation",
    "Corporate Practice & Compliance",
    "General Privacy & AI",
]


def save_results(articles):
    """Save results to a markdown file in privacy_ai_results/."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    groups = group_by_category(articles)

    with open(filepath, "w") as f:
        f.write(f"# Privacy & AI Governance News — {today}\n\n")
        f.write(f"**Sources scanned:** {len(RSS_FEEDS)} RSS feeds\n")
        f.write(f"**Articles found:** {len(articles)}\n")
        f.write(f"**Time window:** Last 48 hours\n\n")
        f.write("---\n\n")

        if not articles:
            f.write("No relevant privacy or AI governance articles found in this period.\n")
        else:
            for cat in CATEGORY_ORDER:
                if cat not in groups:
                    continue
                cat_articles = groups[cat]
                f.write(f"## {cat} ({len(cat_articles)})\n\n")
                for i, article in enumerate(cat_articles, 1):
                    f.write(f"### {i}. {article['title']}\n\n")
                    f.write(f"**Source:** {article['source']}  \n")
                    if article["published"]:
                        f.write(
                            f"**Published:** {article['published'].strftime('%Y-%m-%d %H:%M')}  \n"
                        )
                    f.write(f"**Link:** {article['link']}\n\n")
                    if article["summary"]:
                        f.write(f"{article['summary']}...\n\n")
                    f.write("---\n\n")

        # Footer: reference links
        f.write("\n## Reference Links\n\n")
        f.write("| Resource | URL |\n")
        f.write("|---|---|\n")
        f.write("| IAPP News | https://iapp.org/news/ |\n")
        f.write("| FTC Privacy & Data Security | https://www.ftc.gov/tips-advice/business-center/privacy-and-security |\n")
        f.write("| EDPB News | https://edpb.europa.eu/news/news_en |\n")
        f.write("| NIST AI RMF | https://www.nist.gov/artificial-intelligence |\n")
        f.write("| EU AI Act Text | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689 |\n")
        f.write("| State Privacy Law Tracker | https://iapp.org/resources/article/us-state-privacy-legislation-tracker/ |\n")
        f.write("| EPIC News | https://epic.org/news/ |\n")

    return filepath


def main():
    articles = fetch_all_feeds()

    print(f"\nFound {len(articles)} relevant articles.\n")

    filepath = save_results(articles)

    if articles:
        print("Top articles:")
        for i, article in enumerate(articles[:12], 1):
            title_short = (
                article["title"][:60] + "..."
                if len(article["title"]) > 60
                else article["title"]
            )
            print(f"  {i}. [{article['category']}] {title_short}")
            print(f"     Source: {article['source']}")

    print(f"\nResults saved to: {filepath}")
    return filepath


if __name__ == "__main__":
    main()
