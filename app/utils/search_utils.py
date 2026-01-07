def parse_star_search(raw: str):
    """Parse search query supporting:

    - '***' => list all
    - '*' as separator => AND between parts (each part must match)

    Returns: (mode_all: bool, parts: list[str])
    """
    if raw is None:
        return False, []

    termo = str(raw).strip()
    if not termo:
        return False, []

    if termo == '***':
        return True, []

    if '*' in termo:
        parts = [p.strip() for p in termo.split('*') if p and p.strip()]
        return False, parts

    return False, [termo]


def build_multi_part_like_where(parts, columns):
    """Build WHERE clause for AND-of-parts, OR-of-columns.

    Example:
        parts=['rolamento','fb'], columns=['p.name','p.internal_code']

        returns:
            ("((p.name LIKE %s OR p.internal_code LIKE %s) AND (p.name LIKE %s OR p.internal_code LIKE %s))",
             ['%rolamento%','%rolamento%','%fb%','%fb%'])
    """
    if not parts:
        return "", []

    cols = [c for c in (columns or []) if c]
    if not cols:
        return "", []

    clauses = []
    params = []

    for part in parts:
        part_like = f"%{part}%"
        or_clause = " OR ".join([f"{c} LIKE %s" for c in cols])
        clauses.append(f"({or_clause})")
        params.extend([part_like] * len(cols))

    return " AND ".join(clauses), params
