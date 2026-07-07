import { Box } from "@chakra-ui/react"
import { useEffect, useState } from "react"
import { FiCopy } from "react-icons/fi"
import { Button } from "./button"

interface CopyButtonProps {
  text: string
  children?: React.ReactNode
}

export function CopyButton({ text, children = <FiCopy /> }: CopyButtonProps) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (copied) {
      const timer = setTimeout(() => setCopied(false), 2000)
      return () => clearTimeout(timer)
    }
  }, [copied])

  return (
    <Box position="relative">
      <Button
        size="2xs"
        p="0"
        display="flex"
        alignItems="center"
        justifyContent="center"
        onClick={() =>
          navigator.clipboard.writeText(text).then(() => setCopied(true))
        }
      >
        {children}
      </Button>
      <Box
        position="absolute"
        top="50%"
        right="calc(100% + 8px)"
        transform="translateY(-50%)"
        bg="teal.600"
        color="white"
        fontSize="xs"
        px="1.5"
        py="2px"
        borderRadius="sm"
        whiteSpace="nowrap"
        zIndex="tooltip"
        opacity={copied ? 1 : 0}
        transition="opacity 0.3s ease-out"
        pointerEvents="none"
      >
        Copied!
      </Box>
    </Box>
  )
}
