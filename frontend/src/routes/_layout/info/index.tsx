import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/info/")({
  beforeLoad: () => {
    throw redirect({
      to: "/info/iptv",
    })
  },
})
