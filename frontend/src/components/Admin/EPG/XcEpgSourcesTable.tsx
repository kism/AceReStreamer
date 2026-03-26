import { Box, Heading } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { IptvScraperService } from "@/client"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

function XcEpgSourcesTable() {
  const { data, isLoading } = useQuery({
    queryFn: () => IptvScraperService.sources(),
    queryKey: ["iptvScrapers"],
    placeholderData: (prevData) => prevData,
  })

  const xcSources =
    data?.filter((source) => source.type === "xtream" && source.use_epg) ?? []

  if (isLoading) {
    return <Box>Loading...</Box>
  }

  return (
    <>
      <Heading size="md" mt={2} mb={1}>
        XC Sources with EPG Enabled
      </Heading>
      <AppTableRoot preset="outlineSm" w="fit-content">
        <TableHeader>
          <TableRow>
            <TableColumnHeader>Name</TableColumnHeader>
          </TableRow>
        </TableHeader>
        <TableBody>
          {xcSources.length === 0 ? (
            <TableRow>
              <TableCell>No XC sources with EPG enabled.</TableCell>
            </TableRow>
          ) : (
            xcSources.map((source) => (
              <TableRow key={source.name}>
                <TableCell>{source.name}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </AppTableRoot>
    </>
  )
}

export default XcEpgSourcesTable
