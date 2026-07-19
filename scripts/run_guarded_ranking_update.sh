#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python_bin="${FOOTBALL_PYTHON:-/home/albertovth/anaconda3/envs/spyder607/bin/python}"
results_source="${FOOTBALL_RESULTS_SOURCE:-https://raw.githubusercontent.com/martj42/international_results/master/results.csv}"
minimum_matches="${FOOTBALL_MINIMUM_NEW_MATCHES:-100}"
run_date="${FOOTBALL_RUN_DATE:-$(TZ=Europe/Oslo date +%F)}"
compact_date="${run_date//-/}"
input_dir="$repo_root/data/input/automatic_$compact_date"
run_dir="$repo_root/data/output/automatic_$compact_date"
log_dir="$run_dir/logs"
lock_file="$repo_root/data/output/.ranking_update.lock"

mkdir -p "$input_dir" "$log_dir" "$run_dir/prior"
notification_log="$log_dir/ntfy.log"

send_notification() {
    local level="$1"
    local title="$2"
    local message="$3"
    if ! "$python_bin" scripts/send_ranking_ntfy.py \
        --level "$level" --title "$title" --message "$message" \
        >> "$notification_log" 2>&1; then
        echo "ntfy notification failed; see $notification_log" >&2
    fi
}

abort_update() {
    local message="$1"
    local status="${2:-1}"
    echo "$message" >&2
    send_notification error "Football ranking cron needs attention" "$message See $log_dir."
    exit "$status"
}

ensure_finite_log() {
    local path="$1"
    if rg -qi '(^|[^A-Za-z])(nan|[+-]?inf)([^A-Za-z]|$)' "$path"; then
        abort_update "Non-finite calibration output detected in $path; the live ranking was not changed."
    fi
}

handle_error() {
    local status="$1"
    local line="$2"
    trap - ERR
    send_notification \
        error \
        "Football ranking cron needs attention" \
        "The guarded ranking update for $run_date failed at line $line (exit $status). The published ranking was not intentionally replaced unless validation had already completed. See $log_dir."
    exit "$status"
}

trap 'handle_error "$?" "$LINENO"' ERR
exec 9>"$lock_file"
if ! flock -n 9; then
    echo "Another ranking update is already running; exiting."
    exit 0
fi

if [[ ! -x "$python_bin" ]]; then
    echo "Configured Python is not executable: $python_bin" >&2
    exit 1
fi

# Never build on top of unpublished edits to the live ranking/evidence files.
if ! git diff --quiet -- \
    ranking_final.csv \
    data/output/ranking_final.csv \
    data/output/ranking_evidence.csv \
    data/output/ranking_evidence_ledger.csv; then
    abort_update "Live ranking/evidence files have uncommitted changes; refusing automation."
fi
if ! git diff --cached --quiet -- \
    ranking_final.csv \
    data/output/ranking_final.csv \
    data/output/ranking_evidence.csv \
    data/output/ranking_evidence_ledger.csv; then
    abort_update "Live ranking/evidence files have staged unpublished changes; refusing automation."
fi

cp ranking_final.csv "$run_dir/prior/ranking.csv"
cp data/output/ranking_evidence.csv "$run_dir/prior/evidence.csv"
cp data/output/ranking_evidence_ledger.csv "$run_dir/prior/evidence_ledger.csv"

if "$python_bin" scripts/prepare_rolling_ranking_update.py \
    --source "$results_source" \
    --prior-ranking "$run_dir/prior/ranking.csv" \
    --prior-ledger "$run_dir/prior/evidence_ledger.csv" \
    --dictionary data/config/dictionary.csv \
    --output-dir "$input_dir" \
    --minimum-matches "$minimum_matches" \
    --run-date "$run_date" \
    > "$log_dir/00_prepare.log" 2>&1; then
    prepare_status=0
else
    prepare_status=$?
fi
if [[ "$prepare_status" -eq 3 ]]; then
    echo "Not enough new eligible matches; current ranking left unchanged."
    cat "$log_dir/00_prepare.log"
    eligible_count="$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["eligible_matches"])' "$input_dir/control.json")"
    send_notification \
        info \
        "Football ranking check completed" \
        "Monthly check succeeded: $eligible_count of $minimum_matches required new eligible matches are available. No ranking update was run."
    exit 0
fi
if [[ "$prepare_status" -ne 0 ]]; then
    cat "$log_dir/00_prepare.log" >&2
    abort_update "Input preparation failed; current ranking left unchanged." "$prepare_status"
fi

stage_start="$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["stage_start"])' "$input_dir/control.json")"
stage_end="$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["stage_end"])' "$input_dir/control.json")"
median_start="$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["evidence_window_start"])' "$input_dir/control.json")"
median_end="$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["evidence_window_end"])' "$input_dir/control.json")"
excluded_count="$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["excluded_rows"])' "$input_dir/control.json")"
unfinished_count="$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["unfinished_rows"])' "$input_dir/control.json")"
if (( excluded_count > 0 || unfinished_count > 0 )); then
    send_notification \
        warning \
        "Football ranking source warning" \
        "The $run_date source audit recorded $excluded_count excluded completed rows and $unfinished_count unfinished rows. They are documented and excluded; the guarded update will continue only if every validation gate passes."
fi

mkdir -p \
    "$run_dir/raw/intermediate/confed" \
    "$run_dir/intermediate/confed" \
    "$run_dir/output" \
    "$run_dir/reproducibility/run1" \
    "$run_dir/reproducibility/run2"

common_raw_env=(
    FOOTBALL_DATA_DIR="$repo_root/data"
    FOOTBALL_INTERMEDIATE_DIR="$run_dir/raw/intermediate"
    FOOTBALL_STAGE2_PRIOR_FILE="$run_dir/prior/ranking.csv"
    FOOTBALL_RESULTS_SOURCE="$input_dir/results.csv"
    FOOTBALL_GOAL_MEDIAN_RESULTS_SOURCE="$input_dir/goal_median_results.csv"
    GOAL_MEDIAN_START_DATE="$median_start"
    GOAL_MEDIAN_END_DATE="$median_end"
    STAGE2_START_DATE="$stage_start"
    STAGE2_END_DATE="$stage_end"
)

env "${common_raw_env[@]}" "$python_bin" \
    pipeline/spi_stage2/init_from_spi_538.py \
    > "$log_dir/01_init_prior.log" 2>&1
env "${common_raw_env[@]}" STAGE2_CUTOFF_QUANTILE=0.07 "$python_bin" \
    pipeline/spi_stage2/calculate_adjustment_factor.py \
    > "$log_dir/02_adjustment_factor.log" 2>&1
env "${common_raw_env[@]}" "$python_bin" \
    pipeline/spi_stage2/calculate_caps_off_def.py \
    > "$log_dir/03_caps_off_def.log" 2>&1
env "${common_raw_env[@]}" "$python_bin" \
    pipeline/spi_stage2/calculate_low_team_cutoff.py \
    > "$log_dir/04_low_team_cutoff.log" 2>&1
ensure_finite_log "$log_dir/02_adjustment_factor.log"
ensure_finite_log "$log_dir/03_caps_off_def.log"
ensure_finite_log "$log_dir/04_low_team_cutoff.log"

selected_cutoff="$("$python_bin" -c '
import re,sys
text=open(sys.argv[1]).read()
found=re.findall(r"Found a suitable quantile:\s*([0-9.]+)", text)
print(found[-1] if found else "0.07")
' "$log_dir/04_low_team_cutoff.log")"

env "${common_raw_env[@]}" STAGE2_CUTOFF_QUANTILE="$selected_cutoff" "$python_bin" \
    pipeline/spi_stage2/calculate_xg_xga.py \
    > "$log_dir/05_calculate_raw_xg_xga.log" 2>&1
ensure_finite_log "$log_dir/05_calculate_raw_xg_xga.log"

"$python_bin" pipeline/spi_stage3/combine_prior_evidence.py \
    --prior-ranking "$run_dir/prior/ranking.csv" \
    --prior-evidence "$run_dir/prior/evidence.csv" \
    --prior-evidence-ledger "$run_dir/prior/evidence_ledger.csv" \
    --new-metrics "$run_dir/raw/intermediate/aggregated_xg_data.csv" \
    --dictionary data/config/dictionary.csv \
    --results "$input_dir/results.csv" \
    --start-date "$stage_start" \
    --end-date "$stage_end" \
    --goal-median-results "$input_dir/goal_median_results.csv" \
    --goal-median-start-date "$median_start" \
    --goal-median-end-date "$median_end" \
    --aggregated-output "$run_dir/intermediate/aggregated_xg_data.csv" \
    --confed-output-dir "$run_dir/intermediate/confed" \
    --calibration-output "$run_dir/evidence_calibration.csv" \
    --evidence-output "$run_dir/evidence_final.csv" \
    --evidence-ledger-output "$run_dir/evidence_ledger_final.csv" \
    --windowed-prior-output "$run_dir/windowed_prior_evidence.csv" \
    --evidence-cutoff-date "$run_date" \
    --evidence-window-years 4 \
    --stage-label "auto_$compact_date" \
    --audit-output "$run_dir/evidence_normalization.csv" \
    > "$log_dir/06_combine_prior_evidence.log" 2>&1
ensure_finite_log "$log_dir/06_combine_prior_evidence.log"

simulation_env=(
    FOOTBALL_DATA_DIR="$repo_root/data"
    FOOTBALL_INTERMEDIATE_DIR="$run_dir/intermediate"
    FOOTBALL_RESULTS_SOURCE="$input_dir/results.csv"
    FOOTBALL_GOAL_MEDIAN_RESULTS_SOURCE="$input_dir/goal_median_results.csv"
    GOAL_MEDIAN_START_DATE="$median_start"
    GOAL_MEDIAN_END_DATE="$median_end"
    STAGE2_START_DATE="$stage_start"
    STAGE2_END_DATE="$stage_end"
)

env "${simulation_env[@]}" \
    FOOTBALL_OUTPUT_DIR="$run_dir/output" \
    FOOTBALL_RANKING_OUTPUT_FILE="$run_dir/output/ranking_final.csv" \
    FOOTBALL_ROOT_RANKING_FILE="$run_dir/output/root_ranking_final.csv" \
    "$python_bin" pipeline/spi_stage2/simulate_spi.py \
    > "$log_dir/07_production_simulation.log" 2>&1

for reproducibility_run in run1 run2; do
    reproducibility_dir="$run_dir/reproducibility/$reproducibility_run"
    env "${simulation_env[@]}" \
        FOOTBALL_OUTPUT_DIR="$reproducibility_dir" \
        FOOTBALL_RANKING_OUTPUT_FILE="$reproducibility_dir/ranking_final.csv" \
        FOOTBALL_ROOT_RANKING_FILE="$reproducibility_dir/root_ranking_final.csv" \
        "$python_bin" -c \
        "import numpy as np, runpy; np.random.seed($compact_date); runpy.run_path('pipeline/spi_stage2/simulate_spi.py', run_name='__main__')" \
        > "$log_dir/08_seeded_$reproducibility_run.log" 2>&1
done

"$python_bin" -m pytest -q > "$log_dir/09_pytest.log" 2>&1
"$python_bin" scripts/validate_and_publish_ranking_update.py \
    --run-dir "$run_dir" \
    --input-dir "$input_dir" \
    --prior-ranking "$run_dir/prior/ranking.csv" \
    --prior-evidence "$run_dir/prior/evidence.csv" \
    --prior-ledger "$run_dir/prior/evidence_ledger.csv" \
    --dictionary data/config/dictionary.csv \
    --selected-cutoff "$selected_cutoff" \
    --publish \
    > "$log_dir/10_validate_and_publish.log" 2>&1

if [[ "${FOOTBALL_AUTO_GIT_PUSH:-0}" == "1" ]]; then
    dated="$("$python_bin" -c 'import pandas as pd,sys; d=pd.Timestamp(sys.argv[1]); print(f"{d.day}_{d.month}_{d.year}")' "$run_date")"
    git add \
        ranking_final.csv \
        data/output/ranking_final.csv \
        data/output/ranking_evidence.csv \
        data/output/ranking_evidence_ledger.csv \
        "data/config/priors/spi_global_rankings_intl_$dated.csv" \
        "data/config/priors/ranking_evidence_$dated.csv" \
        "data/config/priors/ranking_evidence_ledger_$dated.csv"
    if ! git diff --cached --quiet; then
        git commit -m "Update international ranking through $run_date"
        git push
    fi
fi

send_notification \
    success \
    "Football ranking updated" \
    "The guarded update for $run_date passed calibration, mapping, rolling-window, test, and reproducibility checks. The validated ranking was published successfully."
echo "Validated rolling ranking update published for $run_date."
