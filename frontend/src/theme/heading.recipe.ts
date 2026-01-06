import { defineRecipe } from "@chakra-ui/react"

export const headingRecipe = defineRecipe({
  base: {
    fontWeight: "bold",
    color: "text.heading",
  },
  defaultVariants: {
    size: "md",
  },
  variants: {
    size: {
      "2xl": {
        fontSize: "2.5rem",
        lineHeight: "3rem",
      },
      xl: {
        fontSize: "2rem",
        lineHeight: "2.5rem",
      },
      lg: {
        fontSize: "1.5rem",
        lineHeight: "2rem",
      },
      md: {
        fontSize: "1.25rem",
        lineHeight: "1.75rem",
      },
      sm: {
        fontSize: "1rem",
        lineHeight: "1.5rem",
      },
    },
  },
})
