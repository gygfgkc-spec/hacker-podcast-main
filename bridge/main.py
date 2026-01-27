import time
import os
import logging
import requests
import sys
from datetime import datetime
from extractor import ReportExtractor
from generator import ScriptGenerator

# Configuration
# Docker 内部路径 (假设 TrendRadar output 挂载到了 /app/trend_output)
HTML_PATH = os.getenv("HTML_PATH", "/app/trend_output/html/latest/daily.html")
WORKER_URL = os.getenv("WORKER_URL", "http://hacker-podcast:8787/api/cron")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300")) # 5 minutes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Bridge")

def process_daily_report():
    logger.info(f"Checking for report at {HTML_PATH}...")

    if not os.path.exists(HTML_PATH):
        logger.info("Report file not found yet.")
        return False

    # Check if file is fresh (e.g., modified today)
    # 简单起见，这里假设只要文件存在就处理。
    # 实际生产中可能需要记录上次处理的时间戳，避免重复处理。
    # 这里我们用一个简单的标记文件
    processed_marker = HTML_PATH + ".processed"

    if os.path.exists(processed_marker):
        # 比较修改时间，如果 html 比 marker 新，说明更新了
        html_mtime = os.path.getmtime(HTML_PATH)
        marker_mtime = os.path.getmtime(processed_marker)
        if html_mtime <= marker_mtime:
            logger.info("Report already processed. Skipping.")
            return False

    logger.info("New report found! Starting processing...")

    try:
        # 1. Extract
        extractor = ReportExtractor(HTML_PATH)
        if not extractor.is_valid():
            logger.warning("Extracted content is empty or invalid.")
            return False

        ai_analysis = extractor.get_ai_analysis()
        hot_news = extractor.get_hot_news()

        logger.info(f"Extracted {len(hot_news)} news items.")

        # 2. Generate
        generator = ScriptGenerator()
        script = generator.generate_script(ai_analysis, hot_news)

        if not script:
            logger.error("Generated script is empty.")
            return False

        logger.info("Script generated successfully. Length: " + str(len(script)))

        # 3. Send to Hacker-Podcast
        logger.info(f"Sending to Worker at {WORKER_URL}...")
        payload = {
            "today": datetime.now().strftime("%Y-%m-%d"),
            "custom_script": script
        }

        response = requests.post(WORKER_URL, json=payload, timeout=30)

        if response.status_code == 200:
            logger.info("✅ Successfully triggered Hacker-Podcast processing!")
            # Update marker
            with open(processed_marker, 'w') as f:
                f.write(str(datetime.now().timestamp()))
            return True
        else:
            logger.error(f"❌ Worker returned status {response.status_code}: {response.text}")
            return False

    except Exception as e:
        logger.exception(f"Error during processing: {e}")
        return False

def run_loop():
    logger.info("Starting Bridge Service (Polling Mode)")
    logger.info(f"Watching: {HTML_PATH}")
    logger.info(f"Target: {WORKER_URL}")

    while True:
        try:
            process_daily_report()
        except Exception as e:
            logger.error(f"Unexpected error in loop: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    # check for command line arg "once"
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        process_daily_report()
    else:
        run_loop()
