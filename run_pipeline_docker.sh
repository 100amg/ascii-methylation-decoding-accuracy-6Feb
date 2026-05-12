#!/usr/bin/env bash
# Requires modkit 0.5.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ------------------------------
# Argument parsing
# ------------------------------
if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
    echo "Usage: $0 <bam_directory> <reference_fasta> [bitwidth] [ask|always|never]"
    exit 1
fi

# BAM directory
BAM_DIR="$(realpath "$1")"
[ -d "$BAM_DIR" ] || { echo "ERROR: BAM directory not found"; exit 1; }

# Reference FASTA
REF_FILE="$(realpath "$2")"
[ -f "$REF_FILE" ] || { echo "ERROR: Reference FASTA not found"; exit 1; }

BITWIDTH="${3:-8}"
INTERACTIVE_MODE="${4:-ask}"

if [[ ! "$INTERACTIVE_MODE" =~ ^(ask|always|never)$ ]]; then
    echo "ERROR: INTERACTIVE_MODE must be ask, always, or never"
    exit 1
fi

echo "BITWIDTH           : $BITWIDTH"
echo "Reference FASTA    : $REF_FILE"
echo "Error-stats mode   : $INTERACTIVE_MODE"

# ------------------------------
# Output directories
# ------------------------------
# saved relative to the directory you're running it from, not of the files being used

OUTROOT="results"
CPG_DIR="$OUTROOT/methylation_cpg"
M_DIR="$OUTROOT/methylation_M"
METHPOS_DIR="$OUTROOT/methpos"
FULL_BED_DIR="$OUTROOT/full_bed"
LOGDIR="$OUTROOT/ASCII_logs"
ERROR_LOGDIR="$OUTROOT/ErrorStats_logs"

mkdir -p "$CPG_DIR" "$M_DIR" "$METHPOS_DIR" "$FULL_BED_DIR" "$LOGDIR" "$ERROR_LOGDIR"

# ------------------------------
# Main loop (RAW BAMs ONLY)
# ------------------------------
# ------------------------------
# Main loop (SORTED BAMs ONLY)
# ------------------------------
for SORTED_BAM in "$BAM_DIR"/*_mod_sorted.bam; do
    [ -e "$SORTED_BAM" ] || continue
    
    SAMPLE_NAME="$(basename "$SORTED_BAM" _mod_sorted.bam)"
    
    echo "======================================"
    echo "Processing sample: $SAMPLE_NAME"
    echo "Sorted BAM: $SORTED_BAM"
    echo "======================================"
    
    # Check for mapped reads - skip if none
    MAPPED_READS=$(samtools idxstats "$SORTED_BAM" | awk '{mapped+=$3} END {print mapped}')
    
    if [[ "$MAPPED_READS" -eq 0 ]]; then
        echo "⚠️  WARNING: No mapped reads for $SAMPLE_NAME - SKIPPING"
        echo "======================================"
        continue
    fi
    
    echo "✓ Found $MAPPED_READS mapped reads"

    # ------------------------------
    # Per-sample bitwidth
    # ------------------------------
    if [[ "$INTERACTIVE_MODE" == "never" ]]; then
        SAMPLE_BITWIDTH="$BITWIDTH"
    else
        echo
        echo "Enter bitwidth for $SAMPLE_NAME (7 or 8) [default: $BITWIDTH]:"
        read -r USER_BITWIDTH

        if [[ -z "$USER_BITWIDTH" ]]; then
            SAMPLE_BITWIDTH="$BITWIDTH"
        elif [[ "$USER_BITWIDTH" == "7" || "$USER_BITWIDTH" == "8" ]]; then
            SAMPLE_BITWIDTH="$USER_BITWIDTH"
        else
            echo "Invalid bitwidth. Using default."
            SAMPLE_BITWIDTH="$BITWIDTH"
        fi
    fi

    echo "Using bitwidth $SAMPLE_BITWIDTH"

    TIMESTAMP="$(date +%d%m%y_%H%M%S)"
    LOGFILE="$LOGDIR/ASCII_Log_${SAMPLE_NAME}_${TIMESTAMP}.log"

    exec 3>&1 4>&2
    exec > >(tee -a "$LOGFILE") 2>&1

    BED_FILE="$CPG_DIR/${SAMPLE_NAME}_methylation_cpg.txt"
    BED_M_FILE="$M_DIR/${SAMPLE_NAME}_methylation_M.txt"
    METHPOS_FILE="$METHPOS_DIR/${SAMPLE_NAME}_methpos.txt"
    FULL_BED_TEXT="$FULL_BED_DIR/${SAMPLE_NAME}_full_bed.txt"

    # ------------------------------
    # modkit pileup (SORTED BAM ONLY)
    # ------------------------------
    modkit pileup \
        --cpg \
        --mod-thresholds C:0.0 \
        --ref "$REF_FILE" \
        "$SORTED_BAM" \
        "$BED_FILE"

    # ------------------------------
    # Filtering
    # ------------------------------
    awk '$4 == "m" && $11 != 0 {print $3, $11}' "$BED_FILE" > "$BED_M_FILE"

    # Count before stats
    COUNT=$(wc -l < "$BED_M_FILE")
    echo "Methylated CpGs before stats: $COUNT"

    # Skip if too few values
    if [[ "$COUNT" -lt 3 ]]; then
        echo "⚠️  Too few methylated CpGs for reliable stats — skipping"
        exec 1>&3 2>&4
        continue
    fi

    # Compute stats safely
    if ! STATS="$(python "$SCRIPT_DIR/B2A/get_stats.py" "$BED_M_FILE" 2>/dev/null)"; then
        echo "⚠️  get_stats failed — skipping $SAMPLE_NAME"
        exec 1>&3 2>&4
        continue
    fi

    MEAN="$(awk '{print $1}' <<< "$STATS")"

    # Ensure MEAN is numeric
    if ! [[ "$MEAN" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        echo "⚠️  Invalid MEAN ($MEAN) — skipping"
        exec 1>&3 2>&4
        continue
    fi

    # Thresholding
    awk -v t="$MEAN" '$11 > t {print $3, $11}' "$BED_FILE" > "$METHPOS_FILE"

    python "$SCRIPT_DIR/B2A/meth_analysis.py" "$METHPOS_FILE" "$SAMPLE_BITWIDTH"

    # ------------------------------
    # Error stats
    # ------------------------------
    if [[ "$INTERACTIVE_MODE" == "always" ]]; then
        RUN_ERROR_STATS="Y"
    elif [[ "$INTERACTIVE_MODE" == "never" ]]; then
        RUN_ERROR_STATS="N"
    else
        echo "Run error analysis for $SAMPLE_NAME? (Y/N)"
        read -r RUN_ERROR_STATS
    fi

    if [[ "$RUN_ERROR_STATS" =~ ^[Yy]$ ]]; then
        ERROR_LOGFILE="$ERROR_LOGDIR/ErrorStats_${SAMPLE_NAME}_${TIMESTAMP}.log"
        python "$SCRIPT_DIR/B2A/error_stats.py" \
            "$METHPOS_FILE" "$SAMPLE_BITWIDTH" | tee -a "$ERROR_LOGFILE"
    fi

    exec 1>&3 2>&4
    echo "Finished sample: $SAMPLE_NAME"
done

echo "All BAM files processed successfully."