#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

# Change only values inside [].
CONFIG: dict[str, Any] = {
    "DB_PATH": "[AUTO]",  # [AUTO] or absolute path (example: [/Users/me/PyRIT_ko/dbdata/pyrit.db])
    "SCENARIO_NAME": "[Encoding]",  # [ANY] for latest across all scenarios, or [Encoding], [RedTeamAgent], ...
    "SCENARIO_RESULT_ID": "[LATEST]",  # [LATEST] or fixed scenario_result_id UUID
    "SAMPLE_LIMIT": 10,
}


def _token(value: Any) -> str:
    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        return text[1:-1].strip()
    return text


def _print_table(title: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    print(f"\n=== {title} ===")
    if not rows:
        print("(no rows)")
        return

    widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            widths[col] = max(widths[col], len(str(row.get(col, ""))))

    header = "  ".join(col.ljust(widths[col]) for col in columns)
    line = "  ".join("-" * widths[col] for col in columns)
    print(header)
    print(line)
    for row in rows:
        print("  ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))


def _resolve_db_path() -> Path:
    db_path_token = _token(CONFIG["DB_PATH"])
    if db_path_token.upper() == "AUTO":
        repo_root = Path(__file__).resolve().parents[1]
        return Path(repo_root, "dbdata", "pyrit.db").resolve()
    return Path(db_path_token).expanduser().resolve()


def _resolve_scenario_result_row(conn: sqlite3.Connection) -> sqlite3.Row:
    scenario_result_id_token = _token(CONFIG["SCENARIO_RESULT_ID"])
    scenario_name_token = _token(CONFIG["SCENARIO_NAME"])

    if scenario_result_id_token.upper() != "LATEST":
        row = conn.execute(
            """
            SELECT id, scenario_name, scenario_run_state, timestamp, attack_results_json
            FROM ScenarioResultEntries
            WHERE id = ?
            """,
            (scenario_result_id_token,),
        ).fetchone()
        if row is None:
            raise ValueError(f"ScenarioResultEntries.id not found: {scenario_result_id_token}")
        return row

    if scenario_name_token.upper() == "ANY":
        row = conn.execute(
            """
            SELECT id, scenario_name, scenario_run_state, timestamp, attack_results_json
            FROM ScenarioResultEntries
            ORDER BY timestamp DESC
            LIMIT 1
            """
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT id, scenario_name, scenario_run_state, timestamp, attack_results_json
            FROM ScenarioResultEntries
            WHERE scenario_name = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (scenario_name_token,),
        ).fetchone()

    if row is None:
        if scenario_name_token.upper() == "ANY":
            raise ValueError("No scenario results found.")
        raise ValueError(f"No scenario results found for scenario_name={scenario_name_token!r}")
    return row


def _fetch_attack_rows_by_conversation_ids(
    conn: sqlite3.Connection, conversation_ids: list[str]
) -> dict[str, sqlite3.Row]:
    if not conversation_ids:
        return {}
    placeholders = ",".join("?" for _ in conversation_ids)
    query = f"""
        SELECT conversation_id, outcome, timestamp, objective, outcome_reason
        FROM AttackResultEntries
        WHERE conversation_id IN ({placeholders})
    """
    rows = conn.execute(query, conversation_ids).fetchall()
    return {str(row["conversation_id"]): row for row in rows}


def main() -> None:
    db_path = _resolve_db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"DB file not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    print(f"DB path: {db_path}")

    recent_rows = conn.execute(
        """
        SELECT id, scenario_name, scenario_run_state, timestamp
        FROM ScenarioResultEntries
        ORDER BY timestamp DESC
        LIMIT 5
        """
    ).fetchall()
    _print_table(
        "Recent Scenario Runs",
        [dict(row) for row in recent_rows],
        ["id", "scenario_name", "scenario_run_state", "timestamp"],
    )

    scenario_row = _resolve_scenario_result_row(conn)
    scenario_id = str(scenario_row["id"])
    scenario_name = str(scenario_row["scenario_name"])
    print(f"\nSelected run: {scenario_id} ({scenario_name})")

    attack_results_json_text = scenario_row["attack_results_json"] or "{}"
    strategy_to_conversation_ids: dict[str, list[str]] = json.loads(attack_results_json_text)

    strategy_pairs: list[tuple[str, str]] = []
    for strategy, conversation_ids in strategy_to_conversation_ids.items():
        for conversation_id in conversation_ids:
            strategy_pairs.append((strategy, str(conversation_id)))

    if not strategy_pairs:
        print("\nNo attack conversation IDs found in attack_results_json.")
        return

    attack_rows_by_conversation_id = _fetch_attack_rows_by_conversation_ids(
        conn, [conversation_id for _, conversation_id in strategy_pairs]
    )

    by_strategy = defaultdict(lambda: {"total": 0, "success": 0, "matched": 0})
    detailed_rows: list[dict[str, Any]] = []
    missing_conversation_ids = 0

    for strategy, conversation_id in strategy_pairs:
        by_strategy[strategy]["total"] += 1
        row = attack_rows_by_conversation_id.get(conversation_id)
        if row is None:
            missing_conversation_ids += 1
            continue

        by_strategy[strategy]["matched"] += 1
        outcome = str(row["outcome"])
        if outcome == "success":
            by_strategy[strategy]["success"] += 1

        detailed_rows.append(
            {
                "strategy": strategy,
                "conversation_id": conversation_id,
                "timestamp": str(row["timestamp"]),
                "objective": str(row["objective"]),
                "outcome": outcome,
                "outcome_reason": str(row["outcome_reason"] or ""),
            }
        )

    summary_rows: list[dict[str, Any]] = []
    for strategy in sorted(by_strategy.keys()):
        total = by_strategy[strategy]["total"]
        success = by_strategy[strategy]["success"]
        matched = by_strategy[strategy]["matched"]
        success_rate = (success * 100.0 / total) if total else 0.0
        summary_rows.append(
            {
                "strategy": strategy,
                "total": total,
                "success": success,
                "success_rate_pct": f"{success_rate:.1f}",
                "matched_rows": matched,
            }
        )

    _print_table(
        "Strategy Summary",
        summary_rows,
        ["strategy", "total", "success", "success_rate_pct", "matched_rows"],
    )
    if missing_conversation_ids:
        print(f"\nWarning: {missing_conversation_ids} conversation IDs were not found in AttackResultEntries.")

    sample_limit = int(CONFIG["SAMPLE_LIMIT"])
    success_rows = sorted(
        [row for row in detailed_rows if row["outcome"] == "success"],
        key=lambda x: x["timestamp"],
        reverse=True,
    )[:sample_limit]
    failure_rows = sorted(
        [row for row in detailed_rows if row["outcome"] != "success"],
        key=lambda x: x["timestamp"],
        reverse=True,
    )[:sample_limit]

    _print_table(
        f"Success Samples (top {sample_limit})",
        success_rows,
        ["strategy", "timestamp", "objective", "outcome"],
    )
    _print_table(
        f"Failure Samples (top {sample_limit})",
        failure_rows,
        ["strategy", "timestamp", "objective", "outcome_reason"],
    )


if __name__ == "__main__":
    main()
