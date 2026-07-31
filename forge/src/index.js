import crypto from "crypto";

// Forwards Bitbucket pull request comment events to the BlameGPT backend,
// signed with a shared secret (same scheme as GitHub webhooks).
export const run = async (event) => {
  const secret = process.env.BLAMEGPT_WEBHOOK_SECRET;
  const backend = process.env.BLAMEGPT_BACKEND_URL;
  if (!secret || !backend) {
    console.error("BLAMEGPT_WEBHOOK_SECRET and BLAMEGPT_BACKEND_URL must be set (forge variables set)");
    return;
  }

  const body = JSON.stringify(event);
  const signature = "sha256=" + crypto.createHmac("sha256", secret).update(body).digest("hex");

  const response = await fetch(`${backend}/api/webhook/bitbucket`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Hub-Signature-256": signature,
    },
    body,
  });

  console.log(`forwarded pullrequest-comment event: ${response.status}`);
};
