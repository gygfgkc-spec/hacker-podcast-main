from bs4 import BeautifulSoup
import os
import logging

logger = logging.getLogger(__name__)

class ReportExtractor:
    def __init__(self, html_path):
        self.html_path = html_path
        self.content = self._load_html()
        self.soup = BeautifulSoup(self.content, 'html.parser')

    def _load_html(self):
        if not os.path.exists(self.html_path):
            raise FileNotFoundError(f"HTML file not found: {self.html_path}")
        with open(self.html_path, 'r', encoding='utf-8') as f:
            return f.read()

    def get_ai_analysis(self):
        """Extracts the AI analysis sections."""
        ai_section = self.soup.find('div', class_='ai-section')
        if not ai_section:
            logger.warning("No .ai-section found in HTML")
            return ""

        analysis_text = ""
        # 提取所有 ai-block 的内容
        blocks = ai_section.find_all('div', class_='ai-block')
        if not blocks:
            # 可能是旧版本或者结构不同，尝试直接获取 ai-section 文本
             return ai_section.get_text(separator="\n", strip=True)

        for block in blocks:
            title = block.find('div', class_='ai-block-title')
            content = block.find('div', class_='ai-block-content')

            if title:
                analysis_text += f"【{title.get_text(strip=True)}】\n"
            if content:
                text = content.get_text(separator='\n', strip=True)
                analysis_text += f"{text}\n\n"

        return analysis_text

    def get_hot_news(self):
        """Extracts hot news titles and sources."""
        news_items = self.soup.find_all('div', class_='news-item')
        extracted_news = []

        for item in news_items:
            title_tag = item.find('div', class_='news-title')
            source_tag = item.find('span', class_='source-name')

            if title_tag:
                title = title_tag.get_text(strip=True)
                source = source_tag.get_text(strip=True) if source_tag else "Unknown"
                # 还可以提取链接
                link_tag = item.find('a', class_='news-link')
                link = link_tag['href'] if link_tag else ""

                extracted_news.append({
                    "title": title,
                    "source": source,
                    "url": link
                })

        return extracted_news

    def is_valid(self):
        """Checks if the extraction yielded meaningful results."""
        # 只要有新闻或者有分析就算有效
        return bool(self.get_hot_news() or self.get_ai_analysis())

if __name__ == "__main__":
    # Test run
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        extractor = ReportExtractor(path)
        print("=== AI Analysis ===")
        print(extractor.get_ai_analysis())
        print("\n=== Top 5 News ===")
        for news in extractor.get_hot_news()[:5]:
            print(f"- {news['title']} ({news['source']})")
