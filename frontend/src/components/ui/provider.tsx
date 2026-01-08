"use client"

import { Box, ChakraProvider } from "@chakra-ui/react"
import { type PropsWithChildren } from "react"
import { system } from "../../theme"
import { ColorModeProvider } from "./color-mode"
import { Toaster } from "./toaster"

export function CustomProvider(props: PropsWithChildren) {
  return (
    <ChakraProvider value={system}>
      <ColorModeProvider
        defaultTheme="system"
        enableSystem
      >
        <Box color="text.main">{props.children}</Box>
      </ColorModeProvider>
      <Toaster />
    </ChakraProvider>
  )
}
