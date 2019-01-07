#!/bin/bash

REPO_SLUG=$TRAVIS_REPO_SLUG  # user/repo
AUTH_TOKEN=$GH_TOKEN
RELEASE_TAG=$TRAVIS_TAG
PREVIEW=false

LAST_RELEASE="$( git describe --abbrev=0 --tags `git rev-list --tags --skip=1  --max-count=1` )"

GENERATE_POST_BODY() {
  cat <<EOF
{
  "tag_name": "$RELEASE_TAG",
  "target_commitish": "master",
  "name": "$RELEASE_TAG",
  "body": $FORMAT_CONTENT,
  "draft": false,
  "prerelease": true
}
EOF
}

CREATE_CHANGELOG() {

  # Definition of default commit types
  declare -A COMMIT_TYPES=( ["BUG"]="Bug Fixes"
                            ["DOC"]="Documentation"
                            ["BLD"]="Continuous Integration"
                            ["ENH"]="Enhancements and Features"
                            ["SIM"]="LinuxCNC sim Configs"
                            ["VCP"]="VCP Examples"
                            ["Merge"]="Branch Merges"
                            )

  # String to accumulate changelog
  CONTENT="Changes since the ${LAST_RELEASE} release.\n\n"

  # Get all commits with type annotations and make them paragraphs.
  for TYPE in "${!COMMIT_TYPES[@]}"
    do
      if [ -z "$1" ]
        then
          PARAGRAPH="$(git log --format="* %s (%h)" --grep="^${TYPE}")"
        else
          PARAGRAPH="$(git log "$1"..HEAD --format="* %s (%h)" --grep="^${TYPE}")"
      fi
      if [ ! -z "$PARAGRAPH" ]
        then
          TITLE="${COMMIT_TYPES[$TYPE]}"
          PARAGRAPH="${PARAGRAPH//$TYPE: /}"
          CONTENT="$CONTENT### $TITLE\n\n$PARAGRAPH\n\n"
      fi
    done

  # Regex used to find commits without types
  TYPES_REGEX=""
  for TYPE in "${!COMMIT_TYPES[@]}"
    do
      TYPES_REGEX="$TYPES_REGEX$TYPE:\|"
  done
  TYPES_REGEX="$TYPES_REGEX\[skip-changelog\]"

  # Get all commit without type annotation and make them another paragraph.
  if [ -z "$1" ]
    then
      PARAGRAPH="$(git log --format=";* %s (%h);")"
    else
      PARAGRAPH="$(git log "$1"..HEAD --format=";* %s (%h);")"
  fi
  OIFS="$IFS"
  IFS=";"
  FILTERED_PARAGRAPH=""
  for COMMIT in $PARAGRAPH
   do
     TRIMMED_COMMIT="$(echo "$COMMIT" | xargs)"
    if [ ! -z "$TRIMMED_COMMIT" ] && ! echo "$TRIMMED_COMMIT" | grep -q "$TYPES_REGEX"
      then
        FILTERED_PARAGRAPH="$FILTERED_PARAGRAPH$TRIMMED_COMMIT\n"
    fi
  done
  IFS="$OIFS"

  # Only add to content if there are commits without type annotations.
  if [ ! -z "$FILTERED_PARAGRAPH" ]
   then
     CONTENT="$CONTENT### Other\n\n$FILTERED_PARAGRAPH\n\n"
  fi

  # Output changelog
  echo -e "$CONTENT"
}

#
# Main script
#

# Exit if not in a Git repository.
if [ "true" != "$(git rev-parse --is-inside-work-tree 2> /dev/null)" ]
  then
    echo -e "This does not seem to be a Git repository.\n"
    exit
fi

# Generate changelog either from last tag or from beginning
if [ -z "$(git tag)" ]
  then
    CONTENT=$(CREATE_CHANGELOG)
  else
    CONTENT=$(CREATE_CHANGELOG "${LAST_RELEASE}")
fi

# In preview mode, show changelog and exit
if [ "$PREVIEW" = true ]
  then
    echo "-----------------------------------------------------"
    echo "$CONTENT"
    echo "-----------------------------------------------------"
  exit
fi

FORMAT_CONTENT="$(node -p -e 'JSON.stringify(process.argv[1])' "${CONTENT}")"
RESPONSE=$(curl --silent -H "Content-Type: application/json" -X POST --data "$(GENERATE_POST_BODY)" "https://api.github.com/repos/${REPO_SLUG}/releases?access_token=${GH_TOKEN}")

echo $RESPONSE
