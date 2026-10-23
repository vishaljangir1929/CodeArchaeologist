import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
const out = "../src/codearchaeologist/web";
await mkdir(out + "/assets", { recursive: true });
await build({
  entryPoints: ["src/main.jsx"],
  bundle: true,
  minify: true,
  outdir: out + "/assets",
  entryNames: "app",
  assetNames: "[name]-[hash]",
  loader: { ".jsx": "jsx" },
  jsx: "automatic",
  define: { "process.env.NODE_ENV": '"production"' },
  sourcemap: false,
});
await writeFile(
  out + "/index.html",
  '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#183039"><meta name="description" content="Explore Python codebases with static analysis and grounded local AI."><title>CodeArchaeologist | Code intelligence</title><link rel="stylesheet" href="/assets/app.css"></head><body><div id="root"></div><script type="module" src="/assets/app.js"></script></body></html>',
);
console.log("Built React interface into " + out);
