📈 Project: Financial Intelligence Audio Pipeline (财经早茶)
📝 项目愿景
本项目旨在为 **A股/美股/黄金投资者** 打造一个全自动的情报与决策辅助系统。
通过自动化抓取全网财经热点（华尔街见闻、财新、金十数据），利用 AI 进行深度复盘分析，并自动生成适合上下班路上收听的 **“老股民 VS 分析师”** 风格的财经播客。

🏗️ 系统架构
1. 情报搜集与分析 (TrendRadar - Finance Edition)
- **功能**: 24小时监控微博财经热搜、雪球、知乎及各大财经 RSS 源。
- **AI 分析**: 每天定时对抓取到的数千条新闻进行清洗，并针对 **“大盘风向(沪深300)”、“科技前沿”、“黄金避险”** 三大板块进行深度研判。
- **产物**: 每日生成包含 AI 投资建议的 HTML 研报，并**推送到飞书**。

2. 桥接与脚本生成 (Bridge Script)
- **功能**: 监听 TrendRadar 的研报生成。
- **处理**: 调用 DeepSeek API，将严肃的研报转化为 **“老张(散户) 与 小王(分析师)”** 的幽默对话脚本。
- **风格**: 拒绝八股文，充满“韭菜味”的真实感与数据支撑的专业度。

3. 音频生成 (Hacker-Podcast)
- **功能**: 接收 Bridge 传来的脚本，利用 Edge-TTS 生成逼真的多角色语音。
- **产物**: 最终生成 MP3 播客文件，并更新 RSS Feed。

🚀 快速开始
1. 配置环境
复制 `.env.example` 为 `.env`，并填入您的 API Key：
```bash
AI_API_KEY=sk-xxxxxxxxxxxxxx
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxx
```

2. 启动服务
```bash
docker-compose up -d
```

3. 访问服务
- **TrendRadar 控制台**: `http://localhost:8080` (查看原始情报)
- **Podcast Worker**: `http://localhost:8787` (音频生成后台)

🤖 AI 分析板块说明
系统会自动将新闻分类并分析以下三个核心领域：
1.  **大盘风向标**：侧重沪深300、央行政策、北向资金，回答“明天涨不涨”。
2.  **科技前沿**：侧重 AI、芯片、半导体，寻找“硬科技”机会。
3.  **黄金与避险**：侧重金价、美元指数、地缘政治，判断“乱世买金”的时机。

🛠️ 技术栈
- **TrendRadar**: Python, BeautifulSoup, SQLite
- **Bridge**: Python, OpenAI SDK
- **Hacker-Podcast**: Cloudflare Workers, TypeScript, Edge-TTS
- **Docker**: 全栈容器化部署
