import { Box, Button, Table, Text } from "@chakra-ui/react"
import { useEffect, useState } from "react"

import { UsersService } from "@/client"
import {
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

async function getAuthToken() {
  const streamTokenService = UsersService.readStreamTokenMe()
  return (await streamTokenService)?.stream_token || ""
}

async function regenerateStreamToken() {
  const streamTokenService = UsersService.regenerateStreamTokenMe()
  return (await streamTokenService)?.stream_token || ""
}

const StreamToken = () => {
  const [token, setToken] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const fetchToken = async () => {
      try {
        const fetchedToken = await getAuthToken()
        setToken(fetchedToken)
      } catch (error) {
        console.error("Failed to fetch token:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchToken()
  }, [])

  if (loading) {
    return (
      <Box>
        <Text>Loading...</Text>
      </Box>
    )
  }

  return (
    <Box>
      <Table.Root size="sm" variant="outline">
        <Table.Body>
          <Table.Row>
            <Table.Cell bg="bg.subtle" whiteSpace="nowrap" width="1%">
              Stream Token
            </Table.Cell>
            <Table.Cell>
              <Text fontFamily="monospace" wordBreak="break-all">
                {token || "No token available"}
              </Text>
            </Table.Cell>
            <Table.Cell width="1%">
              <DialogRoot open={open} onOpenChange={(e) => setOpen(e.open)}>
                <DialogTrigger asChild>
                  <Button size="sm">Regenerate</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Confirm Regeneration</DialogTitle>
                  </DialogHeader>
                  <DialogCloseTrigger />
                  <DialogBody>
                    <Text>
                      Are you sure you want to regenerate your stream token?
                      This will invalidate your current token.
                    </Text>
                  </DialogBody>
                  <DialogFooter>
                    <DialogActionTrigger asChild>
                      <Button variant="outline">Cancel</Button>
                    </DialogActionTrigger>
                    <Button
                      colorPalette="red"
                      onClick={async () => {
                        setOpen(false)
                        setLoading(true)
                        try {
                          const newToken = await regenerateStreamToken()
                          setToken(newToken)
                        } catch (error) {
                          console.error("Failed to regenerate token:", error)
                        } finally {
                          setLoading(false)
                        }
                      }}
                    >
                      Regenerate
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </DialogRoot>
            </Table.Cell>
          </Table.Row>
        </Table.Body>
      </Table.Root>
    </Box>
  )
}

export default StreamToken
