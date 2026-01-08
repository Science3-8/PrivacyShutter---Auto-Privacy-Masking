import customtkinter as ctk
from PIL import Image, ImageTk
# import tkinter as tk
from tkinter import filedialog
import os
import sys

# Add current directory to path just in case
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from masker_core import PrivacyMasker

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PrivacyShutter - Auto Privacy Masking")
        self.geometry("1000x700")

        # Layout configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="PrivacyShutter", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_screenshot = ctk.CTkButton(self.sidebar_frame, text="Take Screenshot", command=self.take_screenshot)
        self.btn_screenshot.grid(row=1, column=0, padx=20, pady=10)

        self.btn_load_image = ctk.CTkButton(self.sidebar_frame, text="Load Image", command=self.load_image)
        self.btn_load_image.grid(row=2, column=0, padx=20, pady=10)

        self.btn_save = ctk.CTkButton(self.sidebar_frame, text="Save Image", fg_color="green", hover_color="darkgreen", command=self.save_image)
        self.btn_save.grid(row=3, column=0, padx=20, pady=10)
        self.btn_save.configure(state="disabled")

        # Custom Keywords Section
        self.lbl_keywords = ctk.CTkLabel(self.sidebar_frame, text="Custom Keywords:", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.lbl_keywords.grid(row=5, column=0, padx=20, pady=(20, 5), sticky="w")

        # Input Area (Entry + Add Button)
        self.input_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.input_frame.grid(row=6, column=0, padx=10, pady=(0, 5), sticky="ew")
        
        self.entry_keyword = ctk.CTkEntry(self.input_frame, placeholder_text="New keyword")
        self.entry_keyword.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_add_keyword = ctk.CTkButton(self.input_frame, text="+", width=30, command=self.add_keyword)
        self.btn_add_keyword.pack(side="right")

        # List Area
        self.keyword_list_frame = ctk.CTkScrollableFrame(self.sidebar_frame, height=150, label_text="Registered Words")
        self.keyword_list_frame.grid(row=7, column=0, padx=10, pady=5, sticky="ew")

        # Advanced Rules Section
        self.btn_reload_rules = ctk.CTkButton(self.sidebar_frame, text="Advanced Rules Editor", fg_color="gray", hover_color="dimgray", command=self.reload_advanced_rules)
        self.btn_reload_rules.grid(row=8, column=0, padx=20, pady=10)

        # Removed old logic, using real-time update instead
        # self.btn_apply_custom = ctk.CTkButton...  <-- No longer needed as we update on add/remove

        # Main Area
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.image_label = ctk.CTkLabel(self.main_frame, text="No image loaded.\nClick 'Take Screenshot' or 'Load Image' to start.")
        self.image_label.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # State
        self.original_image = None
        self.current_image = None
        self.masker = PrivacyMasker()
        self.keywords = []
        self.keyword_file = "keywords.json"

        # Initialize Keywords
        self.load_keywords()
        self.refresh_keyword_list()

    def load_keywords(self):
        import json
        if os.path.exists(self.keyword_file):
            try:
                with open(self.keyword_file, "r", encoding="utf-8") as f:
                    self.keywords = json.load(f)
                self.masker.set_custom_keywords(self.keywords)
            except Exception as e:
                print(f"Error loading keywords: {e}")

    def save_keywords(self):
        import json
        try:
            with open(self.keyword_file, "w", encoding="utf-8") as f:
                json.dump(self.keywords, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving keywords: {e}")

    def add_keyword(self):
        keyword = self.entry_keyword.get().strip()
        if keyword and keyword not in self.keywords:
            self.keywords.append(keyword)
            self.save_keywords()
            self.masker.set_custom_keywords(self.keywords)
            
            self.entry_keyword.delete(0, "end")
            self.refresh_keyword_list()
            self.apply_custom_masking()

    def remove_keyword(self, keyword):
        if keyword in self.keywords:
            self.keywords.remove(keyword)
            self.save_keywords()
            self.masker.set_custom_keywords(self.keywords)
            
            self.refresh_keyword_list()
            self.apply_custom_masking()

    def refresh_keyword_list(self):
        # Clear existing widgets in scrollable frame
        for widget in self.keyword_list_frame.winfo_children():
            widget.destroy()

        for k in self.keywords:
            frame = ctk.CTkFrame(self.keyword_list_frame)
            frame.pack(fill="x", padx=5, pady=2)
            
            lbl = ctk.CTkLabel(frame, text=k)
            lbl.pack(side="left", padx=5)
            
            # Using specific keyword in lambda
            btn_del = ctk.CTkButton(frame, text="X", width=30, fg_color="red", hover_color="darkred", 
                                    command=lambda kw=k: self.remove_keyword(kw))
            btn_del.pack(side="right", padx=5, pady=2)

    def take_screenshot(self):
        # Minimize window to take screenshot
        self.iconify()
        self.after(500, self._perform_screenshot)

    def _perform_screenshot(self):
        try:
            from PIL import ImageGrab
            # Capture full screen
            screenshot = ImageGrab.grab()
            
            # Restore window
            self.deiconify()
            
            # Process image
            self.process_image(screenshot)
        except Exception as e:
            self.deiconify()
            print(f"Error taking screenshot: {e}")

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            img = Image.open(file_path)
            self.process_image(img)

    def process_image(self, image):
        self.original_image = image.copy() # Store original
        self._run_masking()

    def _run_masking(self):
        if not self.original_image:
            return

        # Show "Processing..."
        self.image_label.configure(text="Processing OCR and Masking...", image=None)
        self.update()

        # Run masking on the ORIGINAL image
        masked_image = self.masker.mask_privacy(self.original_image)
        self.current_image = masked_image

        # Update display
        self.display_image(self.current_image)
        self.btn_save.configure(state="normal")

    def display_image(self, image):
        # Resize for display
        display_w = self.main_frame.winfo_width() - 40
        display_h = self.main_frame.winfo_height() - 40
        
        if display_w < 100 or display_h < 100:
            display_w = 800
            display_h = 600

        img = image.copy()
        img.thumbnail((display_w, display_h), Image.Resampling.LANCZOS)
        
        # Keep reference to prevent Garbage Collection causing "image doesn't exist" error
        self.current_ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self.image_label.configure(image=self.current_ctk_image, text="")

    def save_image(self):
        if self.current_image:
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG file", "*.png"), ("JPEG file", "*.jpg")])
            if file_path:
                self.current_image.save(file_path)

    def apply_custom_masking(self):
        if self.original_image:
            self._run_masking()

    def reload_advanced_rules(self):
        # Open the editor window instead of just reloading
        if hasattr(self, "editor_window") and self.editor_window.winfo_exists():
            self.editor_window.focus()
        else:
            self.editor_window = AdvancedEditorWindow(self)

class AdvancedEditorWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Advanced Rules Editor (Regex)")
        self.geometry("600x600")
        
        # Attributes
        self.rules_file = os.path.join(os.path.dirname(__file__), "user_rules.py")
        self.patterns = []

        # UI - Input Area
        self.label = ctk.CTkLabel(self, text="Add New Regex Pattern:", font=ctk.CTkFont(weight="bold"))
        self.label.pack(padx=20, pady=(20, 5), anchor="w")
        
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=20, pady=5)
        
        self.entry_pattern = ctk.CTkEntry(self.input_frame, placeholder_text="e.g. Project\\s*Secret")
        self.entry_pattern.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_add = ctk.CTkButton(self.input_frame, text="Add", width=60, command=self.add_pattern)
        self.btn_add.pack(side="right")

        # UI - List Area
        self.list_label = ctk.CTkLabel(self, text="Registered Regex Patterns:", font=ctk.CTkFont(weight="bold"))
        self.list_label.pack(padx=20, pady=(20, 5), anchor="w")
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=540, height=350)
        self.scroll_frame.pack(padx=20, pady=5, fill="both", expand=True)
        
        self.load_current_rules()
        self.refresh_list()
        
        # Ensure it stays on top initially
        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))

    def load_current_rules(self):
        if os.path.exists(self.rules_file):
            try:
                import re
                with open(self.rules_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.patterns = re.findall(r"re\.compile\(r'(.+?)'\)", content)
            except Exception as e:
                print(f"Error reading user_rules.py for editor: {e}")

    def add_pattern(self):
        p = self.entry_pattern.get().strip()
        if p and p not in self.patterns:
            self.patterns.append(p)
            self.entry_pattern.delete(0, "end")
            self.save_and_apply()
            self.refresh_list()

    def remove_pattern(self, p):
        if p in self.patterns:
            self.patterns.remove(p)
            self.save_and_apply()
            self.refresh_list()

    def refresh_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        for p in self.patterns:
            frame = ctk.CTkFrame(self.scroll_frame)
            frame.pack(fill="x", padx=5, pady=2)
            
            lbl = ctk.CTkLabel(frame, text=p, anchor="w")
            lbl.pack(side="left", padx=10, fill="x", expand=True)
            
            btn_del = ctk.CTkButton(frame, text="X", width=30, fg_color="red", hover_color="darkred",
                                    command=lambda pattern=p: self.remove_pattern(pattern))
            btn_del.pack(side="right", padx=5, pady=2)

    def save_and_apply(self):
        # Construct the python file content
        content = "import re\n\nUSER_PATTERNS = [\n"
        for p in self.patterns:
            # We need to handle escaping backslashes for the string representation
            # but since it's r'...' we can mostly keep it as is.
            content += f"    re.compile(r'{p}'),\n"
        content += "]\n"
        
        try:
            with open(self.rules_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Reload in parent and apply
            self.parent.masker.load_user_rules()
            self.parent.apply_custom_masking()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to save rules: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
