# coding=utf-8
"""
AI 分析结果格式化模块

将 AI 分析结果格式化为各推送渠道的样式
"""

import html as html_lib
import re
from .analyzer import AIAnalysisResult


def _escape_html(text: str) -> str:
    """转义 HTML 特殊字符，防止 XSS 攻击"""
    return html_lib.escape(text) if text else ""


def _format_list_content(text: str) -> str:
    """
    格式化列表内容，确保序号前有换行
    """
    if not text:
        return ""
    
    text = text.strip()
    result = re.sub(r'(\d+)\.([^ \d])', r'\1. \2', text)
    result = re.sub(r'(?<=[^\n])\s+(\d+\.)', r'\n\1', result)
    result = re.sub(r'(?<=[^\n])(\d+\.\*\*)', r'\n\1', result)
    result = re.sub(r'([：:;,。；，])\s*(\d+\.)', r'\1\n\2', result)
    result = re.sub(r'([。！？；，、])\s*([a-zA-Z0-9\u4e00-\u9fa5]+(方面|领域)[:：])', r'\1\n\2', result)
    result = re.sub(r'(?<=[^\n])\s*(【[^】]+】[:：])', r'\n\n\1', result)
    result = re.sub(r'(?<![:：])\n(\d+\.)', r'\n\n\1', result)

    return result


def render_ai_analysis_markdown(result: AIAnalysisResult) -> str:
    """渲染为通用 Markdown 格式"""
    if not result.success:
        return f"⚠️ AI 分析失败: {result.error}"

    lines = ["**✨ AI 财经分析**", ""]

    if result.csi300_analysis:
        lines.extend(["**国内股票：沪深300大盘分析**", _format_list_content(result.csi300_analysis), ""])

    if result.tech_analysis:
        lines.extend(
            ["**科技股：小盘与成长分析**", _format_list_content(result.tech_analysis), ""]
        )

    if result.gold_analysis:
        lines.extend(["**黄金与避险资产分析**", _format_list_content(result.gold_analysis), ""])

    return "\n".join(lines)


def render_ai_analysis_feishu(result: AIAnalysisResult) -> str:
    """渲染为飞书卡片 Markdown 格式"""
    if not result.success:
        return f"⚠️ AI 分析失败: {result.error}"

    lines = ["**✨ AI 财经分析**", ""]

    if result.csi300_analysis:
        lines.extend(["**国内股票：沪深300大盘分析**", _format_list_content(result.csi300_analysis), ""])

    if result.tech_analysis:
        lines.extend(
            ["**科技股：小盘与成长分析**", _format_list_content(result.tech_analysis), ""]
        )

    if result.gold_analysis:
        lines.extend(["**黄金与避险资产分析**", _format_list_content(result.gold_analysis), ""])

    return "\n".join(lines)


def render_ai_analysis_dingtalk(result: AIAnalysisResult) -> str:
    """渲染为钉钉 Markdown 格式"""
    if not result.success:
        return f"⚠️ AI 分析失败: {result.error}"

    lines = ["### ✨ AI 财经分析", ""]

    if result.csi300_analysis:
        lines.extend(
            ["#### 国内股票：沪深300大盘分析", _format_list_content(result.csi300_analysis), ""]
        )

    if result.tech_analysis:
        lines.extend(
            [
                "#### 科技股：小盘与成长分析",
                _format_list_content(result.tech_analysis),
                "",
            ]
        )

    if result.gold_analysis:
        lines.extend(["#### 黄金与避险资产分析", _format_list_content(result.gold_analysis), ""])

    return "\n".join(lines)


def render_ai_analysis_html(result: AIAnalysisResult) -> str:
    """渲染为 HTML 格式（邮件）"""
    if not result.success:
        return (
            f'<div class="ai-error">⚠️ AI 分析失败: {_escape_html(result.error)}</div>'
        )

    html_parts = ['<div class="ai-analysis">', "<h3>✨ AI 财经分析</h3>"]

    if result.csi300_analysis:
        content = _format_list_content(result.csi300_analysis)
        content_html = _escape_html(content).replace("\n", "<br>")
        html_parts.extend(
            [
                '<div class="ai-section">',
                "<h4>国内股票：沪深300大盘分析</h4>",
                f'<div class="ai-content">{content_html}</div>',
                "</div>",
            ]
        )

    if result.tech_analysis:
        content = _format_list_content(result.tech_analysis)
        content_html = _escape_html(content).replace("\n", "<br>")
        html_parts.extend(
            [
                '<div class="ai-section">',
                "<h4>科技股：小盘与成长分析</h4>",
                f'<div class="ai-content">{content_html}</div>',
                "</div>",
            ]
        )

    if result.gold_analysis:
        content = _format_list_content(result.gold_analysis)
        content_html = _escape_html(content).replace("\n", "<br>")
        html_parts.extend(
            [
                '<div class="ai-section">',
                "<h4>黄金与避险资产分析</h4>",
                f'<div class="ai-content">{content_html}</div>',
                "</div>",
            ]
        )

    html_parts.append("</div>")
    return "\n".join(html_parts)


def render_ai_analysis_plain(result: AIAnalysisResult) -> str:
    """渲染为纯文本格式"""
    if not result.success:
        return f"AI 分析失败: {result.error}"

    lines = ["【✨ AI 财经分析】", ""]

    if result.csi300_analysis:
        lines.extend(["[国内股票：沪深300大盘分析]", _format_list_content(result.csi300_analysis), ""])

    if result.tech_analysis:
        lines.extend(
            ["[科技股：小盘与成长分析]", _format_list_content(result.tech_analysis), ""]
        )

    if result.gold_analysis:
        lines.extend(["[黄金与避险资产分析]", _format_list_content(result.gold_analysis), ""])

    return "\n".join(lines)


def get_ai_analysis_renderer(channel: str):
    """根据渠道获取对应的渲染函数"""
    renderers = {
        "feishu": render_ai_analysis_feishu,
        "dingtalk": render_ai_analysis_dingtalk,
        "wework": render_ai_analysis_markdown,
        "telegram": render_ai_analysis_markdown,
        "email": render_ai_analysis_html_rich,  # 邮件使用丰富样式，配合 HTML 报告的 CSS
        "ntfy": render_ai_analysis_markdown,
        "bark": render_ai_analysis_plain,
        "slack": render_ai_analysis_markdown,
    }
    return renderers.get(channel, render_ai_analysis_markdown)


def render_ai_analysis_html_rich(result: AIAnalysisResult) -> str:
    """渲染为丰富样式的 HTML 格式（HTML 报告用）"""
    if not result:
        return ""

    # 检查是否成功
    if not result.success:
        error_msg = result.error or "未知错误"
        return f"""
                <div class="ai-section">
                    <div class="ai-error">⚠️ AI 分析失败: {_escape_html(str(error_msg))}</div>
                </div>"""

    ai_html = """
                <div class="ai-section">
                    <div class="ai-section-header">
                        <div class="ai-section-title">✨ AI 财经分析</div>
                        <span class="ai-section-badge">AI</span>
                    </div>"""

    if result.csi300_analysis:
        content = _format_list_content(result.csi300_analysis)
        content_html = _escape_html(content).replace("\n", "<br>")
        ai_html += f"""
                    <div class="ai-block">
                        <div class="ai-block-title">国内股票：沪深300大盘分析</div>
                        <div class="ai-block-content">{content_html}</div>
                    </div>"""

    if result.tech_analysis:
        content = _format_list_content(result.tech_analysis)
        content_html = _escape_html(content).replace("\n", "<br>")
        ai_html += f"""
                    <div class="ai-block">
                        <div class="ai-block-title">科技股：小盘与成长分析</div>
                        <div class="ai-block-content">{content_html}</div>
                    </div>"""

    if result.gold_analysis:
        content = _format_list_content(result.gold_analysis)
        content_html = _escape_html(content).replace("\n", "<br>")
        ai_html += f"""
                    <div class="ai-block">
                        <div class="ai-block-title">黄金与避险资产分析</div>
                        <div class="ai-block-content">{content_html}</div>
                    </div>"""

    ai_html += """
                </div>"""
    return ai_html
