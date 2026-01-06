// Note: the `PrivateService` is only available when generating the client
// for local environments
import { OpenAPI, PrivateService } from "../../src/client"

OpenAPI.BASE = `${process.env.VITE_API_URL}`

export const createUser = async ({
  username,
  password,
}: {
  username: string
  password: string
}) => {
  return await PrivateService.createUser({
    requestBody: {
      username,
      password,
      is_verified: true,
      full_name: "Test User",
    },
  })
}
