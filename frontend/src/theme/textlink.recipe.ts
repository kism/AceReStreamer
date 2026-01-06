import { defineRecipe } from "@chakra-ui/react"

export const linkRecipe = defineRecipe({
  base: {
    color: "ui.main",
    fontWeight: "regular",
    textDecoration: "underline",
    _hover: {
      textDecoration: "none",
    },
  },
})
