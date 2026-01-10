#!/bin/bash

JSON_FILE="$1"

if [ -z "$JSON_FILE" ]; then
    echo "Usage: bash validate-covalent.sh <cochart-file.json>"
    exit 1
fi

if [ ! -f "$JSON_FILE" ]; then
    echo "Error: File not found: $JSON_FILE"
    exit 1
fi

echo "======================================"
echo "COCHART VALIDATION REPORT"
echo "======================================"
echo "File: $JSON_FILE"
echo ""

ERRORS=0
CHECKED=0
BASEDIR=$(dirname "$JSON_FILE")
TMPFILE=$(mktemp)
TMPIDS=$(mktemp)

# Extract line numbers where "id" field appears (marks start of each node)
grep -n '"id"[[:space:]]*:' "$JSON_FILE" | cut -d: -f1 > "$TMPIDS"

while IFS= read -r line_num; do
    # Find next "id" line to determine node boundary
    next_line=$(awk -v current=$line_num 'NR > current && /"id"[[:space:]]*:/ {print NR; exit}' "$JSON_FILE")
    [ -z "$next_line" ] && next_line=$(wc -l < "$JSON_FILE")

    # Extract node as single line (replace newlines with spaces)
    # Use next_line-1 to exclude the start of next object
    prev_line=$((next_line - 1))
    [ $prev_line -lt $line_num ] && prev_line=$line_num
    node=$(sed -n "${line_num},${prev_line}p" "$JSON_FILE" | tr '\n' ' ')

    # Parse node fields using sed
    id=$(echo "$node" | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*\([0-9]*\).*/\1/p')
    label=$(echo "$node" | sed -n 's/.*"label"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    filePath=$(echo "$node" | sed -n 's/.*"filePath"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    lineNumber=$(echo "$node" | sed -n 's/.*"lineNumber"[[:space:]]*:[[:space:]]*\([0-9]*\).*/\1/p')
    lineContent=$(echo "$node" | sed -n 's/.*"lineContent"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    nodeType=$(echo "$node" | sed -n 's/.*"type"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

    # Schema checks
    # Check for required label
    if [ -z "$label" ]; then
        ((ERRORS++))
        echo "[ERROR] Node $id: Missing required label"
    fi

    # Check type and properties
    if [ "$nodeType" = "todo" ]; then
        # TODO node: should not have lineNumber or filePath
        if [ ! -z "$lineNumber" ]; then
            ((ERRORS++))
            echo "[ERROR] Node $id: TODO node should not have lineNumber"
        fi
        if [ ! -z "$filePath" ]; then
            ((ERRORS++))
            echo "[ERROR] Node $id: TODO node should not have filePath"
        fi
        continue
    elif [ ! -z "$nodeType" ] && [ "$nodeType" != "todo" ]; then
        # Invalid type
        ((ERRORS++))
        echo "[ERROR] Node $id: Invalid type '$nodeType' (only 'todo' allowed)"
    else
        # CODE node
        if [ -z "$lineNumber" ]; then
            ((ERRORS++))
            echo "[ERROR] Node $id: CODE node missing lineNumber"
        fi
        if [ -z "$filePath" ]; then
            ((ERRORS++))
            echo "[ERROR] Node $id: CODE node missing filePath"
        fi
    fi

    ((CHECKED++))

    # Content validation (only for CODE nodes with valid filePath)
    if [ ! -z "$filePath" ]; then
        fullPath="$BASEDIR/../../$filePath"
        fullPath=$(cd "$(dirname "$fullPath")" 2>/dev/null && pwd)/$(basename "$fullPath")

        if [ ! -f "$fullPath" ]; then
            ((ERRORS++))
            echo "[ERROR] Node $id: File not found at $fullPath"
        else
            # Extract actual line and trim
            actualLine=$(sed -n "${lineNumber}p" "$fullPath" 2>/dev/null | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            expectedLine=$(echo "$lineContent" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

            if [ "$actualLine" != "$expectedLine" ]; then
                ((ERRORS++))
                echo "[ERROR] Node $id: Line content mismatch"
                echo "  Expected: \"$expectedLine\""
                echo "  Actual:   \"$actualLine\""
            fi
        fi
    fi
done < "$TMPIDS"

rm -f "$TMPFILE" "$TMPIDS"

echo ""
echo "======================================"
echo "Checked: $CHECKED CODE nodes"
echo "Errors: $ERRORS"
echo "======================================"

exit 0
