#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blackshi Discord Chat Exporter - Terminal Edition
Professional Discord Chat Export Tool
"""

import os
import sys
import time
import json
import shutil
import zipfile
import requests
from datetime import datetime
from pathlib import Path

# ANSI Colors for Terminal
class Colors:
    # Reset
    RESET = '\033[0m'
    
    # Regular Colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bold Colors
    BOLD = '\033[1m'
    RED_BOLD = '\033[1;31m'
    GREEN_BOLD = '\033[1;32m'
    CYAN_BOLD = '\033[1;36m'

class DiscordChatExporter:
    def __init__(self):
        self.running = False
        self.total_messages = 0
        self.total_files = 0
        
        # Show banner
        self.clear_screen()
        self.print_banner()
    
    def clear_screen(self):
        """Clear screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """Print Blackshi banner"""
        banner = f"""
{Colors.CYAN_BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ██████╗ ██╗      █████╗  ██████╗██╗  ██╗███████╗██╗  ██╗██╗               ║
║    ██╔══██╗██║     ██╔══██╗██╔════╝██║  ██║██╔════╝██║  ██║██║               ║
║    ██████╔╝██║     ███████║██║     ███████║███████╗███████║██║               ║
║    ██╔══██╗██║     ██╔══██║██║     ██╔══██║╚════██║██╔══██║██║               ║
║    ██████╔╝███████╗██║  ██║╚██████╗██║  ██║███████║██║  ██║███████╗          ║
║    ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝          ║
║                                                                              ║
║                    Discord Chat Exporter - Terminal Edition                  ║
║                             Created by Blackshi                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
"""
        print(banner)
    
    def print_log(self, message, level="INFO"):
        """Print message with formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "ERROR": Colors.RED,
            "DOWNLOAD": Colors.CYAN
        }
        
        color = colors.get(level, Colors.WHITE)
        
        print(f"{color}[{timestamp}] {message}{Colors.RESET}")
    
    def get_dm_channel(self, token, user_id):
        """Get DM channel ID"""
        url = "https://discord.com/api/v9/users/@me/channels"
        headers = {"Authorization": token, "Content-Type": "application/json"}
        data = {"recipient_id": user_id}
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                return response.json().get('id')
            else:
                self.print_log(f"Failed to create DM: {response.status_code}", "ERROR")
                return None
        except Exception as e:
            self.print_log(f"Error creating DM: {str(e)}", "ERROR")
            return None
    
    def download_file(self, url, filename, zipf, folder):
        """Download single file"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                zipf.writestr(f"{folder}/{filename}", response.content)
                self.total_files += 1
                self.print_log(f"Downloaded: {filename}", "DOWNLOAD")
                return True
        except Exception as e:
            self.print_log(f"Failed to download {filename}: {str(e)[:50]}", "ERROR")
        return False
    
    def export_chat(self, token, mode, target_id, filename):
        """Export chat conversation"""
        try:
            headers = {"Authorization": token}
            channel_id = target_id
            
            # If mode is user, get DM channel
            if mode == "user":
                self.print_log("Creating DM channel...", "INFO")
                channel_id = self.get_dm_channel(token, target_id)
                if not channel_id:
                    return False
            
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
            params = {"limit": 100}
            
            # File extensions
            img_ext = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
            vid_ext = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv")
            aud_ext = (".mp3", ".wav", ".ogg", ".flac", ".m4a")
            
            used_names = set()
            chat_lines = []
            
            # Output path
            desktop = Path.home() / "Desktop"
            zip_path = desktop / filename
            
            self.print_log("=" * 50, "INFO")
            self.print_log("Starting Discord Chat Export", "INFO")
            self.print_log(f"Target: {channel_id}", "INFO")
            self.print_log("=" * 50, "INFO")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Create folders
                for folder in ['images', 'videos', 'audio', 'documents']:
                    zipf.writestr(f"{folder}/.placeholder", "")
                
                # Reset counters
                self.total_messages = 0
                self.total_files = 0
                sessions = 0
                
                while self.running:
                    try:
                        response = requests.get(url, headers=headers, params=params, timeout=30)
                        
                        # Check for errors
                        if response.status_code == 401:
                            self.print_log("ERROR: Invalid or expired token!", "ERROR")
                            break
                        elif response.status_code == 403:
                            self.print_log("ERROR: No permission to access this channel", "ERROR")
                            break
                        elif response.status_code == 404:
                            self.print_log("ERROR: Channel not found", "ERROR")
                            break
                        elif response.status_code == 429:
                            self.print_log("Rate limited, waiting 2 seconds...", "ERROR")
                            time.sleep(2)
                            continue
                        elif response.status_code != 200:
                            self.print_log(f"HTTP Error {response.status_code}", "ERROR")
                            break
                        
                        messages = response.json()
                        if not messages:
                            self.print_log("Reached end of messages", "SUCCESS")
                            break
                        
                        sessions += 1
                        self.print_log(f"Session {sessions}: Processing {len(messages)} messages...", "INFO")
                        
                        # Process messages
                        for msg in messages:
                            # Extract message info
                            author = msg.get("author", {}).get("username", "Unknown")
                            timestamp = msg.get("timestamp", "Unknown")
                            content = msg.get("content", "")
                            
                            # Add to chat
                            if content:
                                chat_lines.append(f"[{timestamp}] {author}: {content}")
                            
                            # Process attachments
                            for att in msg.get("attachments", []):
                                file_url = att.get("url")
                                original_name = att.get("filename", "unknown")
                                
                                if not file_url:
                                    continue
                                
                                # Avoid duplicate names
                                base, ext = os.path.splitext(original_name)
                                i = 1
                                final_name = original_name
                                while final_name in used_names:
                                    final_name = f"{base}_{i}{ext}"
                                    i += 1
                                used_names.add(final_name)
                                
                                # Determine folder
                                ext = ext.lower()
                                if ext in img_ext:
                                    folder = "images"
                                elif ext in vid_ext:
                                    folder = "videos"
                                elif ext in aud_ext:
                                    folder = "audio"
                                else:
                                    folder = "documents"
                                
                                # Download file
                                self.download_file(file_url, final_name, zipf, folder)
                            
                            self.total_messages += 1
                            
                            # Show progress every 50 messages
                            if self.total_messages % 50 == 0:
                                self.print_log(f"Progress: {self.total_messages} messages | {self.total_files} files", "INFO")
                        
                        # Move to next page
                        params["before"] = messages[-1]["id"]
                        time.sleep(0.5)
                        
                    except requests.exceptions.RequestException as e:
                        self.print_log(f"Network issue: {str(e)[:50]}", "ERROR")
                        time.sleep(2)
                        continue
                
                # Save chat text
                self.print_log("Saving chat text...", "INFO")
                chat_content = "\n".join(chat_lines)
                zipf.writestr("chat.txt", chat_content.encode('utf-8'))
                
                # Save metadata
                metadata = f"""=== DISCORD CHAT EXPORT ===
Export Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Channel ID: {channel_id}
Total Messages: {self.total_messages}
Total Files: {self.total_files}
File Size: {os.path.getsize(zip_path) if os.path.exists(zip_path) else 0} bytes
"""
                zipf.writestr("_metadata.txt", metadata)
            
            # Show final result
            print(f"\n{Colors.GREEN_BOLD}{'═' * 50}{Colors.RESET}")
            print(f"{Colors.GREEN_BOLD}✓ EXPORT COMPLETED SUCCESSFULLY!{Colors.RESET}")
            print(f"{Colors.GREEN}  • Total Messages: {self.total_messages}{Colors.RESET}")
            print(f"{Colors.GREEN}  • Total Files: {self.total_files}{Colors.RESET}")
            print(f"{Colors.GREEN}  • Saved to: {zip_path}{Colors.RESET}")
            print(f"{Colors.GREEN}  • File Size: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB{Colors.RESET}")
            print(f"{Colors.GREEN_BOLD}{'═' * 50}{Colors.RESET}\n")
            
            return True
            
        except Exception as e:
            self.print_log(f"CRITICAL ERROR: {str(e)}", "ERROR")
            print(f"\n{Colors.RED_BOLD}{'═' * 50}{Colors.RESET}")
            print(f"{Colors.RED_BOLD}✗ EXPORT FAILED{Colors.RESET}")
            print(f"{Colors.RED}  Error: {str(e)}{Colors.RESET}")
            print(f"{Colors.RED_BOLD}{'═' * 50}{Colors.RESET}\n")
            return False
    
    def get_input(self, prompt, password=False):
        """Get user input"""
        prompt_text = f"{Colors.CYAN}{prompt}: {Colors.RESET}"
        
        # تعديل: إزالة استخدام getpass للتوكن فقط، جعله ظاهراً
        value = input(prompt_text)
        
        return value.strip()
    
    def show_menu(self):
        """Show main menu"""
        while True:
            self.clear_screen()
            self.print_banner()
            
            print(f"{Colors.YELLOW}[1]{Colors.RESET} Start Export")
            print(f"{Colors.YELLOW}[2]{Colors.RESET} Exit")
            
            choice = input(f"\n{Colors.CYAN}Select option [1-2]: {Colors.RESET}")
            
            if choice == "1":
                self.start_export()
            elif choice == "2":
                self.exit_program()
            else:
                print(f"{Colors.RED}Invalid option!{Colors.RESET}")
                time.sleep(1)
    
    def start_export(self):
        """Start export process"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n{Colors.GREEN}Enter export information:{Colors.RESET}")
        print(f"{Colors.CYAN}{'─' * 40}{Colors.RESET}\n")
        
        # Get token - تم التعديل ليكون ظاهراً
        token = self.get_input("Discord Token")
        if not token:
            print(f"{Colors.RED}Token is required!{Colors.RESET}")
            time.sleep(2)
            return
        
        # Select mode
        print(f"\n{Colors.YELLOW}Select export type:{Colors.RESET}")
        print(f"  {Colors.GREEN}[1]{Colors.RESET} Channel")
        print(f"  {Colors.GREEN}[2]{Colors.RESET} User (DM)")
        
        mode_choice = input(f"\n{Colors.CYAN}Type [1-2]: {Colors.RESET}")
        mode = "user" if mode_choice == "2" else "channel"
        
        # Get ID
        if mode == "channel":
            target_id = self.get_input("Channel ID")
        else:
            target_id = self.get_input("User ID")
        
        if not target_id:
            print(f"{Colors.RED}ID is required!{Colors.RESET}")
            time.sleep(2)
            return
        
        # Filename
        filename = self.get_input("Output filename (optional)") or "discord_export.zip"
        if not filename.endswith('.zip'):
            filename += '.zip'
        
        # Confirm
        print(f"\n{Colors.YELLOW}{'─' * 40}{Colors.RESET}")
        print(f"{Colors.WHITE}Token:{Colors.RESET} {token[:20]}...")  # عرض جزئي فقط للأمان
        print(f"{Colors.WHITE}Type:{Colors.RESET} {'DM' if mode == 'user' else 'Channel'}")
        print(f"{Colors.WHITE}Target ID:{Colors.RESET} {target_id}")
        print(f"{Colors.WHITE}Save as:{Colors.RESET} {filename}")
        print(f"{Colors.YELLOW}{'─' * 40}{Colors.RESET}")
        
        confirm = input(f"\n{Colors.YELLOW}Start export? (y/n): {Colors.RESET}").lower()
        
        if confirm == 'y':
            self.running = True
            
            # Show loading
            print(f"{Colors.CYAN}Starting export...{Colors.RESET}")
            time.sleep(1)
            
            # Start export
            success = self.export_chat(token, mode, target_id, filename)
            
            self.running = False
            
            if success:
                input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
            else:
                input(f"\n{Colors.RED}Press Enter to continue...{Colors.RESET}")
    
    def exit_program(self):
        """Exit program"""
        self.clear_screen()
        self.print_banner()
        
        print(f"\n{Colors.GREEN_BOLD}{'═' * 50}{Colors.RESET}")
        print(f"{Colors.GREEN_BOLD}Thank you for using Blackshi Exporter!{Colors.RESET}")
        print(f"{Colors.GREEN}Created by Blackshi{Colors.RESET}")
        print(f"{Colors.GREEN}Telegram: @blackshi{Colors.RESET}")
        print(f"{Colors.GREEN}GitHub: github.com/blackshi{Colors.RESET}")
        print(f"\n{Colors.GREEN}Goodbye! 👋{Colors.RESET}")
        print(f"{Colors.GREEN_BOLD}{'═' * 50}{Colors.RESET}\n")
        
        time.sleep(2)
        sys.exit(0)
    
    def run(self):
        """Run program"""
        try:
            self.show_menu()
        except KeyboardInterrupt:
            self.exit_program()

def main():
    """Main function"""
    try:
        # Check requirements
        try:
            import requests
        except ImportError:
            print("Error: 'requests' module is not installed.")
            print("Install it using: pip install requests")
            return
        
        # Run program
        app = DiscordChatExporter()
        app.run()
        
    except Exception as e:
        print(f"\n{Colors.RED}Fatal Error:{Colors.RESET} {str(e)}")

if __name__ == "__main__":
    main()