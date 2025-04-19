import base64

def encode_image_to_base64(image_path: str) -> str | None:
    try:
        with open(image_path, "rb") as img_file:
            encoded_bytes = base64.b64encode(img_file.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded_bytes}"
    except Exception as e:
        print(f"❌ Failed to encode image: {e}")
        return None
