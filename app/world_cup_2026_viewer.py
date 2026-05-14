import json
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")


SNAPSHOT_FILE = Path(__file__).resolve().parents[1] / "data" / "output" / "world_cup_2026" / "simulation_snapshot.json"

FLAG_FILES = {
    "Algeria": "File:Flag_of_Algeria.svg",
    "Argentina": "File:Flag_of_Argentina.svg",
    "Australia": "File:Flag_of_Australia.svg",
    "Austria": "File:Flag_of_Austria.svg",
    "Belgium": "File:Flag_of_Belgium.svg",
    "Bosnia and Herzegovina": "File:Flag_of_Bosnia_and_Herzegovina.svg",
    "Brazil": "File:Flag_of_Brazil.svg",
    "Canada": "File:Flag_of_Canada.svg",
    "Cape Verde Islands": "File:Flag_of_Cape_Verde.svg",
    "Colombia": "File:Flag_of_Colombia.svg",
    "Congo DR": "File:Flag_of_the_Democratic_Republic_of_the_Congo.svg",
    "Croatia": "File:Flag_of_Croatia.svg",
    "Curacao": "File:Flag_of_Cura%C3%A7ao.svg",
    "Czech Republic": "File:Flag_of_the_Czech_Republic.svg",
    "Ecuador": "File:Flag_of_Ecuador.svg",
    "Egypt": "File:Flag_of_Egypt.svg",
    "England": "File:Flag_of_England.svg",
    "France": "File:Flag_of_France.svg",
    "Germany": "File:Flag_of_Germany.svg",
    "Ghana": "File:Flag_of_Ghana.svg",
    "Haiti": "File:Flag_of_Haiti.svg",
    "Iran": "File:Flag_of_Iran.svg",
    "Iraq": "File:Flag_of_Iraq.svg",
    "Ivory Coast": "File:Flag_of_C%C3%B4te_d%27Ivoire.svg",
    "Japan": "File:Flag_of_Japan.svg",
    "Jordan": "File:Flag_of_Jordan.svg",
    "Mexico": "File:Flag_of_Mexico.svg",
    "Morocco": "File:Flag_of_Morocco.svg",
    "Netherlands": "File:Flag_of_the_Netherlands.svg",
    "New Zealand": "File:Flag_of_New_Zealand.svg",
    "Norway": "File:Flag_of_Norway.svg",
    "Panama": "File:Flag_of_Panama.svg",
    "Paraguay": "File:Flag_of_Paraguay.svg",
    "Portugal": "File:Flag_of_Portugal.svg",
    "Qatar": "File:Flag_of_Qatar.svg",
    "Saudi Arabia": "File:Flag_of_Saudi_Arabia.svg",
    "Scotland": "File:Flag_of_Scotland.svg",
    "Senegal": "File:Flag_of_Senegal.svg",
    "South Africa": "File:Flag_of_South_Africa.svg",
    "South Korea": "File:Flag_of_South_Korea.svg",
    "Spain": "File:Flag_of_Spain.svg",
    "Sweden": "File:Flag_of_Sweden.svg",
    "Switzerland": "File:Flag_of_Switzerland.svg",
    "Tunisia": "File:Flag_of_Tunisia.svg",
    "Turkey": "File:Flag_of_Turkey.svg",
    "Uruguay": "File:Flag_of_Uruguay.svg",
    "USA": "File:Flag_of_the_United_States.svg",
    "Uzbekistan": "File:Flag_of_Uzbekistan.svg",
}

FLAG_EMOJI = {
    "Algeria": "🇩🇿",
    "Argentina": "🇦🇷",
    "Australia": "🇦🇺",
    "Austria": "🇦🇹",
    "Belgium": "🇧🇪",
    "Bosnia and Herzegovina": "🇧🇦",
    "Brazil": "🇧🇷",
    "Canada": "🇨🇦",
    "Cape Verde Islands": "🇨🇻",
    "Colombia": "🇨🇴",
    "Congo DR": "🇨🇩",
    "Croatia": "🇭🇷",
    "Curacao": "🇨🇼",
    "Czech Republic": "🇨🇿",
    "Ecuador": "🇪🇨",
    "Egypt": "🇪🇬",
    "England": "[ENG]",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Ghana": "🇬🇭",
    "Haiti": "🇭🇹",
    "Iran": "🇮🇷",
    "Iraq": "🇮🇶",
    "Ivory Coast": "🇨🇮",
    "Japan": "🇯🇵",
    "Jordan": "🇯🇴",
    "Mexico": "🇲🇽",
    "Morocco": "🇲🇦",
    "Netherlands": "🇳🇱",
    "New Zealand": "🇳🇿",
    "Norway": "🇳🇴",
    "Panama": "🇵🇦",
    "Paraguay": "🇵🇾",
    "Portugal": "🇵🇹",
    "Qatar": "🇶🇦",
    "Saudi Arabia": "🇸🇦",
    "Scotland": "[SCO]",
    "Senegal": "🇸🇳",
    "South Africa": "🇿🇦",
    "South Korea": "🇰🇷",
    "Spain": "🇪🇸",
    "Sweden": "🇸🇪",
    "Switzerland": "🇨🇭",
    "Tunisia": "🇹🇳",
    "Turkey": "🇹🇷",
    "Uruguay": "🇺🇾",
    "USA": "🇺🇸",
    "Uzbekistan": "🇺🇿",
}


def load_snapshot():
    return json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))


def flag_url(team):
    filename = FLAG_FILES.get(team)
    if not filename:
        return "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
    return "https://commons.wikimedia.org/wiki/Special:FilePath/" + quote(filename, safe=":/.%") + "?width=32"


def team_html(team):
    return f'<span class="team"><img src="{flag_url(team)}" /> {team}</span>'


def team_markdown(team):
    return f"{FLAG_EMOJI.get(team, '')} {team}"


def team_display(team):
    return team


def note_display(note):
    if note == "forecast draw resolved by higher non-draw simulated win count":
        return "draw tiebreak"
    return note


def match_html(match):
    note = f'<div class="note">{match["note"]}</div>' if match.get("note") else ""
    home_adv = f'<span class="tag">home adv: {match["home_adv"]}</span>' if match.get("home_adv") else ""
    winner = match["winner"]
    return f"""
    <div class="match">
      <div class="match-label">{match.get("label", "Match")} {home_adv}</div>
      <div class="scoreline">
        <div>{team_html(match["team_a"])}</div>
        <strong>{match["score_a"]}-{match["score_b"]}</strong>
        <div>{team_html(match["team_b"])}</div>
      </div>
      <div class="winner">Winner: {winner}</div>
      {note}
    </div>
    """


def standings_df(rows):
    return pd.DataFrame(
        [
            {"#": pos, "Flag": flag_url(team), "Team": team_display(team), "Pts": points, "GD": gd, "GF": gf}
            for pos, (team, points, gd, gf) in enumerate(rows, start=1)
        ]
    )


def group_matches_df(matches):
    return pd.DataFrame(
        [
            {
                "Flag A": flag_url(match["team_a"]),
                "Team A": team_display(match["team_a"]),
                "Score": f"{match['score_a']}-{match['score_b']}",
                "Flag B": flag_url(match["team_b"]),
                "Team B": team_display(match["team_b"]),
                "Winner": team_display(match["winner"]) if match["winner"] != "draw" else "draw",
                "Home adv": match.get("home_adv", ""),
            }
            for match in matches
        ]
    )


def best_thirds_df(rows):
    return pd.DataFrame(
        [
            {"#": pos, "Flag": flag_url(team), "Team": team_display(team), "Group": group, "Pts": points, "GD": gd, "GF": gf}
            for pos, (team, group, points, gd, gf) in enumerate(rows, start=1)
        ]
    )


def knockout_df(matches):
    return pd.DataFrame(
        [
            {
                "Match": match["label"],
                "Flag A": flag_url(match["team_a"]),
                "Team A": team_display(match["team_a"]),
                "Score": f"{match['score_a']}-{match['score_b']}",
                "Flag B": flag_url(match["team_b"]),
                "Team B": team_display(match["team_b"]),
                "Winner": team_display(match["winner"]),
                "Home adv": match.get("home_adv", ""),
                "Note": note_display(match.get("note", "")),
            }
            for match in matches
        ]
    )


STANDINGS_COLUMNS = {
    "#": st.column_config.NumberColumn(width="small"),
    "Flag": st.column_config.ImageColumn(width=32),
    "Team": st.column_config.TextColumn(width="medium"),
    "Pts": st.column_config.NumberColumn(width="small"),
    "GD": st.column_config.NumberColumn(width="small"),
    "GF": st.column_config.NumberColumn(width="small"),
}

BEST_THIRDS_COLUMNS = {
    "#": st.column_config.NumberColumn(width="small"),
    "Flag": st.column_config.ImageColumn(width=32),
    "Team": st.column_config.TextColumn(width="medium"),
    "Group": st.column_config.TextColumn(width="small"),
    "Pts": st.column_config.NumberColumn(width="small"),
    "GD": st.column_config.NumberColumn(width="small"),
    "GF": st.column_config.NumberColumn(width="small"),
}

MATCH_COLUMNS = {
    "Flag A": st.column_config.ImageColumn(width=32),
    "Team A": st.column_config.TextColumn(width="medium"),
    "Score": st.column_config.TextColumn(width="small"),
    "Flag B": st.column_config.ImageColumn(width=32),
    "Team B": st.column_config.TextColumn(width="medium"),
    "Winner": st.column_config.TextColumn(width="medium"),
    "Home adv": st.column_config.TextColumn(width="small"),
}

KNOCKOUT_COLUMNS = {
    "Match": st.column_config.TextColumn(width="small"),
    "Flag A": st.column_config.ImageColumn(width=32),
    "Team A": st.column_config.TextColumn(width="medium"),
    "Score": st.column_config.TextColumn(width="small"),
    "Flag B": st.column_config.ImageColumn(width=32),
    "Team B": st.column_config.TextColumn(width="medium"),
    "Winner": st.column_config.TextColumn(width="medium"),
    "Home adv": st.column_config.TextColumn(width="small"),
    "Note": st.column_config.TextColumn(width="medium"),
}


def render_styles():
    st.markdown(
        """
        <style>
        .hero {border: 1px solid #d9dee7; border-radius: 8px; padding: 18px; margin-bottom: 16px;}
        .hero h2 {margin: 0 0 8px 0;}
        .team {display: inline-flex; align-items: center; gap: 7px; white-space: nowrap;}
        .team img {width: 24px; height: 16px; object-fit: cover; border: 1px solid #d0d4dc;}
        .match {border: 1px solid #d9dee7; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px;}
        .match-label {font-size: 12px; color: #5b6472; margin-bottom: 8px;}
        .scoreline {display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 10px;}
        .scoreline div:last-child {text-align: right;}
        .winner {font-size: 13px; margin-top: 7px;}
        .note {font-size: 12px; color: #7a4b00; margin-top: 5px;}
        .tag {background: #eef5ff; border: 1px solid #cfe0f5; border-radius: 999px; padding: 2px 7px; margin-left: 6px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


snapshot = load_snapshot()
render_styles()
final_match = next(match for match in snapshot["knockout_matches"] if match["round"] == "Final")
third_place_match = next(match for match in snapshot["knockout_matches"] if match["round"] == "Third place")
runner_up = final_match["team_b"] if final_match["winner"] == final_match["team_a"] else final_match["team_a"]
fourth_place = third_place_match["team_b"] if third_place_match["winner"] == third_place_match["team_a"] else third_place_match["team_a"]

st.title("World Cup 2026 Simulation")
st.caption("Static visualization of a saved tournament simulation snapshot.")

st.markdown(
    f"""
    <div class="hero">
      <h2>{team_html(snapshot["champion"])} Champion: {snapshot["champion"]}</h2>
      <div>Runner-up: {team_html(runner_up)}</div>
      <div>Third place: {team_html(snapshot["third_place"])}</div>
      <div>Fourth place: {team_html(fourth_place)}</div>
      <div>Simulations per match: {snapshot["simulations_per_match"]}</div>
      <div>Home advantage: {snapshot["home_advantage"]} ({snapshot["home_advantage_multiplier"]})</div>
      <div>{snapshot["knockout_tiebreak_note"]}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

groups_tab, thirds_tab, knockout_tab = st.tabs(["Groups", "Best Thirds", "Knockout"])

with groups_tab:
    group_names = list(snapshot["group_tables"].keys())
    for group in group_names:
        with st.expander(f"Group {group}", expanded=group in ("A", "B")):
            st.markdown("**Standings**")
            st.dataframe(
                standings_df(snapshot["group_tables"][group]),
                column_config=STANDINGS_COLUMNS,
                hide_index=True,
                use_container_width=True,
            )
            st.markdown("**Matches**")
            matches = [m for m in snapshot["group_matches"] if m["group"] == group]
            st.dataframe(
                group_matches_df(matches),
                column_config=MATCH_COLUMNS,
                hide_index=True,
                use_container_width=True,
            )

with thirds_tab:
    st.subheader("Best third-place teams advancing")
    st.dataframe(
        best_thirds_df(snapshot["best_thirds"]),
        column_config=BEST_THIRDS_COLUMNS,
        hide_index=True,
        use_container_width=True,
    )

with knockout_tab:
    rounds = ["Round of 32", "Round of 16", "Quarter-finals", "Semi-finals", "Third place", "Final"]
    for round_name in rounds:
        st.subheader(round_name)
        matches = [m for m in snapshot["knockout_matches"] if m["round"] == round_name]
        st.dataframe(
            knockout_df(matches),
            column_config=KNOCKOUT_COLUMNS,
            hide_index=True,
            use_container_width=True,
        )
