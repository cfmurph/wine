"""Link wine producer names to licensed wineries.

Only exact normalized matches and hand-confirmed aliases create a link. Anything
looser goes to a review file, because a wrong link would put one winery's wines
on another winery's profile.
"""

import difflib
import re
import unicodedata
from dataclasses import dataclass

_FILLER_WORDS = re.compile(
    r"\b(winery|wines?|vineyards?|estates?|cellars?|ltd|limited|inc|corp|the|and|family)\b"
)
_MIN_CANDIDATE_LENGTH = 4
_CLOSE_MATCH_CUTOFF = 0.85


def clean_establishment_name(name: str) -> str:
    """Drop the licence number suffix, e.g. 'Mission Hill Winery (300228)'."""
    return re.sub(r"\s*\(\d+\)\s*$", "", name or "").strip()


def normalize_name(name: str | None) -> str:
    """Reduce a name to a comparable key: 'JoieFarm' and 'JOIE FARM' both become 'joiefarm'."""
    ascii_name = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    lowered = re.sub(r"[^a-z0-9 ]", "", ascii_name.lower().replace("&", " and "))
    return _FILLER_WORDS.sub("", lowered).replace(" ", "")


@dataclass
class WineryMatch:
    status: str  # exact | alias | review | unmatched
    licence_number: str | None = None
    candidate: str | None = None
    reason: str | None = None


class WineryMatcher:
    def __init__(self, wineries: list[tuple[str, str, str | None]], aliases: dict[str, str] | None = None):
        """wineries: (licence_number, name, licensee). aliases: producer name -> licence_number."""
        self._by_name: dict[str, set[str]] = {}
        self._by_licensee: dict[str, set[str]] = {}
        self._names: dict[str, str] = {}
        for licence_number, name, licensee in wineries:
            self._names[licence_number] = name
            self._by_name.setdefault(normalize_name(name), set()).add(licence_number)
            self._by_licensee.setdefault(normalize_name(licensee), set()).add(licence_number)
        self._by_name.pop("", None)
        self._by_licensee.pop("", None)
        self._aliases = {normalize_name(k): v for k, v in (aliases or {}).items()}

    def _describe(self, licences) -> str:
        return "; ".join(f"{self._names[n]} ({n})" for n in sorted(licences))

    def match(self, producer: str | None) -> WineryMatch:
        key = normalize_name(producer)
        if not key:
            return WineryMatch("unmatched", reason="no producer name")

        if key in self._aliases and self._aliases[key] in self._names:
            return WineryMatch("alias", licence_number=self._aliases[key])

        # A company can hold licences for several wineries, so a winery's own name wins.
        for index in (self._by_name, self._by_licensee):
            licences = index.get(key, set())
            if len(licences) == 1:
                return WineryMatch("exact", licence_number=next(iter(licences)))
            if licences:
                return WineryMatch("review", candidate=self._describe(licences), reason="several licences share this name")

        if len(key) >= _MIN_CANDIDATE_LENGTH:
            keys = {**self._by_licensee, **self._by_name}
            contains = sorted(k for k in keys if key in k or (len(k) >= _MIN_CANDIDATE_LENGTH and k in key))
            close = difflib.get_close_matches(key, keys, n=3, cutoff=_CLOSE_MATCH_CUTOFF)
            candidates = list(dict.fromkeys(contains + close))[:3]
            if candidates:
                licences = {n for k in candidates for n in keys[k]}
                return WineryMatch("review", candidate=self._describe(licences), reason="similar name")

        return WineryMatch("unmatched", reason="no similar licensed winery")
