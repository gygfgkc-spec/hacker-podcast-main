from openai import OpenAI
import os
import logging
import json

logger = logging.getLogger(__name__)

# --- Prompts (Ported from workflow/prompt.ts - Finance Edition) ---

PODCAST_TITLE = "Agili 的 财经早茶"

SUMMARIZE_PODCAST_PROMPT = f"""
你是财经脱口秀《{PODCAST_TITLE}》的制作人。
**当前任务**：写一份**10-15分钟**的深度复盘与推演脚本（字数3500字以上）。

【主播人设】
- **Host (老张)**：拥有15年股龄的老股民，经历过07年6000点和15年股灾。心态稳（其实是被套怕了），喜欢讲段子，对市场充满了“爱之深责之切”的吐槽。口头禅：“这波操作我给满分”、“护盘还得看...”
- **Guest (分析师小王)**：量化交易员出身，数据党，逻辑严密，专门负责用数据打脸老张的情绪化。他看重宏观周期和产业逻辑，偶尔会蹦出几个专业术语然后被老张打断。

【对话风格要求】
1.  **像在路边摊撸串聊股票**：
    - 老张：负责代表散户的情绪（追涨杀跌、骂主力、找安慰）。
    - 小王：负责理智分析（泼冷水、画大饼、讲逻辑）。
2.  **必须包含三个固定板块的讨论**：
    - **第一部分：大盘风向（沪深300）**。老张吐槽今天账户又缩水了，小王分析宏观原因（央行、汇率等）。
    - **第二部分：科技前沿（科技股）**。聊聊AI、芯片的新动态。老张问“能追吗？”，小王讲估值和风险。
    - **第三部分：黄金避险**。聊聊金价和国际局势。是不是该买黄金避险了？
3.  **极致的拉扯**：
    - 老张：“别扯那些没用的，你就告诉我明天涨不涨？”
    - 小王：“短期看情绪，长期看国运。不过从数据看...”

【输出格式】
- 纯文本，不使用 Markdown。
- 必须非常长，非常详尽。
- 每行以"老张："或"小王："开头。
""".strip()

class ScriptGenerator:
    def __init__(self, api_key=None, base_url=None, model="deepseek-chat"):
        self.api_key = api_key or os.getenv("AI_API_KEY")
        self.base_url = base_url or os.getenv("AI_BASE_URL", "https://api.deepseek.com")
        self.model = model or os.getenv("AI_MODEL", "deepseek-chat")

        if not self.api_key:
            raise ValueError("AI_API_KEY environment variable is not set")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def generate_script(self, ai_analysis, news_list):
        """Generates the podcast script based on extracted content."""

        # Construct the prompt content
        prompt_content = "【今日AI财经深度分析】\n" + ai_analysis + "\n\n"
        prompt_content += "【今日财经热点】\n"
        for news in news_list:
            prompt_content += f"- {news['title']} (来源: {news['source']})\n"

        logger.info(f"Generating script with model {self.model}...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SUMMARIZE_PODCAST_PROMPT},
                    {"role": "user", "content": prompt_content}
                ],
                temperature=1.3, # High temperature for creativity/liveliness
                max_tokens=8192
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            raise

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    try:
        gen = ScriptGenerator()
        print("Generator initialized successfully.")
    except Exception as e:
        print(f"Initialization failed (expected if no API key): {e}")
