# File: service.py
import base64
import io
import json
from typing import List, Dict, Any
from PIL import Image
from pdf2image import convert_from_bytes
import httpx
from config import settings
from schemas import InvoiceData

def pdf_to_images(file_bytes: bytes) -> List[Image.Image]:
    """
    Converts a PDF file (bytes) into a list of PIL Images.
    """
    try:
        images = convert_from_bytes(file_bytes)
        return images
    except Exception as e:
        raise ValueError(f"Failed to convert PDF to image: {str(e)}")

def encode_image_to_base64(image: Image.Image) -> str:
    """
    Encodes a PIL Image to a base64 string.
    """
    buffered = io.BytesIO()
    image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

async def process_invoice_with_vllm(image: Image.Image) -> InvoiceData:
    """
    Sends the image to VLLM and validates the response using Pydantic.
    """
    base64_image = encode_image_to_base64(image)
    
    # Get the dynamic prompt with Pydantic schema
    system_prompt = settings.get_system_prompt()
    
    payload = {
        "model": settings.MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": system_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 2048,
        "temperature": 0.1 
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{settings.VLLM_API_URL}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            
            # Cleanup Markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.replace("```", "").strip()
            
            # 1. Parse JSON
            try:
                raw_json = json.loads(content)
            except json.JSONDecodeError:
                raise ValueError(f"Model did not return valid JSON: {content}")

            # 2. Validate with Pydantic
            validated_data = InvoiceData.model_validate(raw_json)
            
            return validated_data
            
        except httpx.RequestError as e:
            raise RuntimeError(f"API Request failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Processing error: {str(e)}")