import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import requests
import os
import zipfile
import time
import colorsys
import math
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk

class DiscordChatExporter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Blackshi Discord Chat Exporter")
        
        # الحصول على دقة الشاشة
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # جعل النافذة تأخذ 80% من عرض الشاشة و 85% من ارتفاع الشاشة
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)
        
        self.root.geometry(f"{window_width}x{window_height}")
        self.center_window(window_width, window_height)
        
        # --- Deep Dark "Glow" Theme ---
        self.bg_color = '#050505'        # Pure Black/Deepest Gray
        self.card_bg = '#0F0F0F'         # Very Dark Gray
        self.input_bg = '#000000'        # Pure Black inputs
        self.input_border = '#333333'    # Subtle border
        self.input_focus = '#00FFCC'     # Cyan Neon Glow (for focus)
        
        self.text_color = '#FFFFFF'      # Pure White text
        self.sub_text_color = '#888888'  # Dark Gray text
        
        self.accent_color = '#00FFCC'    # Cyan Glow
        self.accent_secondary = '#9D00FF' # Purple Glow
        
        self.button_bg = '#111111'       # Black button
        self.button_hover = '#1A1A1A'    # Slightly lighter black
        
        self.success_color = '#00FF99'   # Neon Green
        self.error_color = '#FF0055'     # Neon Red
        self.warning_color = '#FFCC00'   # Neon Yellow
        
        self.root.configure(bg=self.bg_color)
        
        # تحميل أيقونة النافذة
        self.set_window_icon()
        
        # حالة الأنيميشن RGB
        self.hue = 0.0
        self.animation_running = True
        
        # قائمة الانتظار والحالة
        self.log_queue = queue.Queue()
        self.running = False
        self.total_messages = 0
        self.total_files = 0
        
        # تهيئة الواجهة
        self.setup_ui()
        
        # بدء الحلقات
        self.root.after(100, self.process_log_queue)
        self.root.after(50, self.animate_rgb)  # تحديث أسرع لـ RGB
        
    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def set_window_icon(self):
        """تعيين أيقونة النافذة من blackshi.jpg"""
        try:
            image_paths = [
                "blackshi.jpg",
                os.path.join(os.path.dirname(__file__), "blackshi.jpg"),
                os.path.join(os.getcwd(), "blackshi.jpg")
            ]
            for path in image_paths:
                if os.path.exists(path):
                    img = Image.open(path)
                    photo = ImageTk.PhotoImage(img)
                    self.root.iconphoto(False, photo)
                    return
        except Exception as e:
            print(f"خطأ في تحميل الأيقونة: {e}")
    
    def animate_rgb(self):
        """تغيير لون النص بسلاسة عبر طيف RGB"""
        if self.animation_running and hasattr(self, 'title_label'):
            # زيادة Hue
            self.hue += 0.005
            if self.hue > 1.0: 
                self.hue = 0.0
            
            # تحويل HSV إلى RGB hex
            rgb = colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)
            color = "#{:02x}{:02x}{:02x}".format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
            
            self.title_label.config(fg=color)
            self.root.after(20, self.animate_rgb)
    
    def setup_ui(self):
        # الحاوية الرئيسية
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # --- اللوحة اليسرى (المدخلات) ---
        left_panel = tk.Frame(main_container, bg=self.card_bg, highlightbackground='#222222', highlightthickness=1)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 15))
        
        # حشو داخلي للوحة اليسرى
        left_inner = tk.Frame(left_panel, bg=self.card_bg)
        left_inner.pack(fill='both', expand=True, padx=30, pady=30)
        
        # الرأس
        header_frame = tk.Frame(left_inner, bg=self.card_bg)
        header_frame.pack(fill='x', pady=(0, 40))
        
        tk.Label(header_frame, text="DISCORD", font=('Segoe UI', 32, 'bold'),
                 bg=self.card_bg, fg='#444444').pack(anchor='w')
                 
        self.title_label = tk.Label(header_frame, text="BLACKSHI EXPORTER", font=('Segoe UI', 32, 'bold'),
                                   bg=self.card_bg, fg=self.accent_color)
        self.title_label.pack(anchor='w')
        
        # إزالة خاصية letterspacing الغير مدعومة
        tk.Label(header_frame, text="BLACKSHI TOOL", font=('Segoe UI', 10, 'bold'),
                 bg=self.card_bg, fg='#666666').pack(anchor='w', pady=(5,0))
        
        # المدخلات
        input_container = tk.Frame(left_inner, bg=self.card_bg)
        input_container.pack(fill='x', pady=(0, 30))
        
        self.token_entry = self.create_glow_input(input_container, "DISCORD TOKEN", is_password=True)
        
        # --- Mode Selection (Channel vs User) ---
        mode_frame = tk.Frame(input_container, bg=self.card_bg)
        mode_frame.pack(fill='x', pady=(0, 15))
        
        self.mode_var = tk.StringVar(value="channel")
        
        # Labels for the custom buttons
        tk.Label(mode_frame, text="TARGET TYPE", font=('Segoe UI', 9, 'bold'),
                 bg=self.card_bg, fg='#666666').pack(anchor='w', pady=(0, 5))
                 
        btn_container = tk.Frame(mode_frame, bg=self.card_bg)
        btn_container.pack(fill='x')
        
        # We will create two custom buttons
        self.btn_channel_border = tk.Frame(btn_container, bg=self.accent_color, padx=1, pady=1)
        self.btn_channel_border.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self.btn_user_border = tk.Frame(btn_container, bg=self.input_border, padx=1, pady=1)
        self.btn_user_border.pack(side='left', fill='x', expand=True)
        
        self.btn_channel = tk.Button(self.btn_channel_border, text="CHANNEL",
                                    font=('Segoe UI', 10, 'bold'),
                                    bg=self.input_bg, fg=self.accent_color,
                                    activebackground=self.input_bg, activeforeground=self.accent_color,
                                    relief='flat', bd=0, cursor='hand2',
                                    command=lambda: self.set_mode("channel"))
        self.btn_channel.pack(fill='both', ipady=5)
        
        self.btn_user = tk.Button(self.btn_user_border, text="USER (DM)",
                                 font=('Segoe UI', 10, 'bold'),
                                 bg=self.input_bg, fg='#666666',
                                 activebackground=self.input_bg, activeforeground='#888888',
                                 relief='flat', bd=0, cursor='hand2',
                                 command=lambda: self.set_mode("user"))
        self.btn_user.pack(fill='both', ipady=5)

        self.channel_entry, self.id_label = self.create_glow_input(input_container, "CHANNEL ID", return_label=True)
        self.file_entry = self.create_glow_input(input_container, "FILENAME", default="discord_export.zip")
        
        # الزر
        self.export_btn_frame = tk.Frame(left_inner, bg=self.accent_color, padx=1, pady=1)  # إطار حدود متوهجة
        self.export_btn_frame.pack(fill='x', pady=20)
        
        self.export_btn = tk.Button(self.export_btn_frame, text="START",
                                   font=('Segoe UI', 14, 'bold'),
                                   bg='black', fg='white',
                                   activebackground='#111111', activeforeground='white',
                                   relief='flat', bd=0, cursor='hand2',
                                   height=2, command=self.start_export)
        self.export_btn.pack(fill='both')
        
        # أنيميشن التمرير على الزر
        def btn_hover(e):
            self.export_btn.config(bg=self.accent_color, fg='black')
        
        def btn_leave(e):
            if not self.running:
                self.export_btn.config(bg='black', fg='white')
        
        self.export_btn.bind("<Enter>", btn_hover)
        self.export_btn.bind("<Leave>", btn_leave)

        # الإحصائيات
        stats_frame = tk.Frame(left_inner, bg=self.card_bg)
        stats_frame.pack(fill='x', pady=(40, 0))
        
        self.stats_labels = {}
        self.create_stat_item(stats_frame, "MESSAGES", "0", 0, self.success_color)
        self.create_stat_item(stats_frame, "FILES", "0", 1, self.warning_color)
        self.create_stat_item(stats_frame, "PROGRESS", "0%", 2, self.accent_color)
        
        # --- اللوحة اليمنى (السجلات) ---
        right_panel = tk.Frame(main_container, bg=self.bg_color)
        right_panel.pack(side='right', fill='both', expand=True, padx=(15, 0))
        
        # حاوية صندوق السجلات بحدود متوهجة
        log_border = tk.Frame(right_panel, bg='#222222', padx=1, pady=1)
        log_border.pack(fill='both', expand=True)
        
        log_inner = tk.Frame(log_border, bg=self.card_bg)
        log_inner.pack(fill='both', expand=True)
        
        # شريط أدوات السجلات
        toolbar = tk.Frame(log_inner, bg='#080808')
        toolbar.pack(fill='x')
        
        tk.Label(toolbar, text=" SYSTEM LOGS ", font=('Consolas', 10, 'bold'), bg='#080808', fg='#444444').pack(side='left', padx=10, pady=8)
        
        self.create_tool_btn(toolbar, "SAVE", self.save_logs)
        self.create_tool_btn(toolbar, "CLEAR", self.clear_logs)
        self.create_tool_btn(toolbar, "COPY", self.copy_logs)
        
        # نص السجلات
        self.log_text = scrolledtext.ScrolledText(log_inner, 
                                                 bg='#080808', fg='#CCCCCC',
                                                 font=('Consolas', 9),
                                                 insertbackground='white',
                                                 wrap='word', relief='flat', bd=0, padx=15, pady=15)
        self.log_text.pack(fill='both', expand=True)
        
        # شريط الحالة
        self.status_bar = tk.Label(self.root, text="System Ready", bg=self.bg_color, fg='#444444', 
                                  font=('Consolas', 8), anchor='w', padx=30, pady=5)
        self.status_bar.pack(side='bottom', fill='x')

        # تخصيص العلامات
        self.log_text.tag_config('success', foreground=self.success_color)
        self.log_text.tag_config('error', foreground=self.error_color)
        self.log_text.tag_config('warning', foreground=self.warning_color)
        self.log_text.tag_config('info', foreground='#00CCFF')  # سماوي
        self.log_text.tag_config('download', foreground='#CC00FF')  # بنفسجي

    def create_glow_input(self, parent, label_text, is_password=False, default="", return_label=False):
        container = tk.Frame(parent, bg=self.card_bg)
        container.pack(fill='x', pady=(0, 20))
        
        lbl = tk.Label(container, text=label_text, font=('Segoe UI', 9, 'bold'),
                 bg=self.card_bg, fg='#666666')
        lbl.pack(anchor='w', pady=(0, 5))
        
        # إطار الحدود
        border_frame = tk.Frame(container, bg=self.input_border, padx=1, pady=1)
        border_frame.pack(fill='x')
        
        inner_frame = tk.Frame(border_frame, bg=self.input_bg)
        inner_frame.pack(fill='x')
        
        entry = tk.Entry(inner_frame, font=('Segoe UI', 11),
                         bg=self.input_bg, fg='white',
                         insertbackground='white',
                         relief='flat', bd=0)
        entry.pack(fill='x', padx=12, pady=12, side='left', expand=True)
        
        if default:
            entry.insert(0, default)
            
        # تأثيرات التركيز (توهج)
        def on_focus_in(e):
            border_frame.config(bg=self.accent_color)  # لون التوهج
        
        def on_focus_out(e):
            border_frame.config(bg=self.input_border)
            
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        
        if is_password:
            entry.config(show="•")
            btn = tk.Button(inner_frame, text="👁", font=('Segoe UI', 12),
                           bg=self.input_bg, fg='#444444',
                           activebackground=self.input_bg, activeforeground='white',
                           relief='flat', bd=0, cursor='hand2',
                           command=lambda: self.toggle_password(entry, btn))
            btn.pack(side='right', padx=10)
            
        if return_label:
            return entry, lbl
        return entry

    def set_mode(self, mode):
        self.mode_var.set(mode)
        
        # Reset styles
        self.btn_channel.config(fg='#666666')
        self.btn_channel_border.config(bg=self.input_border)
        
        self.btn_user.config(fg='#666666')
        self.btn_user_border.config(bg=self.input_border)
        
        # Apply active style
        if mode == "channel":
            self.id_label.config(text="CHANNEL ID")
            self.btn_channel.config(fg=self.accent_color)
            self.btn_channel_border.config(bg=self.accent_color)
        else:
            self.id_label.config(text="USER ID")
            self.btn_user.config(fg=self.accent_color)
            self.btn_user_border.config(bg=self.accent_color)

    def toggle_password(self, entry, btn):
        if entry.cget('show') == '•':
            entry.config(show='')
            btn.config(fg=self.accent_color)
        else:
            entry.config(show='•')
            btn.config(fg='#444444')

    def create_stat_item(self, parent, label, value, col, color):
        frame = tk.Frame(parent, bg=self.card_bg)
        frame.grid(row=0, column=col, sticky='w', padx=(0, 50))
        
        tk.Label(frame, text=label, font=('Segoe UI', 8, 'bold'),
                 bg=self.card_bg, fg='#666666').pack(anchor='w')
        
        val_lbl = tk.Label(frame, text=value, font=('Segoe UI', 18, 'bold'),
                           bg=self.card_bg, fg=color)
        val_lbl.pack(anchor='w')
        self.stats_labels[label] = val_lbl

    def create_tool_btn(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, font=('Segoe UI', 8, 'bold'),
                        bg='#080808', fg='#666666',
                        activebackground='#151515', activeforeground='white',
                        relief='flat', bd=0, padx=10, pady=5, cursor='hand2',
                        command=cmd)
        btn.pack(side='right')
        
        btn.bind("<Enter>", lambda e: btn.config(fg='white'))
        btn.bind("<Leave>", lambda e: btn.config(fg='#666666'))

    # --- المنطق ---

    def log_message(self, message, tag='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put((f"[{timestamp}] {message}\n", tag))

    def process_log_queue(self):
        try:
            while True:
                msg, tag = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, msg, tag)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_log_queue)

    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        self.log_message("Logs cleared", 'info')

    def copy_logs(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log_text.get(1.0, tk.END))
        self.log_message("Logs copied to clipboard", 'success')

    def save_logs(self):
        desktop = Path.home() / "Desktop"
        log_file = desktop / f"discord_export_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(self.log_text.get(1.0, tk.END))
        self.log_message(f"Logs saved to: {log_file}", 'success')

    def update_stats(self, key, value, color=None):
        if key in self.stats_labels:
            self.stats_labels[key].config(text=value)
            if color:
                self.stats_labels[key].config(fg=color)

    def get_dm_channel(self, token, user_id):
        """Creates or retrieves a DM channel with a user."""
        url = "https://discord.com/api/v9/users/@me/channels"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        data = {"recipient_id": user_id}
        
        try:
            self.log_message(f"🔍 Resolving DM channel for User ID: {user_id}...", 'info')
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                channel_id = response.json().get('id')
                self.log_message(f"✅ Found DM Channel ID: {channel_id}", 'success')
                return channel_id
            else:
                self.log_message(f"❌ Failed to resolve DM: {response.text}", 'error')
                return None
        except Exception as e:
            self.log_message(f"❌ Error resolving DM: {str(e)}", 'error')
            return None

    def start_export(self):
        if self.running: 
            return
        
        token = self.token_entry.get().strip()
        input_id = self.channel_entry.get().strip()
        filename = self.file_entry.get().strip()
        mode = self.mode_var.get()
        
        if not token or not input_id:
            messagebox.showerror("Error", "Please enter Token and ID!")
            return
        
        if not filename: 
            filename = "discord_export.zip"
        if not filename.endswith('.zip'): 
            filename += '.zip'
        
        desktop = Path.home() / "Desktop"
        zip_path = desktop / filename
        
        self.running = True
        self.export_btn.config(state='disabled', text="EXPORTING...", bg='#222222')
        self.title_label.config(text="EXPORTING...")
        self.status_bar.config(text="Preparing export...", fg=self.accent_color)
        
        # Start in a thread
        def run_thread():
            channel_id = input_id
            
            # If in User mode, resolve DM channel first
            if mode == 'user':
                channel_id = self.get_dm_channel(token, input_id)
                if not channel_id:
                    self.status_bar.config(text="Failed to resolve User ID", fg=self.error_color)
                    self.running = False
                    self.root.after(0, self.export_complete)
                    return
            
            self.export_chat(token, channel_id, str(zip_path))

        thread = threading.Thread(target=run_thread, daemon=True)
        thread.start()

    def export_chat(self, token, channel_id, zip_path):
        try:
            headers = {"Authorization": token}
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
            params = {"limit": 100}
            
            img_ext = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
            vid_ext = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv")
            aud_ext = (".mp3", ".wav", ".ogg", ".flac", ".m4a")
            
            used_names = set()
            chat_lines = []
            self.total_messages = 0
            self.total_files = 0
            
            self.log_message("=" * 50, 'info')
            self.log_message("STARTING DISCORD CHAT EXPORT", 'success')
            self.log_message(f"Channel ID: {channel_id}", 'info')
            self.log_message(f"Save Location: {zip_path}", 'info')
            self.log_message("=" * 50, 'info')
            
            def unique_name(name):
                base, ext = os.path.splitext(name)
                i = 1
                final = name
                while final in used_names:
                    final = f"{base}_{i}{ext}"
                    i += 1
                used_names.add(final)
                return final
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for folder in ['images', 'videos', 'audio', 'documents']:
                    zipf.writestr(f"{folder}/.placeholder", "")
                
                self.log_message("📡 Connecting to Discord API...", 'info')
                
                session_count = 0
                while self.running:
                    try:
                        response = requests.get(url, headers=headers, params=params, timeout=30)
                        
                        if response.status_code == 401:
                            self.log_message("❌ ERROR: Invalid or expired token!", 'error')
                            break
                        elif response.status_code == 403:
                            self.log_message("❌ ERROR: No permission to access this channel", 'error')
                            break
                        elif response.status_code == 404:
                            self.log_message("❌ ERROR: Channel not found", 'error')
                            break
                        elif response.status_code == 429:
                            self.log_message("⚠️ Rate limited, waiting 2 seconds...", 'warning')
                            time.sleep(2)
                            continue
                        elif response.status_code != 200:
                            self.log_message(f"❌ HTTP Error {response.status_code}", 'error')
                            break
                        
                        messages = response.json()
                        if not messages:
                            self.log_message("✅ Reached end of messages", 'success')
                            break
                        
                        session_count += 1
                        self.log_message(f"📥 Session {session_count}: Processing {len(messages)} messages...", 'info')
                        
                        for msg in messages:
                            try:
                                author = msg.get("author", {}).get("username", "Unknown")
                                time_ = msg.get("timestamp", "Unknown")
                                content = msg.get("content", "")
                                
                                if content:
                                    chat_lines.append(f"[{time_}] {author}: {content}")
                                
                                for att in msg.get("attachments", []):
                                    try:
                                        file_url = att.get("url")
                                        original_name = att.get("filename", "unknown")
                                        
                                        if not file_url:
                                            continue
                                            
                                        filename_unique = unique_name(original_name)
                                        
                                        self.log_message(f"⬇️ Downloading: {original_name}", 'download')
                                        
                                        file_response = requests.get(file_url, timeout=45, stream=True)
                                        if file_response.status_code == 200:
                                            ext = os.path.splitext(original_name)[1].lower()
                                            
                                            if ext in img_ext:
                                                folder = "images"
                                            elif ext in vid_ext:
                                                folder = "videos"
                                            elif ext in aud_ext:
                                                folder = "audio"
                                            else:
                                                folder = "documents"
                                            
                                            zipf.writestr(f"{folder}/{filename_unique}", file_response.content)
                                            self.total_files += 1
                                            self.update_stats("FILES", str(self.total_files), self.success_color)
                                        
                                    except Exception as e:
                                        self.log_message(f"⚠️ Failed attachment: {str(e)[:50]}...", 'warning')
                                
                                self.total_messages += 1
                                if self.total_messages % 50 == 0:
                                    self.update_stats("MESSAGES", str(self.total_messages), self.success_color)
                                    progress = min(95, (self.total_messages / 10000) * 95)
                                    self.update_stats("PROGRESS", f"{progress:.1f}%", self.accent_color)
                                    
                            except Exception as e:
                                continue
                        
                        params["before"] = messages[-1]["id"]
                        time.sleep(0.5)
                        
                    except requests.exceptions.RequestException as e:
                        self.log_message(f"🌐 Network issue: {str(e)[:50]}", 'warning')
                        time.sleep(2)
                        continue
                
                # حفظ المحادثة
                self.log_message("💾 Saving chat text...", 'info')
                chat_content = "\n".join(chat_lines)
                zipf.writestr("chat.txt", chat_content)
                
                # حفظ البيانات الوصفية
                metadata = f"""=== DISCORD CHAT EXPORT ===
Export Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Channel ID: {channel_id}
Total Messages: {self.total_messages}
Total Attachments: {self.total_files}
File Size: {os.path.getsize(zip_path) if os.path.exists(zip_path) else 0} bytes
Saved To: {zip_path}
"""
                zipf.writestr("_metadata.txt", metadata)
            
            # تحديث الإحصائيات النهائية
            self.update_stats("MESSAGES", str(self.total_messages), self.success_color)
            self.update_stats("FILES", str(self.total_files), self.success_color)
            self.update_stats("PROGRESS", "100%", self.success_color)
            
            self.log_message("=" * 50, 'success')
            self.log_message("✅ EXPORT COMPLETED SUCCESSFULLY!", 'success')
            self.log_message(f"📊 Total Messages: {self.total_messages}", 'info')
            self.log_message(f"📎 Total Files: {self.total_files}", 'info')
            self.log_message(f"💾 Saved to: {zip_path}", 'info')
            self.log_message(f"📦 File Size: {os.path.getsize(zip_path) / 1024:.1f} KB", 'info')
            self.log_message("=" * 50, 'success')
            
            self.status_bar.config(text="Export completed successfully!", fg=self.success_color)
            
            # عرض رسالة النجاح
            messagebox.showinfo("Export Complete", 
                              f"✅ Export completed successfully!\n\n"
                              f"📄 Messages: {self.total_messages}\n"
                              f"📎 Files: {self.total_files}\n"
                              f"💾 Saved to: Desktop\\{os.path.basename(zip_path)}")
            
        except Exception as e:
            error_msg = str(e)
            self.log_message(f"❌ CRITICAL ERROR: {error_msg}", 'error')
            self.status_bar.config(text="Export failed!", fg=self.error_color)
            messagebox.showerror("Export Failed", 
                               f"Export failed with error:\n\n{error_msg}")
        
        finally:
            self.running = False
            self.root.after(0, self.export_complete)
    
    def export_complete(self):
        self.export_btn.config(state='normal', text="START EXPORT", bg='black', fg='white')
        self.title_label.config(text="CHAT EXPORTER")
        self.status_bar.config(text="System Ready | Press START EXPORT to begin", fg='#444444')
    
    def run(self):
        self.root.mainloop()

def main():
    app = DiscordChatExporter()
    app.run()

if __name__ == "__main__":
    main()
