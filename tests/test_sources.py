from newsintel.harvest import google_news
from newsintel.resolve import pick_result

RSS = b"""<?xml version="1.0"?><rss><channel>
<item><title>Big news - The Daily</title><link>https://news.google.com/rss/articles/abc</link>
<pubDate>Mon, 05 Oct 2026 08:00:00 GMT</pubDate><description>&lt;a href="x"&gt;Big news&lt;/a&gt;</description>
<source url="https://www.daily.example">The Daily</source></item>
</channel></rss>"""


class FakeSession:
    def get(self, url, **kwargs):
        self.url = url

        class R:
            content = RSS

            def raise_for_status(self):
                pass

        return R()


def test_google_news_rss_parsing():
    s = FakeSession()
    [rec] = google_news.search("solar power", days=7, session=s)
    assert "solar%20power%20when%3A7d" in s.url
    assert rec == {
        "title": "Big news",
        "description": "Big news",
        "url": "https://news.google.com/rss/articles/abc",
        "source": "The Daily",
        "source_url": "https://www.daily.example",
        "published_at": "2026-10-05",
    }


def test_pick_result_prefers_publisher_domain():
    results = [{"url": "https://aggregator.com/x"}, {"url": "https://www.daily.example/story"}]
    assert pick_result(results, "daily.example") == "https://www.daily.example/story"
    assert pick_result(results, "other.com") == "https://aggregator.com/x"
    assert pick_result([], "x") == ""
