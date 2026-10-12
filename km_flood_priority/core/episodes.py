"""Group distinct dates using successive gaps, rather than the episode's first date."""

from datetime import date


def group_episodes(dates, gap_days: int = 2) -> list[tuple[date, ...]]:
    if gap_days < 0:
        raise ValueError("EPISODE_GAP_DAYS must be non-negative")
    groups = []
    for day in sorted(set(dates)):
        if not groups or (day - groups[-1][-1]).days > gap_days:
            groups.append([day])
        else:
            groups[-1].append(day)
    return [tuple(group) for group in groups]
