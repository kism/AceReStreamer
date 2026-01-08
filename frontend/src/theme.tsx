import { createSystem, defaultConfig } from "@chakra-ui/react"
import { buttonRecipe } from "./theme/button.recipe"
import { headingRecipe } from "./theme/heading.recipe"
import { linkRecipe } from "./theme/textlink.recipe"
import "@fontsource/noto-sans/500.css"

// https://chakra-ui.com/docs/theming/colors
const lightHeadingColour = "colors.gray.900"
const darkHeadingColour = "colors.white"
const lightTextColour = "colors.gray.800"
const darkTextColour = "colors.gray.300"
const lightUIMainColour = "teal"
const darkUIMainColour = "teal"

// Temp colour for findthing things not themed
// const lightHeadingColour = "blue"
// const darkHeadingColour = "red"
// const lightTextColour = "blue"
// const darkTextColour = "red"
// const lightUIMainColour = "blue"
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
    tokens: {
      colors: {
        text: {
          heading: { value: lightHeadingColour },
          main: { value: lightTextColour },
        },
      },
    },
    semanticTokens: {
      colors: {
        text: {
          heading: {
            value: {
              base: lightHeadingColour,
              _dark: darkHeadingColour,
            },
          },
          main: {
            value: {
              base: lightTextColour,
              _dark: darkTextColour,
            },
          },
        },
        ui: {
          main: {
            value: {
              base: lightUIMainColour,
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
