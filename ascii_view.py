import time
import os
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, font  # Thêm import font
import threading
from tkinter import messagebox

ASCII_STYLES = {
    "Classic": " .:-=+*#%@",
    "Blocks": " ░▒▓█",
    "Thin": " .`^\",:;Il!i~+_-?",
    "Dense": "@#MW&%B$8",
    "Artistic": "≡≣+=-.,~",
    "High Contrast": "@%#*+=-:. "
}

COLOR_SCHEME = {
    "bg": "#2d2d2d",
    "fg": "#e0e0e0",
    "accent": "#3498db",
    "secondary": "#7f8c8d",
    "text_bg": "#1a1a1a"
}

class ModernASCIIArtViewer:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.current_thread = None
        self.file_path = ""
        self.last_render_time = 0
        self.setup_bindings()
        
    def setup_ui(self):
        self.root.title("Super Dump")
        self.root.geometry("1200x800")
        self.root.configure(bg=COLOR_SCHEME["bg"])
        
        # Custom style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background=COLOR_SCHEME["bg"])
        self.style.configure("TLabel", background=COLOR_SCHEME["bg"], foreground=COLOR_SCHEME["fg"], font=('Segoe UI', 9))
        self.style.configure("TButton", font=('Segoe UI', 9), padding=6, background=COLOR_SCHEME["accent"])
        self.style.map("TButton", background=[('active', COLOR_SCHEME["secondary"])])
        self.style.configure("TCombobox", padding=5, fieldbackground=COLOR_SCHEME["text_bg"])
        self.style.configure("Horizontal.TScale", background=COLOR_SCHEME["bg"], troughcolor=COLOR_SCHEME["secondary"])
        
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Text display area
        self.setup_text_area()
        
        # Control panel
        self.setup_control_panel()
        
        # Status bar
        self.setup_status_bar()
    
    def setup_text_area(self):
        text_frame = ttk.Frame(self.main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.NONE,
            font=("Consolas", 12),
            bg=COLOR_SCHEME["text_bg"],
            fg=COLOR_SCHEME["accent"],
            insertbackground=COLOR_SCHEME["fg"],
            selectbackground=COLOR_SCHEME["secondary"],
            padx=10,
            pady=10
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
    
    def setup_control_panel(self):
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # Variables
        self.width_var = tk.IntVar(value=200)
        self.font_size_var = tk.IntVar(value=12)
        self.mode_var = tk.StringVar(value="High Contrast")
        self.effect_var = tk.StringVar(value="Sharpen")
        self.style_var = tk.StringVar(value="High Contrast")
        
        # Control grid
        controls = [
            ("Độ rộng", self.width_var, 50, 400, self.on_control_change),
            ("Cỡ chữ", self.font_size_var, 6, 24, self.update_font_size),
            ("Chế độ", self.mode_var, ["Gray", "Negative", "High Contrast"], None, self.on_control_change),
            ("Hiệu ứng", self.effect_var, ["None", "Sharpen", "Enhance"], None, self.on_control_change),
            ("Kiểu", self.style_var, list(ASCII_STYLES.keys()), None, self.on_control_change),
        ]
        
        for col, (label, var, from_, to, cmd) in enumerate(controls):
            group = ttk.Frame(toolbar)
            group.grid(row=0, column=col, padx=8, sticky="ew")
            
            ttk.Label(group, text=label+" :").pack(anchor="w")
            
            if isinstance(from_, list):
                dropdown = ttk.Combobox(
                    group, textvariable=var,
                    values=from_, state="readonly"
                )
                dropdown.pack(fill=tk.X)
                dropdown.bind("<<ComboboxSelected>>", cmd)
            else:
                slider = ttk.Scale(
                    group, from_=from_, to=to,
                    variable=var, command=cmd,
                    style="Horizontal.TScale"
                )
                slider.pack(fill=tk.X)
        
        # Buttons
        self.select_btn = ttk.Button(
            toolbar, text="Chọn ảnh", command=self.select_image,
            style="TButton"
        )
        self.select_btn.grid(row=0, column=5, padx=8, sticky="e")
        
        self.export_btn = ttk.Button(
            toolbar, text="Xuất TXT", command=self.export_txt,
            style="TButton"
        )
        self.export_btn.grid(row=0, column=6, padx=8, sticky="e")
        
        # Thêm nút autofit_btn
        self.autofit_btn = ttk.Button(
            toolbar, text="Auto Fit", command=self.auto_fit,
            style="TButton"
        )
        self.autofit_btn.grid(row=0, column=7, padx=8, sticky="e")
    
    def setup_status_bar(self):
        self.status_bar = ttk.Frame(self.main_frame, height=24)
        self.status_bar.pack(fill=tk.X, pady=(5,0))
        
        self.status_label = ttk.Label(
            self.status_bar,
            text="Sẵn sàng",
            relief=tk.FLAT,
            anchor=tk.W,
            background=COLOR_SCHEME["secondary"],
            foreground=COLOR_SCHEME["fg"]
        )
        self.status_label.pack(fill=tk.X)
    
    def setup_bindings(self):
        self.root.bind("<Control-MouseWheel>", self.on_ctrl_scroll)
        self.root.bind("<Configure>", self.on_window_resize)
    
    def select_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.png *.jpeg *.bmp")]
        )
        if file_path:
            self.file_path = file_path
            self.status_label.config(text=f"Đang xử lý: {os.path.basename(file_path)}")
            self.render_ascii()
    
    def process_image(self):
        try:
            img = Image.open(self.file_path).convert("L")
            
            if self.effect_var.get() == "Sharpen":
                img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
            elif self.effect_var.get() == "Enhance":
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(2.0)

            if self.mode_var.get() == "Negative":
                img = Image.fromarray(255 - np.array(img))
            elif self.mode_var.get() == "High Contrast":
                img = img.point(lambda x: 0 if x < 128 else 255)

            aspect_ratio = img.height / img.width
            new_width = min(400, max(50, self.width_var.get()))
            height = int(new_width * aspect_ratio * 0.6)
            
            img = img.resize((new_width, height), Image.LANCZOS)
            pixels = np.array(img)

            chars = ASCII_STYLES.get(self.style_var.get(), ASCII_STYLES["High Contrast"])
            gradient = np.linspace(0, 255, len(chars))
            
            ascii_art = []
            for row in pixels:
                line = [chars[np.abs(gradient - val).argmin()] for val in row]
                ascii_art.append("".join(line) + "\n")
            
            return "".join(ascii_art)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xử lý ảnh: {str(e)}")
            return ""
    
    def draw_ascii_art(self, ascii_art):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, ascii_art)
        self.text_area.config(state=tk.DISABLED)
        self.status_label.config(text=f"Hoàn thành: {os.path.basename(self.file_path)} | Kích thước: {self.width_var.get()}x{int(self.width_var.get() * (Image.open(self.file_path).height/Image.open(self.file_path).width) * 0.6)}")
    
    def render_ascii(self):
        if time.time() - self.last_render_time < 0.5:
            return
        self.last_render_time = time.time()
        
        if not self.file_path:
            return
        
        def thread_target():
            ascii_art = self.process_image()
            if ascii_art:
                self.draw_ascii_art(ascii_art)
        
        threading.Thread(target=thread_target, daemon=True).start()
    
    def update_font_size(self, event=None):
        self.text_area.config(font=("Consolas", self.font_size_var.get()))
        self.auto_fit()
    
    def on_control_change(self, event=None):
        self.render_ascii()
    
    def export_txt(self):
        if not self.file_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ảnh trước khi xuất")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_area.get(1.0, tk.END))
                messagebox.showinfo("Thành công", "Đã lưu file thành công")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu file: {str(e)}")
    
    def on_ctrl_scroll(self, event):
        if event.delta > 0:
            self.font_size_var.set(min(24, self.font_size_var.get() + 1))
        else:
            self.font_size_var.set(max(6, self.font_size_var.get() - 1))
        self.update_font_size()
    
    def auto_fit(self):
        if not self.file_path:
            return
        
        # Sửa lỗi font import
        current_font = font.Font(family="Consolas", size=self.font_size_var.get())
        avg_char_width = current_font.measure("A")
        
        if avg_char_width == 0:
            return
        
        # Tính toán kích thước dựa trên widget cha
        text_width = self.text_area.winfo_width() - 20  # Trừ padding
        max_chars = max(10, text_width // avg_char_width)
        self.width_var.set(max_chars)
        self.render_ascii()
    
    def on_window_resize(self, event):
        if event.widget == self.root:
            self.auto_fit()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernASCIIArtViewer(root)
    root.mainloop()