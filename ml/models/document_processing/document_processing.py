import pytesseract
import spacy
from PIL import Image


class DocumentProcessor:
    def __init__(self):
        # Load a pre-trained spaCy model for entity recognition
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model 'en_core_web_sm'...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def extract_text_from_image(self, image_path):
        try:
            text = pytesseract.image_to_string(Image.open(image_path))
            return text
        except Exception as e:
            print(f"Error during OCR: {e}")
            return None

    def analyze_text(self, text):
        if text is None:
            return {"entities": [], "summary": ""}

        doc = self.nlp(text)
        entities = [
            {
                "text": ent.text,
                "label": ent.label_,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
            }
            for ent in doc.ents
        ]

        # Simple summarization (first few sentences)
        sentences = [sent.text for sent in doc.sents]
        summary = " ".join(sentences[:3]) if sentences else ""

        return {"entities": entities, "summary": summary}


if __name__ == "__main__":
    # Example Usage:
    processor = DocumentProcessor()

    # For demonstration, let's create a dummy image file
    # In a real scenario, you would have actual image files (e.g., scanned invoices)
    try:
        from PIL import Image, ImageDraw, ImageFont

        img_path = "/tmp/dummy_invoice.png"
        img = Image.new("RGB", (600, 200), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        try:
            fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", 20)
        except IOError:
            fnt = ImageFont.load_default()
        d.text(
            (10, 10),
            "Invoice #12345\nDate: 2023-01-01\nAmount: $1500.00\nFrom: ABC Corp",
            fill=(0, 0, 0),
            font=fnt,
        )
        img.save(img_path)

        print(f"Dummy image saved to {img_path}")

        extracted_text = processor.extract_text_from_image(img_path)
        print("\nExtracted Text:\n", extracted_text)

        analysis_results = processor.analyze_text(extracted_text)
        print("\nAnalysis Results:\n", analysis_results)

    except ImportError:
        print("Pillow not installed. Cannot create dummy image for demonstration.")
        print("Please install Pillow (pip install Pillow) to run the example.")
    except Exception as e:
        print(f"An error occurred during example execution: {e}")

    # Clean up dummy image
    import os

    if os.path.exists(img_path):
        os.remove(img_path)
        print(f"Cleaned up dummy image {img_path}")
