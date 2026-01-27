💄 Project: Cosmetic Intelligence Audio Pipeline
📝 项目愿景
本项目旨在打通 化妆品理化检验情报 的最后一公里。通过将 TrendRadar 自动化抓取的行业热点（NMPA 通告、成分研发、监管趋势），自动转化为适合 理化检验室新人 以及行业专家收听的深度音频播客。

🏗️ 当前系统架构 (Status Quo)
情报搜集端 (TrendRadar):

功能: 24小时监控微博、抖音及 Bing/Yahoo RSS 源。

现状: 已成功配置“理化检验专用”过滤器，能精准筛选出 2-5% 的核心情报。

产物: 每日在本地 output/html/YYYY-MM-DD/ 生成包含 AI 简报的 HTML 文档。

音频生成端 (Hacker-Podcast):

功能: 基于文本内容生成多角色对话或单人述评播客。

现状: 已跑通生成流程，但目前仍需手动输入文本素材。

🌉 待打通的“数据桥梁” (The Mission)
我们需要一个 桥接脚本 (Bridge Script) 来实现从“静态 HTML”到“动态播客脚本”的自动转换：

1. 数据监听与提取 (Source)
监控 TrendRadar/output/html/latest/ 目录下的 daily.html 或 current.html。

利用 BeautifulSoup 或 Regex 提取 HTML 中的 [AI 分析区域] 文本内容。

提取该报告中匹配到的 核心新闻标题与来源链接。

2. 脚本重构 (Processing)
输入: TrendRadar 原始 AI 摘要。

处理: 调用 DeepSeek API，将枯燥的监管数据转化为 “理化检验室早茶” 风格的对话脚本。

风格指南: 保持专业严谨，但要有“奶油中古风”般的优雅和“生酮饮食”般的干练。

3. 自动喂料 (Target)
将生成的 Script 自动写入 Hacker-Podcast 指定的输入目录。

触发 Hacker-Podcast 的构建流程，产出最终 .mp3 文件。

🛠️ 技术要求 (For Jule)
路径管理: 适配 Docker 挂载路径，确保脚本能同时访问两个项目的 output 与 input 目录。

触发机制:

方式 A (推荐): 轮询监听 HTML 文件的时间戳更新。

方式 B: 配合 TrendRadar 的 Cron 任务，在每日 19:30 后延时执行。

容错处理:

如果当日匹配新闻为 0，则跳过播客生成。

处理 InternalServerError 等 AI 接口波动问题。

📅 开发计划 (Roadmap)
[ ] Phase 1: 编写 HTML 解析工具类。

[ ] Phase 2: 接入 Podcast 脚本生成模版。

[ ] Phase 3: 联调 Docker 容器间的数据同步。

[ ] Phase 4: 实现飞书机器人自动推送生成的播客下载链接。
