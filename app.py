import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk  # Requires: pip install Pillow

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class WorkshopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Workshop PDF Generator")
        self.root.geometry("900x650")

        # Top Frame for Folder Selection
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.select_btn = tk.Button(top_frame, text="Select Screenshots Folder", command=self.load_folder)
        self.select_btn.pack(side=tk.LEFT)

        self.folder_label = tk.Label(top_frame, text="No folder selected", fg="gray")
        self.folder_label.pack(side=tk.LEFT, padx=10)

        # Main Content Area (Split into Left: Form, Right: Preview)
        content_frame = tk.Frame(root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left side: Scrollable Form Container
        left_container = tk.Frame(content_frame)
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(left_container)
        self.scrollbar = tk.Scrollbar(left_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right side: Image Preview Panel
        right_container = tk.Frame(content_frame, width=300, relief=tk.SUNKEN, borderwidth=1)
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_container.pack_propagate(False)

        tk.Label(right_container, text="Screenshot Preview", font=("Arial", 10, "bold")).pack(pady=5)
        
        self.preview_label = tk.Label(right_container, text="Select a field to preview", fg="gray")
        self.preview_label.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Bottom Frame for Compile Button
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        self.compile_btn = tk.Button(bottom_frame, text="Generate PDF", command=self.generate_pdf, bg="#d4edda", state=tk.DISABLED)
        self.compile_btn.pack(fill=tk.X)

        self.image_files = []
        self.input_entries = []
        self.current_photo = None # Keep reference to avoid garbage collection

    def load_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path = Path(folder_path)
            self.folder_label.config(text=str(self.folder_path), fg="black")
            
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.input_entries.clear()
            self.preview_label.config(image="", text="Select a field to preview", fg="gray")

            image_extensions = {".png", ".jpg", ".jpeg"}
            self.image_files = sorted([
                f for f in self.folder_path.iterdir() 
                if f.suffix.lower() in image_extensions
            ])

            if not self.image_files:
                messagebox.showwarning("No Images", "No screenshots found in this folder!")
                self.compile_btn.config(state=tk.DISABLED)
                return

            for idx, img in enumerate(self.image_files):
                row_frame = tk.LabelFrame(self.scrollable_frame, text=f"File: {img.name}", padx=5, pady=5)
                row_frame.pack(fill=tk.X, padx=5, pady=5, expand=True)

                tk.Label(row_frame, text="Question / Header:").grid(row=0, column=0, sticky="w", padx=5)
                q_entry = tk.Entry(row_frame, width=28)
                q_entry.insert(0, f"Question {idx + 1}")
                q_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)

                tk.Label(row_frame, text="Explanation Notes:").grid(row=1, column=0, sticky="nw", padx=5)
                n_text = tk.Text(row_frame, width=35, height=3)
                n_text.grid(row=1, column=1, sticky="w", padx=5, pady=2)

                # Bind focus-in event to update preview pane automatically
                for widget in (q_entry, n_text):
                    widget.bind("<FocusIn>", lambda e, path=img: self.show_preview(path))

                self.input_entries.append({
                    "path": img,
                    "question": q_entry,
                    "notes": n_text
                })

            self.compile_btn.config(state=tk.NORMAL)

    def show_preview(self, img_path):
        try:
            img = Image.open(img_path)
            # Resize image to fit neatly in the preview panel (e.g., max width 280)
            img.thumbnail((280, 280))
            self.current_photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.current_photo, text="")
        except Exception as e:
            self.preview_label.config(image="", text="Could not load preview", fg="red")


    def generate_pdf(self):
        # Prompt user to choose where to save the PDF
        pdf_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Workshop PDF As"
        )
        
        if not pdf_path:
            return  # User cancelled

        try:
            # Setup document (Letter size, 0.5-inch margins)
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                rightMargin=36, leftMargin=36,
                topMargin=36, bottomMargin=36
            )
            
            styles = getSampleStyleSheet()
            
            # Custom styles for clean workshop formatting
            header_style = ParagraphStyle(
                'QuestionHeader',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=6,
                textColor='#1a1a1a'
            )
            
            body_style = ParagraphStyle(
                'ExplanationBody',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=12,
                leading=14
            )

            story = []

            for entry in self.input_entries:
                # 1. Get user inputs
                q_text = entry["question"].get().strip()
                n_text = entry["notes"].get("1.0", tk.END).strip()
                img_path = entry["path"]

                # 2. Add Question Header
                if q_text:
                    story.append(Paragraph(q_text, header_style))

                # 3. Add Screenshot (scaled to fit nicely within printable width ~540 points)
                if img_path.exists():
                    # RLImage handles standard image scaling; keep width bounded to ~500 pts
                    img = RLImage(str(img_path))
                    
                    # Proportional scaling check
                    maxWidth = 500
                    orig_width, orig_height = img.imageWidth, img.imageHeight
                    if orig_width > maxWidth:
                        aspect = orig_height / float(orig_width)
                        img.drawWidth = maxWidth
                        img.drawHeight = maxWidth * aspect
                    
                    story.append(img)
                    story.append(Spacer(1, 8))

                # 4. Add Explanation Notes
                if n_text:
                    story.append(Paragraph(n_text, body_style))
                
                # Space between question items
                story.append(Spacer(1, 14))

            # Build PDF
            doc.build(story)
            messagebox.showinfo("Success", f"PDF successfully generated at:\n{pdf_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = WorkshopApp(root)
    root.mainloop()