import { CodeProps } from "@chakra-ui/react"

import { Code as ChakraCode } from "@chakra-ui/react"
import * as React from "react"

import "@fontsource/fira-code/500.css"

export const Code: React.FC<CodeProps> = ({ children, ...rest }) => {
    return <ChakraCode rounded={"0"} px="2" py="1" fontSize="sm" fontFamily="'Fira Code', monospace" fontWeight="500" {...rest}>{children}</ChakraCode>
}

export const CodeBlock: React.FC<CodeProps> = ({ children, ...rest }) => {
    return (
        <Code display="block" whiteSpace="pre" w="100%" {...rest}>
            {children}
        </Code>
    )
}

