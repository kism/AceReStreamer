import { execSync } from "node:child_process"
import path from "node:path"
import { tanstackRouter } from "@tanstack/router-plugin/vite"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"

const getGitBranch = () => {
  try {
    return execSync("git rev-parse --abbrev-ref HEAD", {
      encoding: "utf-8",
    }).trim()
  } catch {
    return "unknown"
  }
}

const getGitCommit = () => {
  try {
    return execSync("git rev-parse --short HEAD", { encoding: "utf-8" }).trim()
  } catch {
    return "unknown"
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  define: {
    __GIT_BRANCH__: JSON.stringify(getGitBranch()),
    __GIT_COMMIT__: JSON.stringify(getGitCommit()),
  },
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // This will be lazy loaded
          if (id.includes("hls.js")) {
            return "hlsjs"
          }

          // TanStack
          if (id.includes("@tanstack/react-query")) {
            return "tanstack-query"
          }
          if (id.includes("@tanstack/react-router")) {
            return "tanstack-router"
          }

          // Icons can be separated
          if (id.includes("react-icons")) {
            return "react-icons"
          }

          // Chakra needs to be with React
          if (
            id.includes("react-hook-form") ||
            id.includes("react-copy-to-clipboard") ||
            id.includes("react-error-boundary") ||
            id.includes("@chakra-ui") ||
            id.includes("@emotion") ||
            id.includes("@ark-ui") ||
            id.includes("node_modules/react/") ||
            id.includes("node_modules/react-dom/") ||
            id.includes("node_modules/scheduler/")
          ) {
            return "react-chakra"
          }
        },
      },
    },
    chunkSizeWarningLimit: 500,
  },
})
