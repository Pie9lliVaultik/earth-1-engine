"""Measured-reaction case library — history's natural experiments.

Each case: a documented event (headlines perception can read), the
opinion it measurably moved, and the published before/after values.
These are the ground truth for fitting and validating the TEMPORAL
response operator — the law converting force impulses into opinion
change, which run #6/#7 proved is distinct from cross-sectional
calibration (COVID: fear UP moved trust UP; cross-sectionally fearful
societies trust LESS).

Values compiled from published polling; verify against named sources
before publication. Fitting discipline: leave-one-CASE-out — a case's
own data never touches the parameters that predict it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from earth1.news_perception import NewsItem


@dataclass
class ReactionCase:
    id: str
    description: str
    source: str
    question_text: str        # what the poll measured
    headlines: List[NewsItem] # what perception reads
    pre: Dict[str, float]     # country -> measured pre value
    post: Dict[str, float]    # country -> measured post value
    window_days: float        # event -> post-measurement gap


REACTION_CASES: List[ReactionCase] = [
    ReactionCase(
        id="covid_rally_2020",
        description="COVID onset: EU trust in national government rises",
        source="Standard Eurobarometer 92/93 toplines",
        question_text="Do you tend to trust your national government?",
        headlines=[
            NewsItem("Italy imposes nationwide lockdown as coronavirus deaths surge", "IT", "2020-03-09"),
            NewsItem("Spain declares state of emergency over coronavirus outbreak", "ES", "2020-03-14"),
            NewsItem("Germany closes borders with five countries to slow coronavirus", "DE", "2020-03-16"),
            NewsItem("France orders nationwide lockdown; Macron says 'we are at war'", "FR", "2020-03-17"),
            NewsItem("Netherlands announces 'intelligent lockdown' as cases climb", "NL", "2020-03-23"),
            NewsItem("Poland closes borders and schools in coronavirus clampdown", "PL", "2020-03-15"),
        ],
        pre={"IT": 0.22, "ES": 0.18, "DE": 0.45, "FR": 0.25, "NL": 0.61, "PL": 0.37},
        post={"IT": 0.31, "ES": 0.20, "DE": 0.60, "FR": 0.30, "NL": 0.70, "PL": 0.31},
        window_days=90.0,
    ),
    ReactionCase(
        id="nato_nordics_2022",
        description="Russian invasion of Ukraine: Nordic NATO support explodes",
        source="Yle/Taloustutkimus (FI), Demoskop/Novus (SE)",
        question_text="Should your country join NATO?",
        headlines=[
            NewsItem("Russia launches full-scale invasion of Ukraine", "FI", "2022-02-24"),
            NewsItem("Russian forces shell Kyiv as war reaches Finland's doorstep debate", "FI", "2022-02-25"),
            NewsItem("Russia invades Ukraine; Sweden weighs security order collapse", "SE", "2022-02-24"),
        ],
        pre={"FI": 0.24, "SE": 0.37},
        post={"FI": 0.62, "SE": 0.51},
        window_days=90.0,
    ),
    ReactionCase(
        id="fukushima_de_2011",
        description="Fukushima meltdown: German support for rapid nuclear exit surges",
        source="Forsa / Infratest dimap (ARD DeutschlandTrend), 2010-2011",
        question_text="Should Germany exit nuclear power quickly?",
        headlines=[
            NewsItem("Explosions rock Fukushima nuclear plant after tsunami knocks out cooling", "DE", "2011-03-12"),
            NewsItem("Radiation fears grow as Fukushima crisis escalates to highest level", "DE", "2011-03-15"),
        ],
        pre={"DE": 0.54},
        post={"DE": 0.80},
        window_days=60.0,
    ),
    ReactionCase(
        id="migration_de_2015",
        description="Migration crisis winter: German confidence in coping collapses",
        source="ARD DeutschlandTrend (Infratest dimap) Sep 2015 vs Jan 2016",
        question_text="Can Germany cope with the number of refugees?",
        headlines=[
            NewsItem("Hundreds of thousands of refugees arrive as Germany opens borders", "DE", "2015-09-05"),
            NewsItem("Cologne New Year's Eve assaults ignite firestorm over migration policy", "DE", "2016-01-05"),
        ],
        pre={"DE": 0.59},
        post={"DE": 0.37},
        window_days=120.0,
    ),
    ReactionCase(
        id="us_rally_2001",
        description="9/11: US trust in federal government doubles",
        source="Gallup/Pew trust-in-government series, mid-2001 vs Oct 2001",
        question_text="Do you trust the federal government to do what is right?",
        headlines=[
            NewsItem("Terrorists crash airliners into World Trade Center and Pentagon", "US", "2001-09-11"),
        ],
        pre={"US": 0.30},
        post={"US": 0.60},
        window_days=45.0,
    ),
    ReactionCase(
        id="crisis_us_2008",
        description="Financial crisis: US economic optimism collapses",
        source="Pew economic conditions ratings, early 2008 vs early 2009",
        question_text="Are national economic conditions good?",
        headlines=[
            NewsItem("Lehman Brothers collapses in largest bankruptcy in US history", "US", "2008-09-15"),
            NewsItem("Stock market plunges as credit crisis deepens; bailout debated", "US", "2008-09-29"),
        ],
        pre={"US": 0.26},
        post={"US": 0.07},
        window_days=150.0,
    ),
]
