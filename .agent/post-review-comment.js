// Publikuje wynik review agenta jako komentarz w PR.
// Użycie: node .agent/post-review-comment.js review.json
const fs = require("fs");

const [, , reviewPath] = process.argv;
const { GITHUB_TOKEN, GITHUB_REPOSITORY, GITHUB_EVENT_PATH } = process.env;

const event = JSON.parse(fs.readFileSync(GITHUB_EVENT_PATH, "utf8"));
const prNumber = event.pull_request.number;
const { findings } = JSON.parse(fs.readFileSync(reviewPath, "utf8"));

const body = findings.length
  ? "### Agent review\n\n" +
    findings.map((f) => `- \`${f.file}:${f.line}\` – ${f.description}`).join("\n")
  : "### Agent review\n\nNie znaleziono błędów mogących spowodować regresję.";

(async () => {
  const res = await fetch(
    `https://api.github.com/repos/${GITHUB_REPOSITORY}/issues/${prNumber}/comments`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ body }),
    }
  );
  if (!res.ok) {
    console.error(`GitHub API ${res.status}: ${await res.text()}`);
    process.exit(1);
  }
  console.log(`Dodano komentarz do PR #${prNumber} (${findings.length} uwag).`);
})();
