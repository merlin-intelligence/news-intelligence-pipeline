from newsintel.text import classify_text, compile_entities, extract_article, html_to_text, strip_html, summarize, tag_entities

PAGE = """
<html><body>
<nav><p>Home | World | Business | Sign in to read the rest of this website menu</p></nav>
<article>
  <h1>Big headline about the topic</h1>
  <p>The first paragraph of the article is long enough to be kept by the extractor.</p>
  <p>Short.</p>
  <p>The second paragraph of the article is also long enough to be kept as prose.</p>
  <p>The second paragraph of the article is also long enough to be kept as prose.</p>
</article>
<footer><p>Copyright notice that is long enough but sits in the footer element.</p></footer>
</body></html>
"""


def test_html_to_text_keeps_article_body_only():
    text = html_to_text(PAGE)
    assert text.splitlines() == [
        "Big headline about the topic",
        "The first paragraph of the article is long enough to be kept by the extractor.",
        "The second paragraph of the article is also long enough to be kept as prose.",
    ]


def test_html_to_text_without_article_tag():
    html = "<html><body><div><p>" + "Plain page paragraph with enough characters. " * 2 + "</p></div></body></html>"
    assert html_to_text(html).startswith("Plain page paragraph")


def test_classify_text():
    assert classify_text("Please enable cookies " + "x" * 500, 250) == "blocked"
    assert classify_text("short", 250) == "too_short"
    assert classify_text("y" * 300, 250) == "ok"


def test_summarize_skips_boilerplate_and_falls_back():
    text = "We value your privacy and use cookies. The council approved the new budget for public transport. It takes effect in May next year for everyone."
    assert summarize(text).startswith("The council approved")
    assert summarize("", "A description used when no text was extracted.") == "A description used when no text was extracted."


def test_entities():
    compiled = compile_entities({"France": [r"\bfrance\b", r"\bparis\b"], "Spain": [r"\bspain\b"]})
    assert tag_entities("Talks in PARIS today", compiled) == "France"


def test_strip_html():
    assert strip_html("<b>Bold</b>  text") == "Bold text"


def test_summarize_ignores_headings_and_license_notices():
    text = "Big Headline Without Period\nRepublish this article under a Creative Commons licence today.\nThe ministry published the final text of the regulation on Monday morning."
    assert summarize(text) == "The ministry published the final text of the regulation on Monday morning."


ARTICLE_PAGE = """<html><head>
<title>Council approves bike lanes</title>
<meta property="article:published_time" content="2026-10-05T08:30:00Z">
</head><body>
<nav><a href="/">Home</a> <a href="/news">News</a></nav>
<div class="cookie-banner"><p>We use cookies to improve your experience. Accept all cookies to continue browsing.</p></div>
<article>
<h1>Council approves bike lanes</h1>
<p>The city council approved a network of protected bike lanes on Monday after a two-year consultation with residents.</p>
<p>Construction of the first twelve kilometres will start in spring, financed by the regional transport budget and a state grant.</p>
<p>Shop owners on the main avenue had asked for more delivery bays, which the final plan now includes on every block.</p>
</article>
<footer><p>Copyright 2026 The City Paper. All rights reserved. Terms of use and privacy policy apply to this website.</p></footer>
</body></html>"""


def test_extract_article_returns_body_and_page_date():
    text, date = extract_article(ARTICLE_PAGE, "https://citypaper.example/bike-lanes")
    assert date == "2026-10-05"
    assert "protected bike lanes" in text and "delivery bays" in text
    assert "cookies" not in text.lower() and "all rights reserved" not in text.lower()


def test_extract_article_falls_back_on_simple_pages():
    html = "<html><body><p>" + "Short plain page with one paragraph of real prose in it. " * 3 + "</p></body></html>"
    text, date = extract_article(html)
    assert text.startswith("Short plain page") and date == ""


def test_security_wall_is_blocked():
    wall = "This website is using a security service to protect itself from online attacks. " * 5
    assert classify_text(wall, 100) == "blocked"
