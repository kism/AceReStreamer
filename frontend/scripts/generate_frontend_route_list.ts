import * as fs from "node:fs"
import { routeTree } from "../src/routeTree.gen"

function collectAppPaths(route: any, parentPath: string = ""): string[] {
  const paths: string[] = []

  // Get path from the route's options if available
  const currentPath = route.options?.path || route.path || ""
  const fullPath =
    currentPath === "/"
      ? "/"
      : (parentPath + currentPath).replace(/\/+/g, "/") || "/"

  // Add this route's path if it's a valid route
  if (route.options?.id || route.id) {
    paths.push(fullPath)
  }

  // Recursively collect from children
  if (route.children) {
    for (const child of Object.values(route.children)) {
      paths.push(...collectAppPaths(child, fullPath))
    }
  }

  return paths
}

function collectPublicPaths(): string[] {
  const publicDirectory = "./public"

  const paths: string[] = []

  function walkDir(currentPath: string, urlPath: string) {
    const entries = fs.readdirSync(currentPath, { withFileTypes: true })

    for (const entry of entries) {
      const entryPath = `${currentPath}/${entry.name}`
      const entryUrlPath = `${urlPath}/${entry.name}`.replace(/\/+/g, "/")

      if (entry.isDirectory()) {
        walkDir(entryPath, entryUrlPath)
      } else {
        paths.push(entryUrlPath)
      }
    }
  }

  walkDir(publicDirectory, "")

  return paths
}

const appPaths = collectAppPaths(routeTree)
const publicPaths = collectPublicPaths()

const uniquePaths = [...new Set([...appPaths, ...publicPaths])]
  .filter((p) => p && p !== "")
  .sort()

// Check if output path argument is provided
const outputPath = process.argv[2]

if (outputPath) {
  // Write to JSON file
  fs.writeFileSync(outputPath, JSON.stringify(uniquePaths, null, 2), "utf-8")
  console.log(`Routes written to ${outputPath}`)
} else {
  // Print to console
  for (const path of uniquePaths) {
    console.log(path)
  }
}
