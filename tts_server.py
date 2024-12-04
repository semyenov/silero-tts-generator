import os
import json
import logging
import uuid
from pathlib import Path

import tornado.ioloop
import tornado.web
import traceback

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

LANGUAGE_ID = "ru"
MODEL_ID = "v4_ru"
AUDIO_OUTPUT_DIR = Path(os.path.join(os.getcwd(), "tts_outputs"))

# Global TTS Processor
tts_processor = SileroTTSProcessor(
    language_id=LANGUAGE_ID,
    model_id=MODEL_ID,
    output_dir=AUDIO_OUTPUT_DIR,
)


class BaseHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        """
        Override Tornado's default error handler to return JSON
        """
        self.set_header("Content-Type", "application/json")

        # Get the error details
        error_message = self.settings.get("message", "")

        # If an exception was raised, include its details
        if "exc_info" in kwargs:
            error_message = str(kwargs["exc_info"][1])
            # Optionally include traceback for debugging
            # error_trace = traceback.format_exception(*kwargs['exc_info'])

        # Construct error response
        error_response = {
            "success": False,
            "status_code": status_code,
            "error": error_message,
        }

        # Write the JSON error response
        self.set_status(status_code)
        self.write(json.dumps(error_response))
        self.finish()


class TTSHandler(BaseHandler):
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
            speaker = data.get("speaker", "xenia")
            enhance_noise = data.get("enhance_noise", True)

            # Validate input
            if not text:
                raise ValueError("Text is required")

            # Generate unique filename
            filename = f"{uuid.uuid4()}.wav"

            # Generate speech
            audio = tts_processor.generate_speech(
                text,
                speaker_id=speaker,
                enhance_noise=enhance_noise,
                output_filename=filename,
            )

            # Respond with file details
            self.write(
                json.dumps(
                    {
                        "success": True,
                        "filename": filename,
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
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

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
        ],
        debug=True,
        default_handler_class=BaseHandler,
    )


def main():
    app = make_app()
    port = 8765
    app.listen(port)
    logger.info(f"TTS Server running on http://localhost:{port}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
