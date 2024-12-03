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
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SileroTTSProcessor:
    """
    A class to handle text-to-speech conversion using Silero models
    with enhanced configuration and error handling.
    """

    # Predefined language and model configurations
    LANGUAGE_MODELS = {
        "ru": {
            "v4_ru": ["random", "kseniya", "baya", "aidar", "eugene", "xenia"],
            "v3_1_ru": ["random", "kseniya", "baya", "aidar", "eugene", "xenia"],
            "ru_v3": ["random", "kseniya", "baya", "aidar", "eugene", "xenia"],
        },
        "en": ["v3_en", "lj_v2"],
        "de": ["v3_de", "thorsten_v2"],
        # Add more languages as needed
    }

    def __init__(
        self,
        language_id: str = "ru",
        model_id: Optional[str] = None,
        speaker_id: Optional[str] = None,
        sample_rate: int = 48000,
    ):
        """
        Initialize the TTS processor with specified parameters.

        :param language_id: Language of the TTS model
        :param model_id: Specific model ID (optional)
        :param speaker_id: Speaker voice
        :param sample_rate: Audio sample rate
        """
        # Validate language
        if language_id not in self.LANGUAGE_MODELS.keys():
            raise ValueError(f"Unsupported language: {language_id}")

        # Use default model if not specified
        if model_id is None:
            model_id = list(self.LANGUAGE_MODELS[language_id].keys())[0]

        if model_id not in self.LANGUAGE_MODELS[language_id].keys():
            raise ValueError(f"Unsupported model: {model_id}")

        # Use default speaker if not specified
        if speaker_id is None:
            speaker_id = list(self.LANGUAGE_MODELS[language_id][model_id])[0]

        if speaker_id not in self.LANGUAGE_MODELS[language_id][model_id]:
            raise ValueError(f"Unsupported speaker: {speaker_id}")

        self.language_id = language_id
        self.model_id = model_id
        self.speaker_id = speaker_id
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
                language=self.language_id,
                speaker=self.model_id,
            )
            self.model.to(self.device)
            logger.info(
                f"Model loaded: {self.language_id} - {self.model_id} - {self.speaker_id}"
            )
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate_speech(
        self,
        text: str,
        output_path: Optional[str] = None,
        enhance_noise: bool = True,
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
                ssml_text=text,
                speaker=self.speaker_id,
                sample_rate=self.sample_rate,
            )

            # Optional noise enhancement
            if enhance_noise:
                audio = logmmse(
                    np.asarray(audio),
                    self.sample_rate,
                    initial_noise=1,
                    window_size=150,
                    noise_threshold=0.25,
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
    example_text = """
    <speak>
        <p>
            В недрах тундры выдры в гетрах тырят в ведрах +ядра к+едров!
        </p>
        <p>
            Когда я просыпаюсь, 
            <prosody rate="slow">я говорю довольно</prosody>
            <prosody rate="x-slow">медленно</prosody>.
            <prosody pitch="x-high">А могу говорить тоном выше</prosody> и 
            <prosody pitch="x-low">
                <s>и низким тоном</s>
                <prosody rate="x-fast">и очень быстро тоже могу</prosody>
            </prosody>
        </p>
    </speak>
    """

    try:
        # Create TTS processor
        tts_processor = SileroTTSProcessor(
            language_id="ru",
            model_id="v4_ru",
            speaker_id="xenia",
        )

        # Generate speech
        audio = tts_processor.generate_speech(
            example_text,
            output_path="output.wav",
        )

        # Play audio
        tts_processor.play_audio(audio)

    except Exception as e:
        logger.error(f"TTS processing failed: {e}")


if __name__ == "__main__":
    main()
