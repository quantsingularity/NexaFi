import unittest
import os
from PIL import Image, ImageDraw, ImageFont
from NexaFi.ml.models.document_processing.document_processing import DocumentProcessor

class TestDocumentProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = DocumentProcessor()
        self.dummy_image_path = "/tmp/test_dummy_doc.png"
        # Create a dummy image for testing
        img = Image.new("RGB", (600, 200), color = (255, 255, 255))
        d = ImageDraw.Draw(img)
        try:
            fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", 20)
        except IOError:
            fnt = ImageFont.load_default()
        d.text((10,10), "This is a test document.\nIt contains some text for OCR.", fill=(0,0,0), font=fnt)
        img.save(self.dummy_image_path)

    def tearDown(self):
        # Clean up the dummy image after tests
        if os.path.exists(self.dummy_image_path):
            os.remove(self.dummy_image_path)

    def test_extract_text_from_image(self):
        extracted_text = self.processor.extract_text_from_image(self.dummy_image_path)
        self.assertIsNotNone(extracted_text)
        self.assertIn("test", extracted_text.lower())
        self.assertIn("document", extracted_text.lower())
        self.assertIn("ocr", extracted_text.lower())

    def test_analyze_text(self):
        text = "Apple Inc. is an American multinational technology company. It was founded by Steve Jobs."
        analysis_results = self.processor.analyze_text(text)
        self.assertIn("entities", analysis_results)
        self.assertGreater(len(analysis_results["entities"]), 0)
        self.assertIn("summary", analysis_results)
        self.assertGreater(len(analysis_results["summary"]), 0)

    def test_analyze_empty_text(self):
        text = ""
        analysis_results = self.processor.analyze_text(text)
        self.assertEqual(len(analysis_results["entities"]), 0)
        self.assertEqual(analysis_results["summary"], "")

if __name__ == '__main__':
    unittest.main()


