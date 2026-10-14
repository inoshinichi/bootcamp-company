#!/usr/bin/env node
// MCP サーバーを npx で起動する前に、環境変数の先頭 "~" をホームフォルダに展開する。
// MCP の env は ~ や $HOME を展開せず、ホームのパスも OS ごとに違う
// （Mac: /Users/<名前>、Windows: C:\Users\<名前>）ため、os.homedir() で解決する。
//
// 使い方: node with-home.mjs <npmパッケージ> [引数...]

import { spawn } from "node:child_process";
import os from "node:os";
import path from "node:path";

const [pkg, ...rest] = process.argv.slice(2);
if (!pkg) {
  console.error("usage: node with-home.mjs <npm-package> [args...]");
  process.exit(1);
}

const env = { ...process.env };
for (const [key, value] of Object.entries(env)) {
  if (value === "~" || value?.startsWith("~/")) {
    env[key] = path.join(os.homedir(), value.slice(2));
  }
}

// Windows の npx は npx.cmd のため shell 経由で起動する（引数は .mcp.json の固定値のみ）
const args = ["-y", pkg, ...rest];
const child =
  process.platform === "win32"
    ? spawn(["npx", ...args].join(" "), { env, stdio: "inherit", shell: true })
    : spawn("npx", args, { env, stdio: "inherit" });

for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, () => child.kill(sig));
}
child.on("exit", (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  else process.exit(code ?? 0);
});
