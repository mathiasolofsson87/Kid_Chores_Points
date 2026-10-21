// Bundles frontend/src into the single file the integration serves.
import { build } from "esbuild";

export const OUTFILE = "custom_components/kid_chores_points/www/kid-chores-cards.js";

await build({
  entryPoints: ["frontend/src/index.js"],
  outfile: OUTFILE,
  bundle: true,
  format: "iife",
  target: "es2022",
  banner: {
    js: "/* GENERATED FILE - do not edit. Source: frontend/src, build: npm run build. */",
  },
  legalComments: "none",
});
