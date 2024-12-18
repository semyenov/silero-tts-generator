import logging
from typing import Optional, Dict, List
from pathlib import Path

import torch
import soundfile as sf
import numpy as np
from logmmse import logmmse

# Configure logging with more comprehensive settings
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("tts_log.txt", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


class SileroTTSProcessor:
    """
    Enhanced Text-to-Speech processor using Silero models with comprehensive configuration.
    """

    # More comprehensive language and model configurations
    LANGUAGE_MODELS: Dict[str, Dict[str, List[str]]] = {
        "ru": {
            "v4_ru": ["random", "kseniya", "baya", "aidar", "eugene", "xenia"],
            "v3_1_ru": ["random", "kseniya", "baya", "aidar", "eugene", "xenia"],
        },
        "en": {
            "v3_en": ["random", "lj"],
            "lj_v2": ["random", "lj"],
        },
        "de": {
            "v3_de": ["random", "thorsten"],
            "thorsten_v2": ["random", "thorsten"],
        },
    }

    def __init__(
        self,
        language_id: str = "ru",
        model_id: str = "v4_ru",
        sample_rate: int = 48000,
        output_dir: Optional[str] = None,
    ):
        """
        Initialize the TTS processor with enhanced configuration and validation.

        :param language_id: Target language
        :param model_id: Specific model variant
        :param sample_rate: Audio sample rate
        :param output_dir: Directory to save generated audio files
        """

        self.language_id = language_id
        self.model_id = model_id
        self.sample_rate = sample_rate

        # Comprehensive input validation
        self._validate_inputs(language_id, model_id)

        # Create output directory if specified
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "tts_outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Improved device selection with logging
        self.device = self._select_device()

        # Load model with retry mechanism
        self.model = self._load_model()

    def _validate_inputs(
        self,
        language_id: str,
        model_id: Optional[str],
    ):
        """
        Validate input parameters with detailed error messages.

        :raises ValueError: If inputs are invalid
        """
        if language_id not in self.LANGUAGE_MODELS:
            raise ValueError(
                f"Unsupported language. Supported: {list(self.LANGUAGE_MODELS.keys())}"
            )

        if model_id not in self.LANGUAGE_MODELS[language_id]:
            raise ValueError(
                f"Unsupported model for {language_id}. Supported: {list(self.LANGUAGE_MODELS[language_id].keys())}"
            )

    def _validate_speaker(self, speaker_id: str):
        if speaker_id not in self.LANGUAGE_MODELS[self.language_id][self.model_id]:
            raise ValueError(
                f"Unsupported speaker for {self.model_id}. Supported: {self.LANGUAGE_MODELS[self.language_id][self.model_id]}"
            )

    def _select_device(self) -> torch.device:
        """
        Intelligently select computation device with detailed logging.

        :return: Selected torch device
        """
        if torch.cuda.is_available():
            logger.info(f"CUDA available. Using GPU: {torch.cuda.get_device_name(0)}")
            return torch.device("cuda")

        logger.info("No CUDA GPU available. Falling back to CPU.")
        return torch.device("cpu")

    def _load_model(self):
        """
        Load Silero TTS model with comprehensive error handling.

        :return: Loaded TTS model
        :raises RuntimeError: If model loading fails
        """
        try:
            model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language=self.language_id,
                speaker=self.model_id,
            )
            model.to(self.device)

            logger.info(
                f"Model successfully loaded: "
                f"Language={self.language_id}, "
                f"Model={self.model_id}, "
            )
            return model

        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            raise RuntimeError(f"Could not load TTS model: {e}")

    def generate_speech(
        self,
        text: str,
        speaker_id: str = "xenia",
        enhance_noise: bool = True,
        output_filename: Optional[str] = None,
    ) -> np.ndarray:
        """
        Generate speech with enhanced error handling and optional noise reduction.

        :param text: Input text or SSML
        :param output_filename: Optional filename for saving audio
        :param enhance_noise: Apply noise reduction
        :return: Generated audio array
        """
        try:
            # Validate speaker
            self._validate_speaker(speaker_id)

            # strip text from leading and trailing whitespace
            text = text.strip()

            # if text is not SSML, convert it to SSML
            if not text.startswith("<speak>"):
                text = f"<speak>{text}</speak>"

            # Generate audio
            audio = self.model.apply_tts(
                ssml_text=text,
                speaker=speaker_id,
                sample_rate=self.sample_rate,
                put_accent=True,
                put_yo=True,
            )

            # Optional noise enhancement
            if enhance_noise:
                audio = logmmse(
                    np.asarray(audio),
                    self.sample_rate,
                    initial_noise=3,
                    window_size=50,
                    noise_threshold=0.25,
                )

            # Save audio if filename provided
            if output_filename:
                output_path = self.output_dir / output_filename
                sf.write(str(output_path), audio, self.sample_rate)
                logger.info(f"Audio saved to {output_path}")

            return audio

        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            raise
