import type { WorkflowEvent, WorkflowStep, WorkflowStepConfig } from 'cloudflare:workers'
import { createOpenAICompatible } from '@ai-sdk/openai-compatible'
import { generateText } from 'ai'
import { WorkflowEntrypoint } from 'cloudflare:workers'
import { podcastTitle } from '@/config'
import { introPrompt, summarizeBlogPrompt, summarizePodcastPrompt, summarizeStoryPrompt } from './prompt'
import synthesize from './tts'
import { concatAudioFiles } from './utils'

interface Params {
  today?: string
}

interface Env extends CloudflareEnv {
  OPENAI_BASE_URL: string
  OPENAI_API_KEY: string
  OPENAI_MODEL: string
  OPENAI_THINKING_MODEL?: string
  OPENAI_MAX_TOKENS?: string
  NODE_ENV: string
  HACKER_PODCAST_WORKER_URL: string
  HACKER_PODCAST_R2_BUCKET_URL: string
  HACKER_PODCAST_KV: KVNamespace
  HACKER_PODCAST_R2: R2Bucket
  HACKER_PODCAST_WORKFLOW: Workflow
  BROWSER: Fetcher
}

const retryConfig: WorkflowStepConfig = {
  retries: {
    limit: 1,
    delay: '1 seconds',
    backoff: 'linear',
  },
  timeout: '30 minutes',
}

// --- 1. 数据源：使用 RSSHub 获取垂直频道 ---
// 相比全站 RSS，这些频道的噪音少很多，而且格式标准
const DATA_SOURCES = [
  // 36氪 - 消费领域 (包含了美妆、零售)
  {
    name: "36Kr Consumer",
    url: "https://rsshub.app/36kr/information/happy_life", 
    type: "rsshub"
  },
  // 界面新闻 - 消费频道
  {
    name: "Jiemian Consumer",
    url: "https://rsshub.app/jiemian/list/108",
    type: "rsshub"
  },
  // 亿邦动力 - 跨境电商/美妆 (很多出海新闻)
  {
    name: "Ebrun",
    url: "https://rsshub.app/ebrun/news",
    type: "rsshub"
  },
  // 补充：雅虎香港 (搜化妆品) - 这个最稳，作为保底
  {
    name: "Yahoo HK",
    url: "https://hk.news.yahoo.com/rss/search?p=化妝品",
    type: "yahoo"
  }
];

// 简单的 XML 解析，不再做关键词过滤，全部保留交给 AI
function parseRSS(xml: string, sourceName: string) {
  const items: any[] = [];
  const itemRegex = /<item>([\s\S]*?)<\/item>/g;
  let match;
  
  while ((match = itemRegex.exec(xml)) !== null) {
    const content = match[1];
    
    // 提取标题
    const titleMatch = content.match(/<title>([\s\S]*?)<\/title>/);
    let title = "";
    if (titleMatch) title = titleMatch[1].replace(/<!\[CDATA\[|\]\]>/g, '').trim();

    // 提取链接
    const linkMatch = content.match(/<link>([\s\S]*?)<\/link>/);
    let link = "";
    if (linkMatch) link = linkMatch[1].trim();

    // 提取描述
    let desc = '';
    const descMatch = content.match(/<description>([\s\S]*?)<\/description>/);
    if (descMatch) desc = descMatch[1].replace(/<!\[CDATA\[|\]\]>|<[^>]+>/g, '').trim();

    // 提取时间
    let time = Date.now();
    const dateMatch = content.match(/<pubDate>([\s\S]*?)<\/pubDate>/);
    if (dateMatch) {
       const t = Date.parse(dateMatch[1]);
       if (!isNaN(t)) time = t;
    }

    if (title && link) {
      items.push({
        id: link, // 使用链接作为唯一ID
        title: title,
        url: link,
        description: desc.substring(0, 100), // 只要前100字给AI判断即可
        time: time,
        source: sourceName
      });
    }
  }
  return items;
}

export class HackerNewsWorkflow extends WorkflowEntrypoint<Env, Params> {
  async run(event: WorkflowEvent<Params>, step: WorkflowStep) {
    console.info('trigged event: HackerNewsWorkflow', event)
    const runEnv = this.env.NODE_ENV || 'production'
    const today = event.payload?.today || new Date().toISOString().split('T')[0]
    
    // AI Setup
    const apiKey = (this.env.OPENAI_API_KEY || '').trim();
    let baseURL = (this.env.OPENAI_BASE_URL || '').trim();
    if (baseURL.endsWith('/')) baseURL = baseURL.slice(0, -1);
    const openai = createOpenAICompatible({
      name: 'openai', baseURL: baseURL, headers: { Authorization: `Bearer ${apiKey}` },
    })
    
    // --- Step 1: 抓取原始数据 (不过滤) ---
    const rawStories = await step.do(`fetch raw news`, retryConfig, async () => {
      let collected: any[] = [];
      
      await Promise.all(DATA_SOURCES.map(async (source) => {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 20000);
          
          const response = await fetch(source.url, {
            headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' },
            signal: controller.signal
          });
          clearTimeout(timeoutId);

          if (response.ok) {
            const text = await response.text();
            const items = parseRSS(text, source.name);
            console.info(`✅ [${source.name}] 获取到 ${items.length} 条原始数据`);
            collected = collected.concat(items);
          } else {
            console.warn(`❌ [${source.name}] HTTP ${response.status}`);
          }
        } catch (e: any) {
          console.warn(`⏳ [${source.name}] Error: ${e.message}`);
        }
      }));
      
      // 去重
      const unique = Array.from(new Map(collected.map(item => [item.title, item])).values());
      return unique; // 返回所有乱七八糟的新闻
    });

    console.info(`Total raw stories: ${rawStories.length}`);

    // --- Step 2: AI 智能筛选 (核心！) ---
    const targetStories = await step.do(`ai filtering`, retryConfig, async () => {
      if (rawStories.length === 0) return [];

      // 准备给 AI 的清单 (只给标题和ID，节省 Token)
      const listForAI = rawStories.map((s, index) => ({
        index: index,
        title: s.title,
        source: s.source
      }));

      // AI 指令：把电子木鱼和汽车踢出去！
      const prompt = `
      你是专业的化妆品行业主编。下面是一组新闻标题。
      请仔细筛选出**真正属于“化妆品、美妆、医美、原料、护肤”行业**的新闻。
      
      【排除规则】：
      1. 坚决排除“汽车、电子产品、股票大盘、游戏、半导体”。
      2. 排除“消费电子”、“电子木鱼”等无关消费品。
      3. 排除纯粹的电商大促广告（如仅仅是带货）。
      
      【保留规则】：
      1. 保留欧莱雅、雅诗兰黛等美妆巨头的财报或动态。
      2. 保留药监局、新原料、合成生物等技术新闻。
      3. 保留医美、护肤品市场分析。

      请返回一个纯 JSON 数组，只包含保留新闻的 index 值。例如：[0, 5, 12]
      如果没有相关的，返回 []。
      
      新闻列表：
      ${JSON.stringify(listForAI)}
      `;

      try {
        const { text } = await generateText({
          model: openai(this.env.OPENAI_MODEL!), // 用便宜快速的模型筛选即可，或者用 R1
          prompt: prompt,
        });

        // 解析 AI 返回的 JSON
        const jsonMatch = text.match(/\[.*\]/s);
        if (jsonMatch) {
            const validIndexes = JSON.parse(jsonMatch[0]);
            console.info(`🤖 AI 选中了 ${validIndexes.length} 条新闻`);
            // 根据 index 找回原始对象
            return rawStories.filter((_, idx) => validIndexes.includes(idx));
        } else {
            console.warn("AI 返回格式错误，无法解析");
            return [];
        }
      } catch (e) {
        console.error("AI 筛选失败", e);
        return [];
      }
    });

    // 检查 AI 筛选结果
    let finalStories = targetStories;
    if (finalStories.length === 0) {
        console.warn("🚨 AI 筛选后为 0 条 (或抓取失败)，启用系统保底...");
        finalStories = [{
          id: 'fallback-001',
          title: '行业洞察：美妆市场的技术变革与合规挑战',
          url: 'https://news.baidu.com',
          description: '今日无重大新闻。AI 建议讨论话题：1. 重组胶原蛋白的团标落地影响；2. 国货品牌出海东南亚的机遇。',
          time: Date.now(),
          score: 100
        }];
    }
    
    // 截取前 15 条
    finalStories = finalStories.slice(0, 15);
    console.info('Final stories titles:', JSON.stringify(finalStories.map(s => s.title)));

    // --- Step 3: 后面流程照旧 (阅读 -> 总结 -> 播客) ---
    
    // ... (后续流程完全复用之前的) ...
    for (const story of finalStories) {
      const storyResponse = await step.do(`read story ${story.id.substring(0, 10)}...`, retryConfig, async () => {
        if (story.id.includes('fallback')) return `标题：${story.title}\n内容：\n${story.description}`;
        
        let content = '';
        const jinaUrl = `https://r.jina.ai/${story.url}`;
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000);
            const res = await fetch(jinaUrl, { headers: { 'X-Return-Format': 'markdown' }, signal: controller.signal });
            clearTimeout(timeoutId);
            if (res.ok) {
                const text = await res.text();
                if (text.length > 50 && !text.includes("Just a moment")) content = text.substring(0, 4000);
            }
        } catch (e) { console.warn(`Read error: ${story.title}`); }
        if (!content) content = story.description || "无正文";
        return `标题：${story.title}\n内容：\n${content}`;
      });

      const text = await step.do(`summarize ${story.title.substring(0, 5)}`, retryConfig, async () => {
        const { text } = await generateText({ model: openai(this.env.OPENAI_MODEL!), system: summarizeStoryPrompt, prompt: storyResponse });
        return text;
      });

      await step.do(`store summary`, retryConfig, async () => {
         const storyKey = `tmp:${event.instanceId}:story:${story.title.substring(0, 10)}`;
         await this.env.HACKER_PODCAST_KV.put(storyKey, `<story>${text}</story>`, { expirationTtl: 3600 });
         return storyKey;
      });
    }

    // 重新获取摘要列表
    const summaryList = await step.do('fetch summaries', retryConfig, async () => {
       const list = await this.env.HACKER_PODCAST_KV.list({ prefix: `tmp:${event.instanceId}:story:` });
       const texts = [];
       for (const key of list.keys) {
         const val = await this.env.HACKER_PODCAST_KV.get(key.name);
         if (val) texts.push(val);
       }
       return texts;
    });

    // 生成播客脚本
    const podcastContent = await step.do('create podcast', retryConfig, async () => {
      const promptContent = summaryList.length > 0 ? summaryList.join('\n\n---\n\n') : JSON.stringify(finalStories);
      const { text } = await generateText({
        model: openai(this.env.OPENAI_THINKING_MODEL || this.env.OPENAI_MODEL!),
        system: summarizePodcastPrompt,
        prompt: promptContent,
        maxOutputTokens: 8192,
      });
      return text;
    });

    // 生成博客
    const blogContent = await step.do('create blog', retryConfig, async () => {
      const { text } = await generateText({
        model: openai(this.env.OPENAI_THINKING_MODEL || this.env.OPENAI_MODEL!),
        system: summarizeBlogPrompt,
        prompt: summaryList.join('\n\n---\n\n'),
        maxOutputTokens: 4096,
      });
      return text;
    });

    // 生成简介
    const introContent = await step.do('create intro', retryConfig, async () => {
      const { text } = await generateText({ model: openai(this.env.OPENAI_MODEL!), system: introPrompt, prompt: podcastContent });
      return text;
    });

    // TTS & 保存
    const contentKey = `content:${runEnv}:hacker-podcast:${today}`;
    const podcastKey = `${today.replaceAll('-', '/')}/${runEnv}/hacker-podcast-${today}.mp3`;
    const conversations = podcastContent.split('\n').filter(line => line.trim().length > 0);

    for (const [index, conversation] of conversations.entries()) {
      await step.do(`tts ${index}`, { ...retryConfig, timeout: '5 minutes' }, async () => {
        const match = conversation.match(/^([^：:]+)[：:](.+)$/);
        if (!match) return null;
        const speakerName = match[1].trim();
        const content = match[2].trim();
        let gender = '女';
        if (speakerName.includes('Dr') || speakerName.includes('刘') || speakerName.includes('男')) gender = '男';
        const audio = await synthesize(content, gender, this.env);
        if (!audio.size) throw new Error('TTS size 0');
        const audioKey = `tmp/${podcastKey}-${index}.mp3`;
        const audioUrl = `${this.env.HACKER_PODCAST_R2_BUCKET_URL}/${audioKey}?t=${Date.now()}`;
        await this.env.HACKER_PODCAST_R2.put(audioKey, audio);
        await this.env.HACKER_PODCAST_KV.put(`tmp:${event.instanceId}:audio:${index}`, audioUrl);
        return audioUrl;
      });
    }

    const audioFiles = await step.do('collect audio', retryConfig, async () => {
      const urls: string[] = [];
      for (const [index] of conversations.entries()) {
        const url = await this.env.HACKER_PODCAST_KV.get(`tmp:${event.instanceId}:audio:${index}`);
        if (url) urls.push(url);
      }
      return urls;
    });

    await step.do('concat save', retryConfig, async () => {
      if (!this.env.BROWSER) return;
      const blob = await concatAudioFiles(audioFiles, this.env.BROWSER, { workerUrl: this.env.HACKER_PODCAST_WORKER_URL });
      await this.env.HACKER_PODCAST_R2.put(podcastKey, blob);
    });

    await step.do('save meta', retryConfig, async () => {
      await this.env.HACKER_PODCAST_KV.put(contentKey, JSON.stringify({
        date: today, title: `${podcastTitle} ${today}`, stories: finalStories, podcastContent, blogContent, introContent, audio: podcastKey, updatedAt: Date.now(),
      }));
    });

    return 'success';
  }
}