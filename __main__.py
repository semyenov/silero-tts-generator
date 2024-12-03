import logging
import time
from typing import Optional

from silero_tts_processor import SileroTTSProcessor


def main():
    example_text = """
        <speak>
            <p>
                В недрах тундры выдры в гетрах тырят в ведрах +ядра к+едров!
            </p>
            <p>
                <prosody rate="slow">я говорю медленно, а могу</prosody>
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
            speaker_id="xenia",
            output_dir="./tts_outputs",
        )

        audio = tts_processor.generate_speech(
            example_text,
            output_filename=time.strftime("%Y-%m-%d_%H-%M-%S") + ".wav",
        )

        tts_processor.play_audio(audio)

    except Exception as e:
        logging.error(f"TTS processing failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
