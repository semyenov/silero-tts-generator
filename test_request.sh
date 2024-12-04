#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base URL for the TTS server
BASE_URL="http://localhost:8765"

# Function to display usage
usage() {
    echo "Usage: $0 -t text [-s speaker] [-h]"
    echo "Options:"
    echo "  -t    Text to convert to speech (required)"
    echo "  -s    Speaker (default: xenia)"
    echo "  -h    Show this help message"
    exit 1
}

# Default values
TEXT=""
SPEAKER="xenia"

# Parse arguments using getopts
while getopts ":t:s:h" opt; do
    case ${opt} in
    t)
        TEXT="$OPTARG"
        ;;
    s)
        SPEAKER="$OPTARG"
        ;;
    h)
        usage
        ;;
    \?)
        echo "Invalid option: $OPTARG" 1>&2
        usage
        ;;
    :)
        echo "Invalid option: $OPTARG requires an argument" 1>&2
        usage
        ;;
    esac
done
shift $((OPTIND - 1))

# Check if text is provided
if [ -z "$TEXT" ]; then
    echo "Error: Text is required" 1>&2
    usage
fi

# Perform TTS request
echo -e "${YELLOW}Generating speech...${NC}"
echo -e "${GREEN}Text:${NC} $TEXT"
echo -e "${GREEN}Speaker:${NC} $SPEAKER"

# Make the request
RESPONSE=$(curl -s -X POST "$BASE_URL/tts" \
    -H "Content-Type: application/json" \
    -d "{
        \"text\": \"$TEXT\",
        \"speaker\": \"$SPEAKER\",
        \"enhance_noise\": true
    }")

# Check if request was successful
SUCCESS=$(echo "$RESPONSE" | jq -r '.success')
if [ "$SUCCESS" = "true" ]; then
    FILENAME=$(echo "$RESPONSE" | jq -r '.filename')
    DURATION=$(echo "$RESPONSE" | jq -r '.duration')

    echo -e "${GREEN}Speech generated successfully!${NC}"
    echo -e "${YELLOW}Filename:${NC} $FILENAME"
    echo -e "${YELLOW}Duration:${NC} $DURATION seconds"

    # Attempt to download the audio file
    echo -e "${YELLOW}Downloading audio file...${NC}"
    curl -s -O "$BASE_URL/audio/$FILENAME"

    echo -e "${GREEN}Audio file downloaded: $FILENAME${NC}"
else
    ERROR=$(echo "$RESPONSE" | jq -r '.error')
    echo -e "${RED}Error generating speech:${NC} $ERROR"
    exit 1
fi
