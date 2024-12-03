import os
import logging
from typing import Optional, Union

import torch
import soundfile as sf
import sounddevice as sd
import numpy as np
from logmmse import logmmse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SileroTTSProcessor:
    """
    A class to handle text-to-speech conversion using Silero models
    with enhanced configuration and error handling.
    """

    # Predefined language and model configurations
    LANGUAGE_MODELS = {
        "ru": ["v4_ru", "v3_1_ru", "ru_v3"],
        "en": ["v3_en", "lj_v2"],
        "de": ["v3_de", "thorsten_v2"],
        # Add more languages as needed
    }

    SPEAKERS = {
        "ru": ["random", "kseniya", "baya", "aidar", "eugene", "xenia"],
        "en": ["lj", "v3_en"],
        "de": ["thorsten_v2", "v3_de"],
    }

    def __init__(
        self,
        language: str = "ru",
        model_id: Optional[str] = None,
        speaker: Optional[str] = None,
        sample_rate: int = 48000,
    ):
        """
        Initialize the TTS processor with specified parameters.

        :param language: Language of the TTS model
        :param model_id: Specific model ID (optional)
        :param speaker: Speaker voice
        :param sample_rate: Audio sample rate
        """
        # Validate language
        if language not in self.LANGUAGE_MODELS:
            raise ValueError(f"Unsupported language: {language}")

        # Use default model if not specified
        if model_id is None:
            model_id = self.LANGUAGE_MODELS[language][0]

        if speaker is None:
            speaker = self.SPEAKERS[language][0]

        self.language = language
        self.model_id = model_id
        self.speaker = speaker
        self.sample_rate = sample_rate

        # Select device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")

        # Load model
        self._load_model()

    def _load_model(self):
        """
        Load the Silero TTS model with error handling.
        """
        try:
            self.model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                put_accent=True,
                put_yo=True,
                language=self.language,
                speaker=self.model_id,
            )
            self.model.to(self.device)
            logger.info(f"Model loaded: {self.language} - {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate_speech(
        self, text: str, output_path: Optional[str] = None, enhance_noise: bool = True
    ) -> np.ndarray:
        """
        Generate speech from input text with optional noise enhancement.

        :param text: Input text or SSML
        :param output_path: Optional path to save audio
        :param enhance_noise: Whether to apply noise reduction
        :return: Generated audio numpy array
        """
        try:
            # Generate audio
            audio = self.model.apply_tts(
                ssml_text=text, speaker=self.speaker, sample_rate=self.sample_rate
            )

            # Optional noise enhancement
            if enhance_noise:
                audio = logmmse(
                    np.array(audio),
                    self.sample_rate,
                    initial_noise=6,
                    window_size=250,
                    noise_threshold=0.5,
                )

            # Save audio if path provided
            if output_path:
                sf.write(output_path, audio, self.sample_rate)
                logger.info(f"Audio saved to {output_path}")

            return audio

        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            raise

    def play_audio(self, audio: np.ndarray):
        """
        Play generated audio.

        :param audio: Audio numpy array
        """
        try:
            sd.play(audio, self.sample_rate)
            sd.wait()
        except Exception as e:
            logger.error(f"Audio playback failed: {e}")
            raise


def main():
    # Example text with SSML
    example_text = """<speak>
<p>
  В недрах тундры выдры в гетрах тырят в ведрах +ядра к+едров!
  <break strength="x-strong"/>
</p>
<p>
  Когда я просыпаюсь, <prosody rate="slow">я говорю довольно медленно</prosody>.
  <prosody pitch="x-high">А могу говорить тоном выше</prosody> и 
  <prosody pitch="x-low">и довольно низко
    <prosody rate="x-fast">и к тому же  быстро</prosody>
  </prosody>.
</p>
</speak>"""

    try:
        # Create TTS processor
        tts_processor = SileroTTSProcessor(language="ru", speaker="xenia")

        # Generate and play speech
        audio = tts_processor.generate_speech(example_text, output_path="output.wav")
        tts_processor.play_audio(audio)

    except Exception as e:
        logger.error(f"TTS processing failed: {e}")


if __name__ == "__main__":
    main()
