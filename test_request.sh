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
    echo "Usage: $0 [-t text] [-l language] [-m model] [-s speaker] [-h]"
    echo "Options:"
    echo "  -t    Text to convert to speech (required)"
    echo "  -l    Language (default: ru)"
    echo "  -m    Model (default: v4_ru)"
    echo "  -s    Speaker (default: xenia)"
    echo "  -h    Show this help message"
    exit 1
}

# Default values
TEXT=""
LANGUAGE="ru"
MODEL="v4_ru"
SPEAKER="xenia"

# Parse arguments using getopts
while getopts ":t:l:m:s:h" opt; do
    case ${opt} in
    t)
        TEXT="$OPTARG"
        ;;
    l)
        LANGUAGE="$OPTARG"
        ;;
    m)
        MODEL="$OPTARG"
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
echo -e "${GREEN}Language:${NC} $LANGUAGE"
echo -e "${GREEN}Model:${NC} $MODEL"
echo -e "${GREEN}Speaker:${NC} $SPEAKER"

# Make the request
RESPONSE=$(curl -s -X POST "$BASE_URL/tts" \
    -H "Content-Type: application/json" \
    -d "{
        \"text\": \"$TEXT\",
        \"language\": \"$LANGUAGE\",
        \"model\": \"$MODEL\",
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
    curl -O "$BASE_URL/audio/$FILENAME"

    echo -e "${GREEN}Audio file downloaded: $FILENAME${NC}"
else
    ERROR=$(echo "$RESPONSE" | jq -r '.error')
    echo -e "${RED}Error generating speech:${NC} $ERROR"
    exit 1
fi
