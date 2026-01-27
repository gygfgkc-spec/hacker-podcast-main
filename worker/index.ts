export * from '../workflow'

interface Env extends CloudflareEnv {
  HACKER_PODCAST_WORKFLOW: Workflow
  BROWSER: Fetcher
}

export default {
  async runWorkflow(event: ScheduledEvent | Request, env: Env, ctx: ExecutionContext) {
    console.info('trigger event by:', event)

    let params: any = {};
    // 如果是通过 HTTP POST 触发，尝试读取 body 中的参数 (比如 custom_script)
    if (event instanceof Request && event.method === 'POST') {
      try {
        // clone() 防止多次读取报错 (虽然后面没再读了)
        const body = await event.clone().json();
        if (body && typeof body === 'object') {
           params = body;
           console.info('Triggered with params:', params);
        }
      } catch (e) {
        console.warn('Failed to parse request body as JSON', e);
      }
    }

    const createWorkflow = async () => {
      // 将参数透传给 Workflow
      const instance = await env.HACKER_PODCAST_WORKFLOW.create({ params })

      const instanceDetails = {
        id: instance.id,
        details: await instance.status(),
      }

      console.info('instance detail:', instanceDetails)
      return instanceDetails
    }

    ctx.waitUntil(createWorkflow())

    return new Response('create workflow success')
  },
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const { pathname, hostname } = new URL(request.url)
    
    // --- 修改开始：允许浏览器直接访问 /api/cron 触发 ---
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
    const isTriggerPath = pathname.includes('/api/cron'); // 只要网址里有这个词就行
    
    if (isLocal && (request.method === 'POST' || isTriggerPath)) {
      return this.runWorkflow(request, env, ctx)
    }
    // --- 修改结束 ---
    if (pathname.includes('/static')) {
      const filename = pathname.replace('/static/', '')
      const file = await env.HACKER_PODCAST_R2.get(filename)
      console.info('fetch static file:', filename, {
        uploaded: file?.uploaded,
        size: file?.size,
      })
      return new Response(file?.body)
    }
    return Response.redirect(`https://hacker-podcast.agi.li/${pathname}`, 302)
  },
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    return this.runWorkflow(event, env, ctx)
  },
}
