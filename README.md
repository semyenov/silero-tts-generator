# Silero TTS Text-to-Speech Generator

## Overview

A Python-based text-to-speech generator using the Silero TTS models, supporting
multiple languages and advanced features:

- Multiple language support (Russian, English, German)
- SSML text processing
- Noise reduction
- GPU/CPU compatibility
- Flexible speaker selection
- Tornado-based API server for remote TTS generation

## Project Structure

- `__main__.py`: Example script demonstrating local TTS usage
- `silero_tts_processor.py`: Core TTS processor class
- `tts_server.py`: Tornado-based API server for remote TTS generation
- `test_request.sh`: Bash script for testing the TTS API
- `requirements.txt`: Project dependencies

## Prerequisites

- Python 3.8+
- CUDA (optional, for GPU acceleration)
- `curl` for API testing (optional, used in test script)
- `jq` for JSON parsing (optional, used in test script)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/semyenov/silero-tts-generator.git
cd silero-tts-generator
```

2. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Local Usage

```python
from silero_tts_processor import SileroTTSProcessor

# Create TTS processor
tts = SileroTTSProcessor(
    language_id="ru",
    model_id="v4_ru",
)

# Generate speech
audio = tts.generate_speech(
    "<speak>Привет, мир</speak>",
    speaker_id="xenia",
    enhance_noise=True,
    output_filename="output.wav"
)
tts.play_audio(audio)
```

## API Server Usage

Start the Tornado API server:

```bash
python tts_server.py
```

### API Testing with Bash Script

A convenient bash script `test_request.sh` is provided to test the TTS API:

```bash
# Basic usage
./test_request.sh -t "Привет, мир"

# Advanced usage with custom parameters
./test_request.sh \
    -t "<speak>Привет, мир</speak>" \
    -s xenia
```

Script options:

- `-t`: Text to convert to speech (required)
- `-s`: Speaker (default: xenia)
- `-h`: Show help message

### API Endpoints

#### Generate TTS

`POST /tts`

Request Body:

```json
{
  "text": "<speak>Текст для синтеза речи</speak>",
  "speaker": "xenia",
  "enhance_noise": true
}
```

Response:

```json
{
  "success": true,
  "filename": "generated_audio_file.wav"
}
```

#### Retrieve Audio File

`GET /audio/{filename}`

Retrieves the generated audio file.

## Supported Languages

- Russian
- English
- German
- ...

Full list of supported languages and models
can be found [here](https://raw.githubusercontent.com/snakers4/silero-models/refs/heads/master/models.yml).

## Troubleshooting

- Ensure you have the latest version of PyTorch
- Check CUDA compatibility if using GPU
- Verify audio device settings
- Make sure `curl` and `jq` are installed for API testing

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first.
