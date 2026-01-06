"use client"

import type { HTMLChakraProps, RecipeProps } from "@chakra-ui/react"
import { createRecipeContext } from "@chakra-ui/react"

export interface LinkProps
  extends HTMLChakraProps<"a", RecipeProps<"textlink">> {}

const { withContext } = createRecipeContext({ key: "textlink" })

export const Link = withContext<HTMLAnchorElement, LinkProps>("a")
