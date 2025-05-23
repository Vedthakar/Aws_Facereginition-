#!/usr/bin/env python3
import os
import boto3
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from pathlib import Path

# ─── Configuration ─────────────────────────────────────────────────────────────
AWS_REGION    = "us-east-2"
BUCKET        = "allowedpeople-images"  # bucket name
# ────────────────────────────────────────────────────────────────────────────────

# ─── AWS Client ─────────────────────────────────────────────────────────────────
s3 = boto3.client("s3", region_name=AWS_REGION)
# ────────────────────────────────────────────────────────────────────────────────

class UploaderApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Intruder Detector Uploader")
        self.geometry("500x200")
        self.configure(padx=10, pady=10)

        # File path
        self.file_path = None

        # Widgets
        self.lbl = tk.Label(self, text="Drag & drop an image here\nor click to browse", 
                            relief="ridge", width=50, height=5)
        self.lbl.pack(pady=(0,10))
        self.lbl.drop_target_register(DND_FILES)
        self.lbl.dnd_bind('<<Drop>>', self.on_drop)
        self.lbl.bind("<Button-1>", lambda e: self.browse_file())

        # Metadata entry
        tk.Label(self, text="Metadata (key:value), optional:").pack(anchor="w")
        self.meta_var = tk.StringVar()
        self.meta_entry = tk.Entry(self, textvariable=self.meta_var, width=50)
        self.meta_entry.pack(pady=(0,10))

        self.btn = tk.Button(self, text="Upload to intruder-detector", command=self.upload)
        self.btn.pack()

    def on_drop(self, event):
        path = event.data.strip("{}")  # remove braces around path
        self.file_path = path
        self.lbl.config(text=Path(path).name)

    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image files","*.jpg;*.jpeg;*.png;*.bmp;*.HEIC")]
        )
        if path:
            self.file_path = path
            self.lbl.config(text=Path(path).name)

    def upload(self):
        if not self.file_path:
            messagebox.showerror("No file", "Please drag/drop or select an image file first.")
            return

        key = Path(self.file_path).name
        metadata = {}
        meta_input = self.meta_var.get().strip()
        if meta_input:
            try:
                k, v = meta_input.split(":", 1)
                metadata[k.strip()] = v.strip()
            except ValueError:
                messagebox.showerror("Invalid metadata", "Please enter metadata in 'key:value' format.")
                return

        try:
            with open(self.file_path, "rb") as f:
                s3.put_object(
                    Bucket=BUCKET,
                    Key=key,
                    Body=f,
                    Metadata=metadata
                )
            messagebox.showinfo("Success", f"Uploaded {key} to {BUCKET}")
            # Reset UI
            self.file_path = None
            self.lbl.config(text="Drag & drop an image here\nor click to browse")
            self.meta_var.set("")
        except Exception as e:
            messagebox.showerror("Upload failed", str(e))

if __name__ == "__main__":
    app = UploaderApp()
    app.mainloop()

