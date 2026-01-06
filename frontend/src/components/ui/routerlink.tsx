"use client"
import type { RecipeProps } from "@chakra-ui/react"
import { createRecipeContext } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"


export interface RouterLinkProps
    extends React.ComponentProps<typeof Link>, RecipeProps<"textlink"> {}

const { withContext } = createRecipeContext({ key: "textlink" })

export const RouterLink = withContext<
  React.ComponentRef<typeof Link>,
  RouterLinkProps
>(Link)
