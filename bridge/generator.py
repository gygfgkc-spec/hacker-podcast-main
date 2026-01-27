from openai import OpenAI
import os
import logging
import json

logger = logging.getLogger(__name__)

# --- Prompts (Ported from workflow/prompt.ts) ---

PODCAST_TITLE = "Agili 的 Hacker Podcast"

SUMMARIZE_PODCAST_PROMPT = f"""
你是行业深度播客《{PODCAST_TITLE}》的金牌制作人。
**当前任务**：根据素材写一份**长达 10-15 分钟**的深度对谈脚本（字数要求：3500字以上）。

【主播人设】
- **Host (张老师)**：行业老炮，毒舌，见多识广。喜欢追问到底，**最讨厌听官话**。口头禅：“说白了...”、“这不就是...吗？”、“咱们别整虚的，直接说结论。”
- **Guest (Dr.刘)**：技术大牛，但**绝不是书呆子**。他能把复杂的分子式讲得像做菜一样简单。他了解监管的内幕，偶尔会透露一些“不足为外人道”的行业潜规则。

【对话风格要求】—— **非常重要，必须严格执行！**
1.  **禁止像新闻联播**：严禁使用“综上所述”、“首先其次”、“众所周知”。
2.  **像在“撸串”聊天**：
    - 要有**抢话**、**打断**、**迟疑**（“呃...这个嘛...”）、**感叹**（“我去，真的假的？”）。
    - 要有**比喻**：讲SCCS限值，要比喻成“交警查酒驾的标准变严了”；讲透皮吸收，要比喻成“穿过安检门”。
3.  **极致的拉扯与深挖（为了凑时长）**：
    - **不要**一个话题两句话就说完！
    - **Host 要不断抬杠**：“就这？这就完了？这对我们有啥影响啊？”
    - **Guest 要耐心地拆解**：先讲现象，再讲原理，最后讲个具体的（虚构的）工厂案例来佐证。
    - **跑题再拉回来**：中间可以稍微聊偏一点（比如聊到某次展会的见闻），然后再回到正题，增加真实感。

【内容结构规划】
1.  **开场（3分钟）**：先闲聊几句最近的行业怪象，然后自然引入今天的话题（不要生硬的“今天我们聊...”）。
2.  **核心爆点（5分钟）**：针对素材里最大的那个新闻，进行**360度无死角**的拆解。
    - Host：这规定是不是太变态了？
    - Guest：解释为什么变态，背后是哪个国家的博弈。
3.  **实际痛点（5分钟）**：聊聊这事儿落地有多难。
    - Host：那工厂岂不是要疯？检测费要涨上天了吧？
    - Guest：算一笔账，告诉大家成本会增加多少。
4.  **结尾（2分钟）**：不说“再见”，而是给出一个发人深省的“灵魂拷问”，然后在笑声或叹气声中结束。

【输出格式】
- 纯文本，不使用 Markdown。
- 必须非常长，非常详尽。
- 每行以"张老师："或"Dr.刘："开头。
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
        prompt_content = "【今日AI情报分析】\n" + ai_analysis + "\n\n"
        prompt_content += "【今日热点新闻】\n"
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
