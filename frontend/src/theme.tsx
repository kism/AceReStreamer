import { createSystem, defaultConfig } from "@chakra-ui/react"
import { buttonRecipe } from "./theme/button.recipe"
import { headingRecipe } from "./theme/heading.recipe"
import { linkRecipe } from "./theme/textlink.recipe"
import "@fontsource/noto-sans/500.css"

// https://chakra-ui.com/docs/theming/colors
const darkHeadingColour = "colors.white"
const darkTextColour = "colors.gray.300"
const darkUIMainColour = "teal"

// Temp colour for findthing things not themed
// const darkHeadingColour = "red"
// const darkTextColour = "red"
// const darkUIMainColour = "red"

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
  },
  theme: {
    semanticTokens: {
      colors: {
        text: {
          heading: {
            value: {
              _dark: darkHeadingColour,
            },
          },
          main: {
            value: {
              _dark: darkTextColour,
            },
          },
        },
        ui: {
          main: {
            value: {
              _dark: darkUIMainColour,
            },
          },
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
