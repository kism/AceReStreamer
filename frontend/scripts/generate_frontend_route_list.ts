import * as fs from "node:fs"
import { routeTree } from "../src/routeTree.gen"

function collectPaths(route: any, parentPath: string = ""): string[] {
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
      paths.push(...collectPaths(child, fullPath))
    }
  }

  return paths
}

const allPaths = collectPaths(routeTree)
const uniquePaths = [...new Set(allPaths)].filter((p) => p && p !== "").sort()

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
