import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.team_flags import TEAM_FLAG_FILES, flag_url_for_team


def ranking_team_names():
    with (ROOT / "ranking_final.csv").open(newline="", encoding="utf-8") as handle:
        return [row["name"] for row in csv.DictReader(handle)]


def test_every_ranked_team_has_a_named_flag_mapping():
    missing = [team for team in ranking_team_names() if team not in TEAM_FLAG_FILES]

    assert missing == []


def test_flag_lookup_does_not_depend_on_ranking_order():
    expected = {
        "Spain": "Flag_of_Spain.svg",
        "England": "Flag_of_England.svg",
        "South Korea": "Flag_of_South_Korea.svg",
        "Argentina": "Flag_of_Argentina.svg",
        "Norway": "Flag_of_Norway.svg",
    }

    for team in reversed(ranking_team_names()):
        if team in expected:
            assert expected[team] in flag_url_for_team(team)


def test_percent_encoded_asset_is_not_double_encoded():
    url = flag_url_for_team("Curacao")

    assert "Cura%C3%A7ao" in url
    assert "%25C3%25A7" not in url
