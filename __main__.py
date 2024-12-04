import logging
import time

import numpy as np
import sounddevice as sd

from silero_tts_processor import SileroTTSProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("tts_server.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def play_audio(audio: np.ndarray, sample_rate: int):
    """
    Play generated audio with timeout and error handling.

    :param audio: Audio numpy array
    :param sample_rate: Sample rate
    """
    try:
        sd.play(audio, sample_rate)
        sd.wait()
    except sd.CallbackStop:
        logger.warning("Audio playback interrupted")
    except Exception as e:
        logger.error(f"Audio playback failed: {e}")
        raise


def main():
    example_text = """
        <speak>
            <p>
                В недрах тундры выдры в гетрах тырят в ведрах +ядра к+едров!
            </p>
            <p>
                <prosody rate="slow">Сейчас я говорю медленно, а могу</prosody>
                <prosody rate="x-slow">ещё медленнее</prosody>.
                <break time="500ms"/>
                <prosody pitch="x-high">ещё я могу говорить тоном выше</prosody>
                <break time="500ms"/>
                <prosody pitch="x-low">и низким тоном</prosody>
                <break time="500ms"/>
                <prosody rate="x-fast" pitch="x-low">и очень быстро тоже могу</prosody>
            </p>
        </speak>
    """

    try:
        tts_processor = SileroTTSProcessor(
            language_id="ru",
            model_id="v4_ru",
            output_dir="./tts_outputs",
        )

        audio = tts_processor.generate_speech(
            example_text,
            speaker_id="xenia",
            enhance_noise=True,
            output_filename=time.strftime("%Y-%m-%d_%H-%M-%S") + ".wav",
        )

        play_audio(audio, tts_processor.sample_rate)

    except Exception as e:
        logging.error(f"TTS processing failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
