import { createSystem, defaultConfig } from "@chakra-ui/react"
import { buttonRecipe } from "./theme/button.recipe"
import { headingRecipe } from "./theme/heading.recipe"
import { linkRecipe } from "./theme/textlink.recipe"
import "@fontsource/noto-sans/500.css"

export const system = createSystem(defaultConfig, {
  globalCss: {
    html: {
      color: "text.main",
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
  },
  theme: {
    tokens: {
      colors: {
        text: {
          heading: { value: "#ffffff" },
          main: { value: "#cccccc" },
        },
        ui: {
          main: { value: "#008080" },
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
