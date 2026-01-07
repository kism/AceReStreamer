import type { ButtonProps } from "@chakra-ui/react"
import { IconButton } from "@chakra-ui/react"
import * as React from "react"
import { FaAngleLeft,  } from "react-icons/fa"

export type CloseButtonProps = ButtonProps

export const CloseButton = React.forwardRef<
  HTMLButtonElement,
  CloseButtonProps
>(function CloseButton(props, ref) {
  return (
    <IconButton variant="ghost" aria-label="Close" ref={ref} {...props}>
      {props.children ?? <FaAngleLeft />}
    </IconButton>
  )
})
