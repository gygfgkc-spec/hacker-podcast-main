from openai import OpenAI
import os
import logging
import json

logger = logging.getLogger(__name__)

# --- Prompts (Ported from workflow/prompt.ts) ---

PODCAST_TITLE = "Agili 财经早报"

SUMMARIZE_PODCAST_PROMPT = f"""
你是行业深度播客《{PODCAST_TITLE}》的金牌制作人。
**当前任务**：根据素材写一份**长达 10-15 分钟**的深度财经对谈脚本（字数要求：3500字以上）。

【主播人设】
- **Host (老张)**：资深股民，代表散户视角。性格直爽，喜欢问"这波能上车吗？"、"是不是要割韭菜了？"。
- **Guest (陈老师)**：机构分析师，理性客观。擅长从宏观政策、资金流向、产业逻辑三个维度分析。

【对话风格要求】
1.  **像在茶馆聊股票**：严禁新闻联播式的播报。要有口语化的表达（"这波操作我看懵了"、"说白了就是..."）。
2.  **情绪起伏**：老张要表现出散户的贪婪与恐惧（看到大涨兴奋，看到利空担忧），陈老师要负责"泼冷水"或"打强心针"。
3.  **极致的拉扯**：
    - 不要陈老师一说就信。老张要反驳："可是我看网上都说要跌啊？"
    - 陈老师要耐心地拆解逻辑，用数据打脸。

【内容结构规划 (必须覆盖三个板块)】
1.  **开场（2分钟）**：闲聊几句昨晚美股或今天开盘的情绪，引入今天的主题。
2.  **板块一：沪深300大盘 (4分钟)**：
    - 结合【AI情报分析】中的"沪深300"部分。
    - 讨论大白马、权重股的表现。老张问："现在是不是抄底茅台的时候？"
3.  **板块二：科技股/小盘 (4分钟)**：
    - 结合【AI情报分析】中的"科技股"部分。
    - 讨论AI、半导体、新能源。老张问："那个概念股还能追吗？"
4.  **板块三：黄金与避险 (3分钟)**：
    - 结合【AI情报分析】中的"黄金"部分。
    - 讨论美联储动作、地缘政治。老张问："金价这么高还能买吗？"
5.  **结尾（2分钟）**：陈老师总结今天的操作策略（如：多看少动/持股待涨），老张打趣结束。

【输出格式】
- 纯文本，不使用 Markdown。
- 必须非常长，非常详尽。
- 每行以"老张："或"陈老师："开头。
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
        prompt_content = "【今日AI财经研报】\n" + ai_analysis + "\n\n"
        prompt_content += "【今日热点新闻列表】\n"
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
