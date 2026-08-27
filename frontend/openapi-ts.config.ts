import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "./openapi.json",
  output: "./src/client",

  plugins: [
    {
      name: "@hey-api/client-fetch",
      // Legacy-client behaviour: throw on error, resolve with data directly
      throwOnError: true,
    },
    {
      name: "@hey-api/sdk",
      // NOTE: this doesn't allow tree-shaking
      asClass: true,
      classNameBuilder: "{{name}}Service",
      responseStyle: "data",
    },
  ],
})
