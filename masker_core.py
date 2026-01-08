import re
from rapidocr_onnxruntime import RapidOCR
from PIL import Image, ImageDraw
import numpy as np

class PrivacyMasker:
    def __init__(self):
        # Initialize RapidOCR
        # det_use_gpu=False, cls_use_gpu=False, rec_use_gpu=False ensure compatibility
        self.ocr_engine = RapidOCR(det_use_gpu=False, cls_use_gpu=False, rec_use_gpu=False)
        
        # Compile Regex Patterns
        self.patterns = {
            'phone': re.compile(r'(\d{2,4}-\d{2,4}-\d{3,4})|(\d{3}-\d{4}-\d{4})'),
            'postal_code': re.compile(r'〒?\d{3}-\d{4}'),
            'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            'credit_card': re.compile(r'(?:\d{4}[-\s]?){3}\d{4}'), # 16 digits
            'address_keyword': re.compile(r'(住所|所在地|Add\.|Address)[:：]\s*(.*)'),
            'name_keyword': re.compile(r'(氏名|名前|Name)[:：]\s*(.*)')
        }

        self.custom_keywords = []
        self.user_patterns = []
        self.load_user_rules()

    def load_user_rules(self):
        """
        Dynamically load or reload user_rules.py
        """
        try:
            import user_rules
            import importlib
            importlib.reload(user_rules)
            self.user_patterns = getattr(user_rules, "USER_PATTERNS", [])
            print(f"Loaded {len(self.user_patterns)} advanced rules from user_rules.py")
        except Exception as e:
            print(f"No user_rules.py found or error loading: {e}")
            self.user_patterns = []

    def set_custom_keywords(self, keywords: list[str]):
        """
        Set a list of custom keywords and convert them to space-flexible regex patterns.
        Example: 'ABC' -> 'A\s*B\s*C'
        """
        self.custom_keywords = []
        for kw in keywords:
            if not kw: continue
            # Escape special regex characters in the keyword
            escaped_kw = re.escape(kw)
            # Insert \s* between every character to handle OCR spaces
            # We only do this for characters to keep it simple
            pattern_str = r'\s*'.join(list(kw))
            try:
                self.custom_keywords.append(re.compile(pattern_str, re.IGNORECASE))
            except Exception as e:
                print(f"Error compiling keyword pattern {kw}: {e}")

    def mask_privacy(self, image: Image.Image) -> Image.Image:
        """
        Takes a PIL Image, detects PII using OCR, and returns a masked PIL Image.
        """
        # Convert PIL Image to numpy array (RGB) for RapidOCR
        img_np = np.array(image)
        
        # Run OCR
        # result is a list of [box, text, score]
        # box is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        ocr_result, _ = self.ocr_engine(img_np)
        
        if not ocr_result:
            return image

        # Create a drawing context
        masked_image = image.copy()
        draw = ImageDraw.Draw(masked_image)

        for item in ocr_result:
            box, text, score = item
            
            if self._is_sensitive(text):
                self._draw_mask(draw, box)

        return masked_image

    def _is_sensitive(self, text: str) -> bool:
        """
        Check if the text contains sensitive information.
        """
        # 0. Check Custom Keywords (now compiled regex patterns)
        for pattern in self.custom_keywords:
            if pattern.search(text):
                return True
        
        # 0.5 Check Advanced User Rules (Regex)
        for pattern in self.user_patterns:
            if pattern.search(text):
                return True

        # 1. Check direct Regex matches
        for key, pattern in self.patterns.items():
            if pattern.search(text):
                return True
        
        # 2. Check for simple keyword contexts (very basic)
        # If the text itself looks like a specific value without context, it might be hard
        # But for now, we rely on the regexes above.
        
        # Additional cleanup detection?
        # Maybe check if text is purely numbers and long enough? (Might be risky)
        
        return False

    def _draw_mask(self, draw, box):
        """
        Draw a black rectangle over the detected box.
        box is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        """
        # Determine bounding rectangle
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        
        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)
        
        # Draw black rectangle
        draw.rectangle([min_x, min_y, max_x, max_y], fill="black", outline="black")

