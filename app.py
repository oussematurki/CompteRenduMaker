import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import re
from PIL import Image, ImageTk

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def natural_sort_key(path):
    """Ensures files like 2.png sort before 10.png."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'([0-9]+)', path.name)]

class WorkshopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Workshop PDF Generator")
        self.root.geometry("1050x700")

        # Top Frame for Selection Actions
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.dump_btn = tk.Button(top_frame, text="📁 Dump Folder", command=self.load_folder)
        self.dump_btn.pack(side=tk.LEFT, padx=5)

        self.select_files_btn = tk.Button(top_frame, text="🖼️ Select Individual Images", command=self.load_files)
        self.select_files_btn.pack(side=tk.LEFT, padx=5)

        self.add_section_btn = tk.Button(top_frame, text="➕ Add Empty Section", command=lambda: self.add_section(), bg="#e2e8f0")
        self.add_section_btn.pack(side=tk.LEFT, padx=15)

        self.source_label = tk.Label(top_frame, text="No source selected", fg="gray")
        self.source_label.pack(side=tk.LEFT, padx=10)

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
        right_container = tk.Frame(content_frame, width=320, relief=tk.SUNKEN, borderwidth=1)
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_container.pack_propagate(False)

        tk.Label(right_container, text="Screenshot Preview", font=("Arial", 10, "bold")).pack(pady=5)
        
        self.preview_label = tk.Label(right_container, text="Select an image to preview", fg="gray")
        self.preview_label.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Bottom Frame for Compile Button
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        self.compile_btn = tk.Button(bottom_frame, text="Generate PDF Report", command=self.generate_pdf, bg="#d4edda", state=tk.DISABLED)
        self.compile_btn.pack(fill=tk.X)

        self.sections = []  # List of section dictionaries
        self.current_photo = None

    def clear_workspace(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.sections.clear()
        self.preview_label.config(image="", text="Select an image to preview", fg="gray")

    def load_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            folder = Path(folder_path)
            self.source_label.config(text=f"Folder: {folder.name}", fg="black")
            self.clear_workspace()

            image_extensions = {".png", ".jpg", ".jpeg"}
            image_files = sorted([
                f for f in folder.iterdir() 
                if f.suffix.lower() in image_extensions
            ], key=natural_sort_key)

            if not image_files:
                messagebox.showwarning("No Images", "No screenshots found in this folder!")
                self.compile_btn.config(state=tk.DISABLED)
                return

            # Create one section per image
            for idx, img in enumerate(image_files):
                self.add_section(default_question=f"Question {idx + 1}", initial_images=[img])

            self.compile_btn.config(state=tk.NORMAL)
            self._bind_mouse_scroll(self.scrollable_frame)

    def load_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Screenshots",
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if file_paths:
            self.source_label.config(text=f"{len(file_paths)} files selected", fg="black")
            self.clear_workspace()

            image_files = sorted([Path(f) for f in file_paths], key=natural_sort_key)

            if not image_files:
                return

            # Put all selected individual files into a clean initial section together
            self.add_section(default_question="Question 1", initial_images=image_files)

            self.compile_btn.config(state=tk.NORMAL)
            self._bind_mouse_scroll(self.scrollable_frame)

    def add_section(self, default_question=None, initial_images=None):
        if initial_images is None:
            initial_images = []
        if default_question is None:
            default_question = f"Question {len(self.sections) + 1}"

        # Frame for this question group (using pack)
        row_frame = tk.LabelFrame(self.scrollable_frame, text=f"Section {len(self.sections) + 1}", padx=8, pady=8)
        row_frame.pack(fill=tk.X, padx=5, pady=6, expand=True)

        section_data = {
            "frame": row_frame,
            "question": None,
            "notes": None,
            "images": list(initial_images),
            "listbox": None
        }

        # Top row controls inside section (Delete section button)
        top_ctrls = tk.Frame(row_frame)
        top_ctrls.pack(fill=tk.X, anchor="e", pady=(0, 4))
        
        del_sec_btn = tk.Button(top_ctrls, text="❌ Delete Section", fg="red", font=("Arial", 8), 
                                command=lambda s=section_data: self.remove_section(s))
        del_sec_btn.pack(side=tk.RIGHT)

        # Question Header Row
        q_frame = tk.Frame(row_frame)
        q_frame.pack(fill=tk.X, pady=2)
        tk.Label(q_frame, text="Question / Header:", width=16, anchor="w").pack(side=tk.LEFT, padx=5)
        q_entry = tk.Entry(q_frame, width=40)
        q_entry.insert(0, default_question)
        q_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        section_data["question"] = q_entry

        # Explanation Notes Row
        n_frame = tk.Frame(row_frame)
        n_frame.pack(fill=tk.X, pady=2)
        tk.Label(n_frame, text="Explanation Notes:", width=16, anchor="nw").pack(side=tk.LEFT, padx=5, anchor="n")
        n_text = tk.Text(n_frame, width=40, height=3)
        n_text.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        section_data["notes"] = n_text

        # Images Management Sub-frame
        img_frame = tk.LabelFrame(row_frame, text="Attached Screenshots", padx=5, pady=5)
        img_frame.pack(fill=tk.X, padx=5, pady=5)

        listbox_frame = tk.Frame(img_frame)
        listbox_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        listbox = tk.Listbox(listbox_frame, height=4, width=40)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        lb_scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
        lb_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.configure(yscrollcommand=lb_scrollbar.set)
        
        section_data["listbox"] = listbox

        # Image action buttons column
        btn_col = tk.Frame(img_frame)
        btn_col.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        add_img_btn = tk.Button(btn_col, text="Add Image", command=lambda s=section_data: self.add_image_to_section(s))
        add_img_btn.pack(fill=tk.X, pady=2)

        rem_img_btn = tk.Button(btn_col, text="Remove", command=lambda s=section_data: self.remove_image_from_section(s))
        rem_img_btn.pack(fill=tk.X, pady=2)

        up_btn = tk.Button(btn_col, text="⬆ Up", command=lambda s=section_data: self.move_image(s, -1))
        up_btn.pack(fill=tk.X, pady=2)

        down_btn = tk.Button(btn_col, text="⬇ Down", command=lambda s=section_data: self.move_image(s, 1))
        down_btn.pack(fill=tk.X, pady=2)

        # Populate listbox
        self.refresh_image_listbox(section_data)

        # Bind selection event on listbox to show preview
        listbox.bind("<<ListboxSelect>>", lambda e, s=section_data: self.on_listbox_select(s))

        # Bind focus-in for text fields to preview the first image if available
        for widget in (q_entry, n_text):
            widget.bind("<FocusIn>", lambda e, s=section_data: self.preview_first_image(s))

        self.sections.append(section_data)
        self.compile_btn.config(state=tk.NORMAL)
        self._bind_mouse_scroll(self.scrollable_frame)

    def remove_section(self, section_data):
        section_data["frame"].destroy()
        if section_data in self.sections:
            self.sections.remove(section_data)
        if not self.sections:
            self.compile_btn.config(state=tk.DISABLED)

    def refresh_image_listbox(self, section_data):
        lb = section_data["listbox"]
        lb.delete(0, tk.END)
        for img in section_data["images"]:
            lb.insert(tk.END, img.name)

    def add_image_to_section(self, section_data):
        file_paths = filedialog.askopenfilenames(
            title="Add Screenshots",
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if file_paths:
            for f in file_paths:
                section_data["images"].append(Path(f))
            self.refresh_image_listbox(section_data)

    def remove_image_from_section(self, section_data):
        lb = section_data["listbox"]
        selection = lb.curselection()
        if selection:
            idx = selection[0]
            section_data["images"].pop(idx)
            self.refresh_image_listbox(section_data)

    def move_image(self, section_data, direction):
        lb = section_data["listbox"]
        selection = lb.curselection()
        if not selection:
            return
        idx = selection[0]
        new_idx = idx + direction
        
        images = section_data["images"]
        if 0 <= new_idx < len(images):
            # Swap
            images[idx], images[new_idx] = images[new_idx], images[idx]
            self.refresh_image_listbox(section_data)
            lb.selection_set(new_idx)

    def on_listbox_select(self, section_data):
        lb = section_data["listbox"]
        selection = lb.curselection()
        if selection:
            idx = selection[0]
            img_path = section_data["images"][idx]
            self.show_preview(img_path)

    def preview_first_image(self, section_data):
        if section_data["images"]:
            self.show_preview(section_data["images"][0])

    def show_preview(self, img_path):
        try:
            img = Image.open(img_path)
            img.thumbnail((300, 300))
            self.current_photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.current_photo, text="")
        except Exception as e:
            self.preview_label.config(image="", text="Could not load preview", fg="red")

    def generate_pdf(self):
        pdf_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Workshop PDF As"
        )
        
        if not pdf_path:
            return  

        try:
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                rightMargin=36, leftMargin=36,
                topMargin=36, bottomMargin=36
            )
            
            styles = getSampleStyleSheet()
            
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

            for section in self.sections:
                q_text = section["question"].get().strip()
                n_text = section["notes"].get("1.0", tk.END).strip()
                images = section["images"]

                # 1. Add Question Header
                if q_text:
                    story.append(Paragraph(q_text, header_style))

                # 2. Add all screenshots attached to this section with strict bounds
                for img_path in images:
                    if img_path.exists():
                        img = RLImage(str(img_path))
                        
                        maxWidth = 500
                        maxHeight = 450  # Prevent tall images from overflowing a single page
                        
                        orig_width, orig_height = img.imageWidth, img.imageHeight
                        
                        # Scale down by width if it exceeds maxWidth
                        if orig_width > maxWidth:
                            aspect = orig_height / float(orig_width)
                            img.drawWidth = maxWidth
                            img.drawHeight = maxWidth * aspect
                        else:
                            img.drawWidth = orig_width
                            img.drawHeight = orig_height

                        # Secondary check: if height still exceeds maxHeight, scale down further
                        if img.drawHeight > maxHeight:
                            aspect = img.drawWidth / float(img.drawHeight)
                            img.drawHeight = maxHeight
                            img.drawWidth = maxHeight * aspect
                        
                        story.append(img)
                        story.append(Spacer(1, 6))

                # 3. Add Explanation Notes
                if n_text:
                    story.append(Spacer(1, 4))
                    story.append(Paragraph(n_text, body_style))
                
                story.append(Spacer(1, 14))

            doc.build(story)
            messagebox.showinfo("Success", f"PDF successfully generated at:\n{pdf_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")

    def _on_mousewheel(self, event):
        if hasattr(event, 'delta') and event.delta != 0:
            if abs(event.delta) >= 120:
                amount = int(-1 * (event.delta / 120))
                self.canvas.yview_scroll(amount, "units")
            else:
                self.canvas.yview_scroll(int(-1 * event.delta), "pixels")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def _bind_mouse_scroll(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel, add="+")
        widget.bind("<Button-5>", self._on_mousewheel, add="+")
        for child in widget.winfo_children():
            self._bind_mouse_scroll(child)

if __name__ == "__main__":
    root = tk.Tk()
    app = WorkshopApp(root)
    root.mainloop()