import { createSystem, defaultConfig } from "@chakra-ui/react"
import { buttonRecipe } from "./theme/button.recipe"
import { headingRecipe } from "./theme/heading.recipe"
import { linkRecipe } from "./theme/textlink.recipe"
import "@fontsource/noto-sans/500.css"

export const system = createSystem(defaultConfig, {
  globalCss: {
    html: {
      fontSize: "16px",
      fontWeight: "500",
      fontFamily:
        '"Noto Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol"',
    },
    body: {
      fontSize: "0.875rem",
      margin: 0,
      padding: 0,
    },
    ".chakra-theme": {
      color: "text.main",
    },
  },
  theme: {
    semanticTokens: {
      colors: {
        text: {
          heading: { value: { base: "gray.900", _dark: "white" } },
          main: { value: { base: "gray.800", _dark: "gray.200" } },
        },
        ui: {
          main: { value: { base: "teal.600", _dark: "teal.300" } },
        },
      },
    },
    recipes: {
      button: buttonRecipe,
      heading: headingRecipe,
      textlink: linkRecipe,
    },
  },
})
