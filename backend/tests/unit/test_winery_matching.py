"""Unit tests for linking producer names to licensed wineries."""

from app.services.winery_matching import WineryMatcher, clean_establishment_name, normalize_name

WINERIES = [
    ("100", "Mission Hill Winery", "Mission Hill Vineyards Inc."),
    ("200", "JoieFarm", None),
    ("301", "Township 7 Vineyards & Winery", None),
    ("302", "Township 7 Vineyards & Winery", None),
    ("400", "Bench 1775 Winery Estate", None),
]


class TestNames:
    def test_strips_licence_suffix(self):
        assert clean_establishment_name("Mission Hill Winery (300228)") == "Mission Hill Winery"

    def test_ignores_case_spacing_and_filler_words(self):
        assert normalize_name("JOIE FARM") == normalize_name("JoieFarm")
        assert normalize_name("Mission Hill Family Estate Winery") == "missionhill"

    def test_handles_accents_and_empty_values(self):
        assert normalize_name("vinAmité Winery") == "vinamite"
        assert normalize_name(None) == ""


class TestMatching:
    def test_exact_match_links(self):
        match = WineryMatcher(WINERIES).match("MISSION HILL")
        assert (match.status, match.licence_number) == ("exact", "100")

    def test_winery_name_wins_over_a_shared_licensee(self):
        wineries = [("1", "Sandhill", "Sandhill Inc."), ("2", "Red Rooster", "Sandhill")]
        match = WineryMatcher(wineries).match("Sandhill")
        assert (match.status, match.licence_number) == ("exact", "1")

    def test_licensee_name_links_when_it_is_unique(self):
        match = WineryMatcher([("1", "Tasting Room", "Hillside Ltd.")]).match("Hillside")
        assert (match.status, match.licence_number) == ("exact", "1")

    def test_candidates_are_not_repeated(self):
        wineries = [("1", "Kalala Organic Estate Winery", "Kalala Organic Estate Winery Ltd.")]
        assert WineryMatcher(wineries).match("Kalala").candidate.count("(1)") == 1

    def test_shared_name_goes_to_review_without_a_link(self):
        match = WineryMatcher(WINERIES).match("Township 7")
        assert match.status == "review"
        assert match.licence_number is None
        assert "301" in match.candidate and "302" in match.candidate

    def test_similar_name_goes_to_review_without_a_link(self):
        match = WineryMatcher(WINERIES).match("Mission Hill Reserve")
        assert match.status == "review"
        assert match.licence_number is None

    def test_alias_links_a_brand_to_a_licence(self):
        match = WineryMatcher(WINERIES, {"Copper Moon": "100"}).match("COPPER MOON")
        assert (match.status, match.licence_number) == ("alias", "100")

    def test_alias_to_unknown_licence_is_ignored(self):
        assert WineryMatcher(WINERIES, {"Copper Moon": "999"}).match("Copper Moon").status == "unmatched"

    def test_unknown_or_missing_producer_is_unmatched(self):
        matcher = WineryMatcher(WINERIES)
        assert matcher.match("Zzyzx Ridge").status == "unmatched"
        assert matcher.match(None).status == "unmatched"
