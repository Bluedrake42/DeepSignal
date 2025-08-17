#!/usr/bin/env python3
import eel, threading, time, requests, webbrowser, platform
from app import app

eel.init('templates')

def run_flask():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def wait_flask():
    for _ in range(30):
        try:
            if requests.get('http://127.0.0.1:5000', timeout=1).status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    return False

def main():
    print("🚀 Starting Flask desktop app...")
    
    threading.Thread(target=run_flask, daemon=True).start()
    
    if not wait_flask():
        print("❌ Flask failed to start")
        return
    
    print("✅ Flask ready, opening desktop window...")
    
    url = 'http://127.0.0.1:5000'
    
    try:
        eel.start(url, mode='chrome', port=8080, size=(1200, 800),
                 cmdline_args=[f'--app={url}', '--no-first-run'])
    except:
        try:
            eel.start(url, mode='edge', port=8080, size=(1200, 800),
                     cmdline_args=[f'--app={url}'])
        except:
            webbrowser.open(url)

if __name__ == "__main__":
    main()
