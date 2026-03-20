# AceReStreamer Frontend Guidelines

React + TypeScript frontend for AceReStreamer video streaming platform.

## Tech Stack

- **React 19** with TypeScript
- **Vite** + SWC for fast builds
- **TanStack Router** (file-based routing)
- **TanStack Query** (server state)
- **Chakra UI v3** (component library)
- **Biome** (linting and formatting)
- **Bun** (package manager and runtime)
- **Playwright** (E2E testing)

## Build Commands

```bash
bun install              # Install dependencies
bun dev                  # Start dev server
bun build                # Production build
bun typecheck            # TypeScript check
bun lint                 # Biome lint/format (auto-fix)
bun generate-client      # Regenerate API client from openapi.json
bun test:e2e             # Run Playwright tests
```

## Architecture Patterns

### API Integration

**Auto-generated client** from OpenAPI spec:
- Run `bun generate-client` after backend schema changes
- Import services: `import { StreamsService, UsersService } from "@/client"`
- All API methods return `CancelablePromise`
- Types auto-generated in `src/client/types.gen.ts`

**Always use with TanStack Query**:
```tsx
// Queries
const { data } = useQuery({
  queryKey: ["streams"],
  queryFn: () => StreamsService.streams()
})

// Mutations - ALWAYS invalidate queries on success
const mutation = useMutation({
  mutationFn: (data) => StreamsService.addStream({ requestBody: data }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["streams"] })
    showSuccessToast("Stream added")
  }
})
```

### Routing

**File-based routing** with TanStack Router:
- Routes map to files in `src/routes/`
- `_layout.tsx` provides wrapper with auth guard
- Route tree auto-generated in `src/routeTree.gen.ts`
- Use `<Link>` from `@tanstack/react-router` for navigation

### Components

**Organization**:
```
src/components/
├── Admin/          # Feature-specific (streams, users, config, etc.)
├── Common/         # Shared layout (Header, Sidebar, NotFound)
├── ui/             # Chakra UI wrapper components
└── [feature]/      # Feature folders (epg, info, etc.)
```

**Chakra UI wrappers**: Use components from `@/components/ui/` (not directly from `@chakra-ui/react`) for buttons, inputs, dialogs, etc.

### Code Style

- **Biome** handles all formatting - don't configure Prettier or ESLint
- Import alias `@/` maps to `src/`
- Use functional components with hooks
- Custom hooks for cross-cutting concerns (see `src/hooks/`)

### Authentication

- Token in `localStorage.getItem("access_token")`
- Use `useAuth()` hook for login/logout/user state
- Global 401/403 handling redirects to `/login`
- No manual auth headers needed (handled by OpenAPI client)

### Error Handling

- Use `handleError()` from `@/utils` for consistent error display
- Use `useCustomToast()` for success/error toasts
- Global error handling at QueryClient level catches auth errors

## Key Conventions

1. **Regenerate client after schema changes**: `bun generate-client`
2. **Always invalidate queries** after mutations for cache freshness
3. **Use generated types** from `@/client` - don't create duplicate types
4. **File-based routes**: Create route files in `src/routes/` - don't manually configure routes
5. **Biome runs on save/commit** - formatting is automatic
6. **Type safety**: Leverage auto-generated types, avoid `any`
7. **Custom hooks**: Extract reusable logic to `src/hooks/`
8. **Codeblock display**: Use `<CodeBlock>` from `@/components/ui/code` for JSON display

## Testing

- **Playwright** for E2E tests in `tests/`
- Auth state managed in `tests/auth.setup.ts`
- Run with `bun test:e2e` or `bun test:e2e:ui` for UI mode
- Store test config in `tests/config.ts`
