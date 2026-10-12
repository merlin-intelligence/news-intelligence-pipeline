from newsintel.data import article_id, domain_of, load_seeds, normalize_url


def test_normalize_url_drops_tracking_and_fragment():
    a = normalize_url("https://Example.com/a/?utm_source=x&id=3#top")
    assert a == "https://example.com/a?id=3"
    assert article_id("https://example.com/a?utm_medium=y&id=3") == article_id("https://EXAMPLE.com/a/?id=3")


def test_domain_strips_www():
    assert domain_of("https://www.reuters.com/x") == "reuters.com"


def test_load_seeds_csv_autodetects_column_and_dedupes(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text("id,Keyword\n1,Solar power\n2,solar power\n3,\n4,Wind\n", encoding="utf-8")
    assert load_seeds(f) == ["Solar power", "Wind"]


def test_load_seeds_txt_inline_and_limit(tmp_path):
    f = tmp_path / "s.txt"
    f.write_text("# comment\na\nb\n", encoding="utf-8")
    assert load_seeds(f, inline=["z"], limit=2) == ["z", "a"]
