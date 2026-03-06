"""
HTML-to-text extraction with topic-focused filtering.

Uses heading-based sectioning to extract only content relevant
to the page's main health topic, filtering out navigation,
sidebars, related articles, and other noise.
"""

from bs4 import BeautifulSoup, Tag
import re


# Noise elements to remove entirely before extraction
NOISE_SELECTORS = [
    "script", "style", "nav", "footer", "header", "aside", "iframe",
    "noscript", "svg", "form",
]

# CSS class/id patterns that indicate noise (case-insensitive)
NOISE_ATTR_PATTERNS = [
    r"breadcrumb", r"sidebar", r"side-bar", r"side_bar",
    r"related[-_]?(article|post|content|link|story|topic)",
    r"share[-_]?(button|bar|widget|link|section|this)",
    r"social[-_]?(media|link|share|button|icon)",
    r"cookie[-_]?(banner|notice|consent|bar|popup)",
    r"newsletter", r"subscribe", r"signup", r"sign-up",
    r"advertisement", r"ad[-_]?(banner|container|slot|wrapper)",
    r"comment[-_]?(section|form|list|area)",
    r"popup", r"modal", r"overlay",
    r"footer[-_]?(nav|link|menu|widget)",
    r"nav[-_]?(bar|menu|link|item)",
    r"menu[-_]?(item|list|toggle)",
    r"search[-_]?(bar|box|form|widget)",
    r"skip[-_]?to[-_]?content",
    r"back[-_]?to[-_]?top",
    r"print[-_]?(button|link|version)",
    r"feedback[-_]?(form|button|section)",
    r"rating", r"review[-_]?(section|form)",
    r"author[-_]?(bio|info|card|box)",
    r"tag[-_]?(cloud|list|widget)",
    r"pagination",
]

# Heading text patterns that indicate non-content sections
NOISE_HEADING_PATTERNS = [
    r"^related\b", r"^see also\b", r"^you (may|might) (also )?(like|enjoy)\b",
    r"^more (on|about|from)\b", r"^share\b", r"^comment",
    r"^about the author\b", r"^about us\b", r"^disclaimer\b",
    r"^cookie\b", r"^subscribe\b", r"^newsletter\b", r"^follow us\b",
    r"^advertisement\b", r"^sponsored\b", r"^promoted\b",
    r"^(also|previously) (on|at|from)\b", r"^popular\b",
    r"^trending\b", r"^latest\b", r"^recent (post|article|news)\b",
    r"^(don.t )?miss\b", r"^read (more|next)\b",
    r"^feedback\b", r"^rate this\b", r"^was this helpful\b",
    r"^references?\b", r"^sources?\b", r"^citation",
    r"^external links?\b", r"^additional resources?\b",
]

NOISE_HEADING_COMPILED = [re.compile(p, re.IGNORECASE) for p in NOISE_HEADING_PATTERNS]
NOISE_ATTR_COMPILED = [re.compile(p, re.IGNORECASE) for p in NOISE_ATTR_PATTERNS]


def _element_matches_noise_attrs(tag: Tag) -> bool:
    """Check if a tag's class or id matches noise patterns."""
    attrs_to_check = []
    if tag.get("class"):
        attrs_to_check.extend(tag["class"] if isinstance(tag["class"], list) else [tag["class"]])
    if tag.get("id"):
        attrs_to_check.append(tag["id"])
    if tag.get("role"):
        attrs_to_check.append(tag["role"])

    attr_text = " ".join(str(a) for a in attrs_to_check)
    if not attr_text:
        return False

    for pattern in NOISE_ATTR_COMPILED:
        if pattern.search(attr_text):
            return True
    return False


def _is_noise_heading(heading_text: str) -> bool:
    """Check if a heading text matches noise patterns."""
    text = heading_text.strip()
    for pattern in NOISE_HEADING_COMPILED:
        if pattern.search(text):
            return True
    return False


def _extract_main_container(soup: BeautifulSoup) -> Tag:
    """Find the main content container in the page."""
    # Priority order for main content
    candidates = [
        soup.find("article"),
        soup.find("main"),
        soup.find(attrs={"role": "main"}),
        soup.find("div", class_=re.compile(r"(article|content|entry|post)[-_]?(body|text|content|main)", re.I)),
        soup.find("div", class_=re.compile(r"^(content|article|body|main|entry)$", re.I)),
        soup.find("div", id=re.compile(r"(content|article|body|main|entry)", re.I)),
        soup.body,
        soup,
    ]
    for c in candidates:
        if c:
            return c
    return soup


def _remove_noise_elements(container: Tag) -> None:
    """Remove noise elements from the container in-place."""
    # Remove standard noise tags
    for tag_name in NOISE_SELECTORS:
        for tag in container.find_all(tag_name):
            tag.decompose()

    # Remove elements with noise class/id patterns
    for tag in container.find_all(True):
        if _element_matches_noise_attrs(tag):
            tag.decompose()

    # Remove elements with noise ARIA roles
    for role in ["banner", "navigation", "complementary", "contentinfo"]:
        for tag in container.find_all(attrs={"role": role}):
            tag.decompose()


def _extract_sections(container: Tag) -> list[dict]:
    """
    Parse the container into sections defined by headings.
    Returns a list of dicts: {"heading": str, "level": int, "paragraphs": [str]}
    """
    sections = []
    current_section = {"heading": "", "level": 0, "paragraphs": []}

    for child in container.descendants:
        if isinstance(child, Tag) and child.name in ("h1", "h2", "h3", "h4"):
            # Start a new section
            if current_section["paragraphs"] or current_section["heading"]:
                sections.append(current_section)
            heading_text = child.get_text(strip=True)
            level = int(child.name[1])
            current_section = {"heading": heading_text, "level": level, "paragraphs": []}

        elif isinstance(child, Tag) and child.name in ("p", "li"):
            # Only include if this is a direct content element (not nested in another p/li)
            parent_tags = [p.name for p in child.parents if isinstance(p, Tag)]
            if child.name == "li" and "li" in parent_tags[:3]:
                continue  # Skip deeply nested list items

            text = child.get_text(strip=True)
            if text and len(text) >= 30:
                current_section["paragraphs"].append(text)

    # Don't forget the last section
    if current_section["paragraphs"]:
        sections.append(current_section)

    return sections


def _filter_relevant_sections(sections: list[dict]) -> list[dict]:
    """
    Filter out sections with noise headings.
    Keeps all sections with relevant or empty (intro) headings.
    """
    filtered = []
    for section in sections:
        heading = section["heading"]
        # Always keep sections without headings (intro content)
        if not heading:
            filtered.append(section)
            continue
        # Skip sections with noise headings
        if _is_noise_heading(heading):
            continue
        filtered.append(section)
    return filtered


def extract_text_from_html(html: str) -> tuple[str, str]:
    """
    Extract title and topic-focused text content from HTML.
    Returns (title, text) tuple.

    Uses heading-based sectioning to keep only relevant content
    and filters out navigation, sidebars, and promotional noise.
    """
    if not html:
        return ("", "")

    soup = BeautifulSoup(html, "lxml")

    # Extract title first (before removing elements)
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # Try h1 as fallback or better title
    h1 = soup.find("h1")
    if h1:
        h1_text = h1.get_text(strip=True)
        if h1_text:
            # Prefer h1 if it's more specific than the <title>
            if not title or len(h1_text) < len(title):
                title = h1_text

    # Find main content container
    container = _extract_main_container(soup)

    # Remove noise elements
    _remove_noise_elements(container)

    # Extract sections
    sections = _extract_sections(container)

    # Filter to relevant sections only
    relevant = _filter_relevant_sections(sections)

    # Build output text
    output_parts = []
    for section in relevant:
        if section["heading"]:
            output_parts.append(f"\n{section['heading']}\n")
        for para in section["paragraphs"]:
            output_parts.append(para)

    text = "\n".join(output_parts).strip()

    # Remove very short extractions (likely nav-only pages)
    if len(text) < 50:
        text = ""

    return (title, text)
