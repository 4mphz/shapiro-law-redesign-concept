# Preview feedback Worker

This Worker powers the visual review overlay. It creates one GitHub issue per submitted comment and exposes those feedback issues back to the preview so reviewers can browse their shared comment history. It does not trigger Codex or make website changes.

## Configure

1. Create the Worker in the Cloudflare account that serves preview deployments.
2. Set `GITHUB_OWNER=4mphz`, `GITHUB_REPO=shapiro-law-redesign-concept`, and `ALLOWED_ORIGINS` to the exact preview origins, comma-separated.
3. Add the GitHub secret:

   ```sh
   wrangler secret put GITHUB_TOKEN
   ```

   `GITHUB_TOKEN` needs permission to create issues in this repository.
4. Deploy the Worker, then update the `window.SHAPIRO_REVIEW_CONFIG` block at the top of `js/main.js` with the deployed endpoint.

The Worker accepts requests only from the configured Pages production domain and its pull-request preview domains. If this preview becomes public, protect it with Cloudflare Access before collecting feedback.

## Reviewer flow

Open the preview, select **Add comment**, click an element, write a note, then choose **Submit comments**. The Worker creates a GitHub issue for every saved note. Select **Comments** to view local drafts and all submitted feedback.
