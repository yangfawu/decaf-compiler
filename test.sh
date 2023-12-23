#!/bin/bash
INPUT_FILES=$(find input -type f -name "*.decaf" | sort)
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
BLUE=$(tput setaf 4)
RESET=$(tput sgr0)
FAILING_NAMES="invalid|missing|error"

mkdir -p ami

cnt=0
failed=0
for input_path in $INPUT_FILES; do
    ((cnt=cnt+1))

    output_path=$(echo "${input_path}.out" | sed "s/input/output/")
    output_dir=$(dirname "$output_path")
    output_name=$(basename "$output_path")
    
    mkdir -p "$output_dir"

    expected=0
    [[ $output_name =~ .*$FAILING_NAMES.* ]] && expected=1
    
    python3 src/decaf_compiler.py "$input_path" > "$output_path" 2>&1
    got=$?
    
    if [ $got -eq $expected ]; then
        echo "[${GREEN}PASS${RESET}] ${input_path}"
        mv *.ami ami/.
    else
        echo "[${RED}FAIL${RESET}] ${input_path}"
        echo "       Expected exit status ${expected}, but got ${got}"
        ((failed=failed+1))
    fi
done

echo "[${BLUE}====${RESET}] Tested: $cnt | Passing: $((cnt-failed)) | Failing: ${failed}"
