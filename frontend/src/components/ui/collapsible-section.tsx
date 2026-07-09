import { Box, Collapsible, Flex, Heading } from "@chakra-ui/react"
import { useState } from "react"
import { FaAngleDown, FaAngleUp } from "react-icons/fa"

interface CollapsibleSectionProps {
  title: React.ReactNode
  headerExtra?: (open: boolean) => React.ReactNode
  children: React.ReactNode
}

export function CollapsibleSection({
  title,
  headerExtra,
  children,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(false)

  return (
    <Flex direction="column" p={2} borderWidth="1px" w="full">
      <Collapsible.Root open={open}>
        <Collapsible.Trigger cursor="pointer" onClick={() => setOpen(!open)}>
          <Flex align="center" gap={2}>
            <Box p="1">{open ? <FaAngleUp /> : <FaAngleDown />}</Box>
            <Heading size="sm">{title}</Heading>
            {headerExtra?.(open)}
          </Flex>
        </Collapsible.Trigger>
        <Collapsible.Content>{children}</Collapsible.Content>
      </Collapsible.Root>
    </Flex>
  )
}
