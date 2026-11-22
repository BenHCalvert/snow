import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base is "./" so the build works at any path (GitHub Pages serves it at /snow/).
export default defineConfig({ plugins: [react()], base: "./" });
