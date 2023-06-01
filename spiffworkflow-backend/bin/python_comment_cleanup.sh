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

# this is the sort of garbage we want to remove:
# class InvalidLogLevelError(Exception):
#     """InvalidLogLevelError."""

# Function to remove useless comments after class declarations
remove_useless_comments() {
  local file_name="$1"

  # echo "grepping"
  # matches=$(grep --group-separator=HOTSEP -B 1 -E '^\s*"""' "$file_name" || echo '')
  # if [[ -n "$matches" ]]; then
  #   matches="${matches}\nHOTSEP"
  #   echo -e "$matches"
  #   while read -d'HOTSEP' -r match || [ -n "$match" ]; do
  #     echo "match: ${match}"
  #     if [[ -n "$match" ]]; then
  #       code_line_of_match=$(head -n 1 <<< "$match")
  #       echo "code_line_of_match: ${code_line_of_match}"
  #       comment_line_of_match=$(sed -n '2 p' <<< "$match")
  #       echo "comment_line_of_match: ${comment_line_of_match}"
  #       comment_contents=$(hot_sed -E 's/^\s*"""(.*)\.""".*$/\1/' <<< "$comment_line_of_match")
  #       echo "comment_contents: ${comment_contents}"
  #       if grep -Eiq "^class.*${comment_contents}\(Exception\)" <<< "$code_line_of_match"; then
  #         hot_sed -i "s/^(\s*)[^\s]*${comment_line_of_match}.*/\1pass/" "$file_name"
  #       fi
  #       # if grep -Eiq "^\s*(def|class) ${comment_contents}\(" <<< "$code_line_of_match"; then
  #       #   # Remove line from file matching comment_line
  #       #   hot_sed -i "/${comment_line_of_match}/d" "$file_name"
  #       # fi
  #     fi
  #   done <<< $matches
  # fi
  # matches=$(grep -E '\s*(def|class) ' "$file_name" || echo '')
  # if [[ -n "$matches" ]]; then
  # fi
  sed -Ei 's/^(\s*)"""[A-Z]\w*Error\."""/\1pass/' "$file_name"
  sed -Ei '/^\s*"""[A-Z_]\w*\."""/d' "$file_name"
}

# Process each Python file in the "src" and "tests" directories
for file in $(find src tests -type f -name '*.py'); do
  # Read the first line of the file
  # if grep -Eq '/logging_service' <<< "$file"; then
    echo "processing file that we hand picked for debugging: ${file}"
    remove_useless_comments "$file"
  # fi

  # this is already done
  # if [ -s "$file" ]; then
  #   # read -r first_line < "$file"
  #
  #   # Check if the first line matches the expected comment pattern
  #   # if matches_filename_pattern "$file" "$first_line"; then
  #   #   # Remove the comment from the file
  #   #   hot_sed -i '1d' "$file"
  #   #
  #   #   # Remove useless comments after class declarations
  #   # fi
  # fi
done
