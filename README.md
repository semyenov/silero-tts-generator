# Silero TTS Text-to-Speech Generator

## Overview

A Python-based text-to-speech generator using the Silero TTS models, supporting multiple languages and advanced SSML features.

## Features

- Multiple language support (Russian, English, German)
- SSML text processing
- Noise reduction
- GPU/CPU compatibility
- Flexible speaker selection

## Prerequisites

- Python 3.8+
- CUDA (optional, for GPU acceleration)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/semyenov/silero-tts-generator.git
cd silero-tts-generator
```

2. Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```python
from __main__ import SileroTTSProcessor

# Create TTS processor
tts = SileroTTSProcessor(language="ru", speaker="xenia")

# Generate speech
audio = tts.generate_speech(
    "<speak>Привет, мир!</speak>",
    output_path="output.wav"
)
tts.play_audio(audio)
```

## Supported Languages

- Russian
- English
- German

## Troubleshooting

- Ensure you have the latest version of PyTorch
- Check CUDA compatibility if using GPU
- Verify audio device settings

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first.
