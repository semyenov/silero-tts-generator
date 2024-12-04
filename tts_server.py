import os
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any

import soundfile as sf
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.options

from silero_tts_processor import SileroTTSProcessor

# Configure logging with more robust configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("tts_server.log", encoding="utf-8", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


# Use environment variables with type conversion and default values
class Config:
    PORT: int = int(os.getenv("PORT", 8765))
    LANGUAGE_ID: str = os.getenv("LANGUAGE_ID", "ru")
    MODEL_ID: str = os.getenv("MODEL_ID", "v4_ru")
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "tts_outputs")).resolve()

    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {cls.OUTPUT_DIR}")


class BaseHandler(tornado.web.RequestHandler):
    """Base handler with enhanced error handling and CORS support"""

    def set_default_headers(self) -> None:
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        """
        Enhanced error handler to return structured JSON errors

        Args:
            status_code (int): HTTP status code
            kwargs (dict): Additional error information
        """
        error_message = self._get_error_message(kwargs)

        error_response = {
            "success": False,
            "status_code": status_code,
            "error": error_message,
        }

        self.set_status(status_code)
        self.write(json.dumps(error_response))
        self.finish()

    def _get_error_message(self, kwargs: Dict[str, Any]) -> str:
        """Extract error message from exception"""
        if "exc_info" in kwargs:
            return str(kwargs["exc_info"][1])
        return self.settings.get("message", "Unknown error")


class TTSHandler(BaseHandler):
    def options(self) -> None:
        """Handle CORS preflight requests"""
        self.set_status(204)
        self.finish()

    def post(self) -> None:
        """
        Handle TTS generation request

        Expected JSON payload:
        {
            "text": str (required),
            "speaker": str (optional, default="xenia"),
            "enhance_noise": bool (optional, default=True)
        }
        """
        try:
            data = self._parse_request_data()
            filename = self._generate_speech(data)
            self._send_success_response(filename)
        except ValueError as ve:
            self._handle_validation_error(ve)
        except Exception as e:
            self._handle_generation_error(e)

    def _parse_request_data(self) -> Dict[str, Any]:
        """Parse and validate request data"""
        data = json.loads(self.request.body)
        text = data.get("text", "").strip()

        if not text:
            raise ValueError("Text is required and cannot be empty")

        return {
            "text": text,
            "speaker": data.get("speaker", "xenia"),
            "enhance_noise": data.get("enhance_noise", True),
        }

    def _generate_speech(self, data: Dict[str, Any]) -> str:
        """Generate speech and return filename"""
        filename = f"{uuid.uuid4()}.wav"

        audio = tts_processor.generate_speech(
            data["text"],
            speaker_id=data["speaker"],
            enhance_noise=data["enhance_noise"],
            output_filename=filename,
        )

        return filename

    def _send_success_response(self, filename: str) -> None:
        """Send successful TTS generation response"""
        response = {
            "success": True,
            "filename": filename,
        }
        self.write(json.dumps(response))
        self.set_status(200)

    def _handle_validation_error(self, error: ValueError) -> None:
        """Handle input validation errors"""
        logger.error(f"Validation Error: {error}")
        self.set_status(400)
        self.write(json.dumps({"success": False, "error": str(error)}))

    def _handle_generation_error(self, error: Exception) -> None:
        """Handle TTS generation errors"""
        logger.error(f"TTS Generation Error: {error}")
        self.set_status(500)
        self.write(json.dumps({"success": False, "error": str(error)}))


class AudioFileHandler(BaseHandler):
    def get(self, filename: str) -> None:
        """
        Serve audio file by filename

        Args:
            filename (str): Name of the audio file to serve
        """
        try:
            filepath = self._validate_file(filename)
            self._serve_audio_file(filepath, filename)
        except FileNotFoundError as fnf:
            self._handle_file_not_found(fnf)
        except Exception as e:
            self._handle_serving_error(e)

    def _validate_file(self, filename: str) -> Path:
        """Validate and return file path"""
        filepath = Config.OUTPUT_DIR / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Audio file {filename} not found")

        return filepath

    def _serve_audio_file(self, filepath: Path, filename: str) -> None:
        """Set headers and serve audio file"""
        self.set_header("Content-Type", "audio/wav")
        self.set_header("Content-Disposition", f"attachment; filename={filename}")

        with open(filepath, "rb") as f:
            self.write(f.read())
        self.finish()

    def _handle_file_not_found(self, error: FileNotFoundError) -> None:
        """Handle file not found errors"""
        logger.error(f"File Not Found: {error}")
        self.set_status(404)
        self.write(json.dumps({"success": False, "error": str(error)}))

    def _handle_serving_error(self, error: Exception) -> None:
        """Handle audio file serving errors"""
        logger.error(f"Audio File Serving Error: {error}")
        self.set_status(500)
        self.write(json.dumps({"success": False, "error": str(error)}))


class IndexHandler(tornado.web.RequestHandler):
    """Handler to serve the index.html file"""

    def get(self):
        """Serve the index.html file"""
        self.render("./static/index.html")


def make_app() -> tornado.web.Application:
    """Create Tornado web application"""
    return tornado.web.Application(
        [
            (r"/", IndexHandler),
            (r"/tts", TTSHandler),
            (r"/audio/([^/]+)", AudioFileHandler),
        ],
        debug=True,
        default_handler_class=BaseHandler,
    )


def main() -> None:
    """Main server startup method"""
    # Validate configuration before starting
    Config.validate()

    # Create TTS processor with configuration
    global tts_processor
    tts_processor = SileroTTSProcessor(
        language_id=Config.LANGUAGE_ID,
        model_id=Config.MODEL_ID,
        output_dir=Config.OUTPUT_DIR,
    )

    # Create application and server
    app = make_app()
    server = tornado.httpserver.HTTPServer(app)

    try:
        server.listen(Config.PORT)
        logger.info(f"TTS Server running on http://localhost:{Config.PORT}")
        tornado.ioloop.IOLoop.current().start()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
