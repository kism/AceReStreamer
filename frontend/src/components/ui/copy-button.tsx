import { Box } from "@chakra-ui/react"
import { useEffect, useState } from "react"
import { CopyToClipboard } from "react-copy-to-clipboard-ts"
import { FiCopy } from "react-icons/fi"
import { Button } from "./button"

interface CopyButtonProps {
  text: string
  children?: React.ReactNode
}

export function CopyButton({ text, children = <FiCopy /> }: CopyButtonProps) {
  const [showCopied, setShowCopied] = useState(false)
  const [isVisible, setIsVisible] = useState(false)

  const handleCopy = () => {
    setShowCopied(true)
    setIsVisible(true)
  }

  useEffect(() => {
    if (showCopied) {
      const timer = setTimeout(() => {
        setIsVisible(false)
        // Wait for fade out transition to complete before hiding
        setTimeout(() => setShowCopied(false), 300)
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [showCopied])

  return (
    <Box position="relative">
      <CopyToClipboard text={text} onCopy={handleCopy}>
        <Button
          size="2xs"
          p="0"
          display="flex"
          alignItems="center"
          justifyContent="center"
        >
          {children}
        </Button>
      </CopyToClipboard>
      {showCopied && (
        <Box
          position="absolute"
          top="50%"
          left="calc(100% + 8px)"
          transform="translateY(-50%)"
          bg="teal.600"
          color="white"
          fontSize="xs"
          px="1.5"
          py="2px"
          borderRadius="sm"
          whiteSpace="nowrap"
          zIndex="tooltip"
          opacity={isVisible ? 1 : 0}
          transition="opacity 0.3s ease-out"
          pointerEvents="none"
        >
          Copied!
        </Box>
      )}
    </Box>
  )
}
