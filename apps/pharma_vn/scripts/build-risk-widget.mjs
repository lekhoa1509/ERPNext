import { build } from "esbuild";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(__dirname, "..");
const entryFile = path.join(appRoot, "frontend", "risk_dashboard", "src", "index.tsx");
const outputFile = path.join(appRoot, "pharma_vn", "public", "js", "customer_risk_widget.bundle.js");

await build({
  entryPoints: [entryFile],
  outfile: outputFile,
  bundle: true,
  format: "iife",
  platform: "browser",
  jsx: "automatic",
  minify: true,
  sourcemap: false,
  target: ["es2019"],
  define: {
    "process.env.NODE_ENV": '"production"',
  },
  logLevel: "info",
});

console.log(`Built customer risk widget: ${outputFile}`);
