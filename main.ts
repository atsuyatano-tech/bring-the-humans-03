// bring-the-humans-03 — make.fun entry helper.
//
// Job: read VIDEO.json from the bot directory (env MAKEFUN_BOT_DIR,
// default: this program's own directory) and copy it byte-for-byte to
// VIDEO.json in the output directory (env MAKEFUN_OUTPUT_DIR, default:
// "out"), creating the output directory if needed. Then print one
// deterministic line naming the TikTok video URL that was copied.
//
// VIDEO.json names this entry's public TikTok video:
//   {"url": "https://www.tiktok.com/@<handle>/video/<id>"}
//
// Pure Node.js standard library only. No network access, no timestamps
// and no randomness, so repeated runs produce identical output.

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// A full TikTok video address: a handle of letters, digits, dots or
// underscores after the @, then /video/ and the numeric video id.
// Short links (vm.tiktok.com, vt.tiktok.com, tiktok.com/t/...) and
// photo posts (/photo/<id>) are not accepted by the bounty, and this
// pattern refuses them too.
const TIKTOK_VIDEO_URL_PATTERN =
  /^https:\/\/www\.tiktok\.com\/@[A-Za-z0-9_.]+\/video\/\d+$/;

function fail(message: string): never {
  console.error("error: " + message);
  process.exit(1);
}

function resolveBotDir(): string {
  return process.env.MAKEFUN_BOT_DIR || dirname(fileURLToPath(import.meta.url));
}

function resolveOutDir(): string {
  return process.env.MAKEFUN_OUTPUT_DIR || "out";
}

// Reads the source file as raw bytes (so the copy stays byte-for-byte)
// and returns both the bytes and the validated video URL inside them.
function readEntry(botDir: string): { data: Buffer; url: string } {
  const sourcePath = join(botDir, "VIDEO.json");
  let data: Buffer;
  try {
    data = readFileSync(sourcePath);
  } catch {
    fail(
      "cannot read " +
        sourcePath +
        " (set MAKEFUN_BOT_DIR to the directory containing VIDEO.json)",
    );
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(data.toString("utf8"));
  } catch {
    fail(sourcePath + " is not valid JSON");
  }

  const url =
    parsed !== null && typeof parsed === "object"
      ? (parsed as { url?: unknown }).url
      : undefined;
  if (typeof url !== "string" || !TIKTOK_VIDEO_URL_PATTERN.test(url)) {
    fail(
      sourcePath +
        ' must hold {"url": "https://www.tiktok.com/@<handle>/video/<id>"}',
    );
  }
  return { data, url };
}

function main(): void {
  const botDir = resolveBotDir();
  const outDir = resolveOutDir();
  const { data, url } = readEntry(botDir);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, "VIDEO.json"), data);
  console.log("tiktok video: " + url);
}

main();
