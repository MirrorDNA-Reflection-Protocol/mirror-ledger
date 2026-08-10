"""Static contract checks for the weekly orchestrator's fail-closed preflight."""

from pathlib import Path


def test_mirrorstate_is_refreshed_before_gather():
    script = (
        Path(__file__).resolve().parents[1] / "scripts" / "run_weekly.sh"
    ).read_text(encoding="utf-8")
    mirrorstate_stage = script.index('STAGE="mirrorstate"')
    ensure_call = script.index('"$PYBIN" "$MIRRORSTATE_RUNTIME" ensure')
    gather_stage = script.index('STAGE="gather"')
    assert mirrorstate_stage < ensure_call < gather_stage
    assert 'MIRRORSTATE_RUNTIME="$HOME/.mirrordna/scripts/mirrorstate_runtime.py"' in script
