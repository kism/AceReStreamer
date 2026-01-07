import { Badge, Container, Flex, Heading } from "@chakra-ui/react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type UserPublic, UsersService } from "@/client"
import AddUser from "@/components/Admin/User/AddUser"
import { UserActionsMenu } from "@/components/Common/UserActionsMenu"
import PendingUsers from "@/components/Pending/PendingUsers"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination.tsx"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const PER_PAGE = 5

function getUsersQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      UsersService.readUsers({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["users", { page }],
  }
}

function UsersTable() {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  const [page, setPage] = useState(1)

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getUsersQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  const users = data?.data.slice(0, PER_PAGE) ?? []
  const count = data?.count ?? 0

  if (isLoading) {
    return <PendingUsers />
  }

  return (
    <>
      <AppTableRoot preset="outlineSm">
        <TableHeader>
          <TableRow>
            <TableCell>Full name</TableCell>
            <TableCell>Username</TableCell>
            <TableCell>Role</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHeader>
        <TableBody>
          {users?.map((user) => (
            <TableRow key={user.id} opacity={isPlaceholderData ? 0.5 : 1}>
              <TableCell color={!user.full_name ? "gray" : "inherit"}>
                {user.full_name || "N/A"}
                {currentUser?.id === user.id && (
                  <Badge ml="1" colorScheme="teal">
                    You
                  </Badge>
                )}
              </TableCell>
              <TableCell truncate maxW="sm">
                {user.username}
              </TableCell>
              <TableCell>{user.is_superuser ? "Superuser" : "User"}</TableCell>
              <TableCell>{user.is_active ? "Active" : "Inactive"}</TableCell>
              <TableCell>
                <UserActionsMenu
                  user={user}
                  disabled={currentUser?.id === user.id}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </AppTableRoot>
      <Flex justifyContent="flex-end" mt={4}>
        <PaginationRoot
          count={count}
          pageSize={PER_PAGE}
          page={page}
          onPageChange={({ page }) => setPage(page)}
        >
          <Flex>
            <PaginationPrevTrigger />
            <PaginationItems />
            <PaginationNextTrigger />
          </Flex>
        </PaginationRoot>
      </Flex>
    </>
  )
}

function UserManagement() {
  return (
    <Container maxW="full">
      <Heading size="sm" py={4}>
        Users Management
      </Heading>
      <AddUser />
      <UsersTable />
    </Container>
  )
}

export default UserManagement
