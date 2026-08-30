const json = (body, status = 200, origin = '') => new Response(status === 204 ? null : JSON.stringify(body), {
  status,
  headers: {
    'content-type': 'application/json; charset=utf-8',
    'access-control-allow-origin': origin,
    'access-control-allow-headers': 'content-type',
    'access-control-allow-methods': 'POST, OPTIONS',
    vary: 'Origin'
  }
});

function allowedOrigin(request, env) {
  const origin = request.headers.get('Origin') || '';
  const allowed = (env.ALLOWED_ORIGINS || '').split(',').map((value) => value.trim()).filter(Boolean);
  if (allowed.includes(origin)) return origin;
  const suffixes = (env.ALLOWED_ORIGIN_SUFFIXES || '').split(',').map((value) => value.trim()).filter(Boolean);
  try {
    const url = new URL(origin);
    return url.protocol === 'https:' && suffixes.some((suffix) => url.hostname.endsWith(suffix)) ? origin : '';
  } catch (_) {
    return '';
  }
}

function issueBody(note, reviewer) {
  const location = note.position ? `\n- Position: ${note.position.x}, ${note.position.y}` : '';
  const image = note.imageSrc ? `\n- Image source: ${note.imageSrc}` : '';
  return `@codex implement this

## Website feedback

${note.comment}

## Context

- Reviewer: ${reviewer}
- Page: ${note.pageUrl}
- Page title: ${note.pageTitle || 'Untitled'}
- Element: \`${note.selector || note.element || 'unknown'}\`
- Selected content: ${note.selectedText || 'No text captured'}${image}${location}
- Viewport: ${note.viewport ? `${note.viewport.width} × ${note.viewport.height}` : 'Unknown'}
- Submitted: ${note.createdAt || new Date().toISOString()}

Please make the requested change, verify it locally, and open a pull request. Do not merge to main.`;
}

export default {
  async fetch(request, env) {
    const origin = allowedOrigin(request, env);
    if (request.method === 'OPTIONS') return json({}, 204, origin);
    if (!origin) return json({ error: 'Origin is not permitted.' }, 403);
    if (request.method !== 'POST') return json({ error: 'Method not allowed.' }, 405, origin);
    if (!env.GITHUB_TOKEN || !env.GITHUB_OWNER || !env.GITHUB_REPO) {
      return json({ error: 'Review Worker is not configured.' }, 503, origin);
    }

    let payload;
    try { payload = await request.json(); } catch (_) { return json({ error: 'Invalid JSON.' }, 400, origin); }
    const notes = Array.isArray(payload.notes) ? payload.notes.slice(0, 25) : [];
    if (!notes.length) return json({ error: 'No feedback notes supplied.' }, 400, origin);

    const reviewer = String(payload.reviewer || 'Preview reviewer').slice(0, 120);
    const results = [];
    for (const note of notes) {
      const comment = String(note.comment || '').trim().slice(0, 1600);
      if (!comment) continue;
      const titleTarget = String(note.selectedText || note.element || 'website element').replace(/\s+/g, ' ').slice(0, 80);
      const response = await fetch(`https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/issues`, {
        method: 'POST',
        headers: {
          accept: 'application/vnd.github+json',
          authorization: `Bearer ${env.GITHUB_TOKEN}`,
          'content-type': 'application/json',
          'user-agent': 'shapiro-preview-feedback-worker'
        },
        body: JSON.stringify({ title: `[Preview feedback] ${titleTarget}`, body: issueBody({ ...note, comment }, reviewer) })
      });
      if (!response.ok) {
        const detail = await response.text();
        console.error('GitHub issue creation failed:', detail);
        return json({ error: 'GitHub issue creation failed.', detail }, 502, origin);
      }
      const issue = await response.json();
      results.push({ number: issue.number, url: issue.html_url });
    }
    return json({ issues: results }, 201, origin);
  }
};
