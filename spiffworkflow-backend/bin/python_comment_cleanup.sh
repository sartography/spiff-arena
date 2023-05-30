#!/usr/bin/env bash

function error_handler() {
  >&2 echo "Exited with BAD EXIT CODE '${2}' in ${0} script at line: ${1}."
  exit "$2"
}
trap 'error_handler ${LINENO} $?' ERR
set -o errtrace -o errexit -o nounset -o pipefail

# Function to check if a string matches the file name pattern
matches_filename_pattern() {
  local file_name="$1"
  local comment_line="$2"

  # Remove file extension and capitalize the first letter
  local expected_comment=$(basename "$file_name" .py)

  expected_comment_with_first_letter_capitalized="${expected_comment^}"

  if grep -Eq "\"\"\"${expected_comment}\.\"\"\"" <<< "$comment_line"; then
    return 0
  else
    if grep -Eq "\"\"\"${expected_comment_with_first_letter_capitalized}\.\"\"\"" <<< "$comment_line"; then
      return 0
    else
      return 1
    fi
  fi
}

# Process each Python file in the "src" and "tests" directories
for file in $(find src tests -type f -name '*.py'); do
  # Read the first line of the file
  read -r first_line < "$file"

  # Check if the first line matches the expected comment pattern
  if matches_filename_pattern "$file" "$first_line"; then
    # Remove the comment from the file
    hot_sed -i '1d' "$file"
  fi
done
