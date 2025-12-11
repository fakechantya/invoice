# File: config.py
import os
import json
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from schemas import InvoiceData

load_dotenv()

# --- Application Settings ---

class Settings(BaseSettings):
    # API Config
    VLLM_API_URL: str = os.getenv("VLLM_API_URL", "http://localhost:8000/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "Qwen/Qwen3-VL-4B-Instruct")
    
    # Database Config
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "invoice_db")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_system_prompt(self) -> str:
        """
        Dynamically generates the system prompt using the Pydantic model's JSON schema.
        """
        # We now import InvoiceData from schemas.py
        schema_json = json.dumps(InvoiceData.model_json_schema(), indent=2)
        
        return f"""Analyze the provided invoice image and extract all relevant information.

Structure your output only as a valid JSON object that strictly adheres to the following schema.
If a specific field or value is not present in the image, use null as the value for that field (do not omit the key).
Do not include any text, explanations, or markdown formatting.

JSON Schema:
{schema_json}
"""

    class Config:
        env_file = ".env"

settings = Settings()