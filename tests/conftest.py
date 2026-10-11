import pandas as pd
import pytest

from newsintel.config import config_from_dict
from newsintel.data import article_id

TOPICS = {
    "rail": "The new high-speed rail line opened, trains run between the two cities and ticket prices for rail passengers fell.",
    "solar": "Solar panel installations reached a record as photovoltaic capacity grew and solar farms connected to the grid.",
    "water": "Drought forced water restrictions; reservoirs are low and the water utility asked households to cut consumption.",
}

FILLER = (
    "mayor council budget contract delay strike union engineers survey households tariff region north south "
    "investors bank loan citizens report audit minister village farmers schools hospital museum festival weather"
).split()


def make_articles(n_per_topic=4, duplicate=True):
    rows = []
    for topic, body in TOPICS.items():
        for k in range(n_per_topic):
            url = f"https://example-{topic}.com/story-{k}"
            rows.append(
                {
                    "article_id": article_id(url),
                    "channel": "google_news",
                    "seed": topic,
                    "title": f"{topic.title()} story {k}",
                    "description": f"News about {topic} number {k}.",
                    "url": url,
                    "resolved_url": url,
                    "source": f"Example {topic}",
                    "domain": f"example-{topic}.com",
                    "published_at": f"2026-10-0{k + 1}",
                    "harvested_at": "2026-10-10 10:00:00",
                    # shared topic sentence + words specific to this article
                    "text": body + " " + " ".join(FILLER[(7 * k + j) % len(FILLER)] + topic[:2] + str(k) for j in range(20)) + ".",
                    "extraction_status": "ok",
                    "extraction_error": "",
                }
            )
    if duplicate:
        dup = dict(rows[0], url="https://mirror.com/copy", resolved_url="https://mirror.com/copy", title="Rail story copy")
        dup["article_id"] = article_id(dup["url"])
        rows.append(dup)
    return pd.DataFrame(rows)


@pytest.fixture
def articles():
    return make_articles()


@pytest.fixture
def cfg(tmp_path):
    return config_from_dict(
        {
            "project": {"name": "test", "title": "Infrastructure watch", "description": "rail trains solar water infrastructure"},
            "seeds": {"queries": ["rail", "solar", "water"]},
            "categories": [
                {"id": "rail", "name": "Rail", "description": "rail trains passengers tickets line"},
                {"id": "solar", "name": "Solar", "description": "solar panels photovoltaic grid capacity"},
                {"id": "water", "name": "Water", "description": "water drought reservoirs utility restrictions"},
            ],
            "entities": {"Grid": [r"\bgrid\b"]},
            "selection": {"top_n": 4, "next_n": 5},
            "output_dir": str(tmp_path / "runs"),
        },
        base_dir=tmp_path,
    )
