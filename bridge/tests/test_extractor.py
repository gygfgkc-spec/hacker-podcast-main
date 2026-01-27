import unittest
import os
from bridge.extractor import ReportExtractor

class TestExtractor(unittest.TestCase):
    def setUp(self):
        self.test_html = "test_daily.html"
        with open(self.test_html, "w", encoding="utf-8") as f:
            f.write("""
            <div class="ai-section">
                <div class="ai-block">
                    <div class="ai-block-title">Analysis 1</div>
                    <div class="ai-block-content">Content 1</div>
                </div>
            </div>
            <div class="news-item">
                <div class="news-title">News 1</div>
                <span class="source-name">Source A</span>
            </div>
            """)

    def tearDown(self):
        if os.path.exists(self.test_html):
            os.remove(self.test_html)

    def test_extraction(self):
        extractor = ReportExtractor(self.test_html)
        self.assertTrue(extractor.is_valid())

        analysis = extractor.get_ai_analysis()
        self.assertIn("【Analysis 1】", analysis)
        self.assertIn("Content 1", analysis)

        news = extractor.get_hot_news()
        self.assertEqual(len(news), 1)
        self.assertEqual(news[0]['title'], "News 1")
        self.assertEqual(news[0]['source'], "Source A")

if __name__ == '__main__':
    unittest.main()
