import logging
import threading
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TextIteratorStreamer,
)
from config import Config

logger = logging.getLogger(__name__)


class ModelService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                    cls._instance._load_error = None
        return cls._instance

    def initialize(self):
        if self._initialized:
            return

        try:
            logger.info(f"Loading model from: {Config.MODEL_PATH}")

            quantization_config = None
            if Config.USE_4BIT:
                if not torch.cuda.is_available():
                    raise RuntimeError(
                        "4-bit quantization requires CUDA GPU but none detected. "
                        "Set USE_4BIT=false in .env to run on CPU (slower)."
                    )
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
            elif Config.USE_8BIT:
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)

            self.tokenizer = AutoTokenizer.from_pretrained(
                Config.MODEL_PATH,
                trust_remote_code=True,
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model = AutoModelForCausalLM.from_pretrained(
                Config.MODEL_PATH,
                quantization_config=quantization_config,
                device_map=Config.DEVICE if quantization_config else None,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )

            if quantization_config is None:
                self.device = (
                    "cuda" if torch.cuda.is_available() else "cpu"
                ) if Config.DEVICE == "auto" else Config.DEVICE
                self.model = self.model.to(self.device)
            else:
                self.device = "cuda"

            self.model.eval()
            self._initialized = True
            self._load_error = None
            logger.info(f"Model loaded on {self.device}")
        except Exception as e:
            self._load_error = str(e)
            logger.error(f"Model failed to load: {e}", exc_info=True)
            raise

    @property
    def _gen_defaults(self):
        return {
            "max_new_tokens": Config.MAX_NEW_TOKENS,
            "temperature": Config.TEMPERATURE,
            "top_p": Config.TOP_P,
            "repetition_penalty": Config.REPETITION_PENALTY,
            "do_sample": True,
        }

    def generate(self, prompt: str, **kwargs) -> str:
        if not self._initialized:
            raise RuntimeError("Model not initialized.")

        params = {**self._gen_defaults, **kwargs}

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=Config.MAX_CONTEXT,
        ).to(self.device)

        if "min_new_tokens" not in params:
            params["min_new_tokens"] = 50

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                **params,
            )

        new_ids = output_ids[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_ids, skip_special_tokens=True).strip()

    def generate_stream(self, prompt: str, **kwargs):
        if not self._initialized:
            raise RuntimeError("Model not initialized.")

        params = {**self._gen_defaults, **kwargs}

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=Config.MAX_CONTEXT,
        ).to(self.device)

        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )

        gen_kwargs = {
            **inputs,
            "streamer": streamer,
            "pad_token_id": self.tokenizer.eos_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
            **params,
        }

        threading.Thread(
            target=self.model.generate,
            kwargs=gen_kwargs,
            daemon=True,
        ).start()

        for token_text in streamer:
            yield token_text

    @property
    def is_ready(self) -> bool:
        return self._initialized

    @property
    def load_error(self) -> str | None:
        return self._load_error


model_service = ModelService()
