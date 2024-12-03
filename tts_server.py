import os
import json
import logging
import uuid
import tornado.ioloop
import tornado.web

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

# Create output directory for audio files
AUDIO_OUTPUT_DIR = os.path.join(os.getcwd(), "tts_outputs")
os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)

# Global TTS Processor
tts_processor = SileroTTSProcessor(
    language_id="ru",  # Default language
    model_id="v4_ru",  # Default model
    speaker_id="xenia",  # Default speaker
    output_dir=AUDIO_OUTPUT_DIR,
)


class TTSHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def options(self):
        # Preflight request for CORS
        self.set_status(204)
        self.finish()

    def post(self):
        try:
            # Parse request body
            data = json.loads(self.request.body)
            text = data.get("text", "")
            language = data.get("language", "ru")
            model = data.get("model", "v4_ru")
            speaker = data.get("speaker", "xenia")
            enhance_noise = data.get("enhance_noise", True)

            # Validate input
            if not text:
                raise ValueError("Text is required")

            # Update TTS processor configuration if needed
            if (
                language != tts_processor.language_id
                or model != tts_processor.model_id
                or speaker != tts_processor.speaker_id
            ):
                tts_processor._validate_inputs(language, model, speaker)
                tts_processor.language_id = language
                tts_processor.model_id = model
                tts_processor.speaker_id = speaker
                tts_processor.model = tts_processor._load_model()

            # Generate unique filename
            filename = f"{uuid.uuid4()}.wav"
            full_path = os.path.join(AUDIO_OUTPUT_DIR, filename)

            # Generate speech
            audio = tts_processor.generate_speech(
                text,
                output_filename=filename,
                enhance_noise=enhance_noise,
            )

            # Respond with file details
            self.write(
                json.dumps(
                    {
                        "success": True,
                        "filename": filename,
                        "path": full_path,
                        "duration": len(audio) / tts_processor.sample_rate,
                    }
                )
            )
            self.set_status(200)

        except ValueError as ve:
            logger.error(f"Validation Error: {ve}")
            self.set_status(400)
            self.write(json.dumps({"success": False, "error": str(ve)}))
        except Exception as e:
            logger.error(f"TTS Generation Error: {e}")
            self.set_status(500)
            self.write(json.dumps({"success": False, "error": str(e)}))


class AudioFileHandler(tornado.web.RequestHandler):
    def get(self, filename):
        try:
            filepath = os.path.join(AUDIO_OUTPUT_DIR, filename)

            # Check if file exists
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Audio file {filename} not found")

            # Set headers for audio file
            self.set_header("Content-Type", "audio/wav")
            self.set_header("Content-Disposition", f"attachment; filename={filename}")

            # Write file contents
            with open(filepath, "rb") as f:
                self.write(f.read())
            self.finish()

        except FileNotFoundError as fnf:
            logger.error(f"File Not Found: {fnf}")
            self.set_status(404)
            self.write(json.dumps({"success": False, "error": str(fnf)}))
        except Exception as e:
            logger.error(f"Audio File Serving Error: {e}")
            self.set_status(500)
            self.write(json.dumps({"success": False, "error": str(e)}))


def make_app():
    return tornado.web.Application(
        [
            (r"/tts", TTSHandler),
            (r"/audio/([^/]+)", AudioFileHandler),
        ]
    )


def main():
    app = make_app()
    port = 8765
    app.listen(port)
    logger.info(f"TTS Server running on http://localhost:{port}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
