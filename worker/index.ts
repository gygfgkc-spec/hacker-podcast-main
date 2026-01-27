export * from '../workflow'

interface Env extends CloudflareEnv {
  HACKER_PODCAST_WORKFLOW: Workflow
  BROWSER: Fetcher
}

export default {
  runWorkflow(event: ScheduledEvent | Request, env: Env, ctx: ExecutionContext) {
    console.info('trigger event by:', event)

    const createWorkflow = async () => {
      const instance = await env.HACKER_PODCAST_WORKFLOW.create()

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
