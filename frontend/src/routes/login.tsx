import { Container, Input, Text } from "@chakra-ui/react"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiLock, FiUser } from "react-icons/fi"

import type { Body_Login_login_access_token as AccessToken } from "@/client"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { InputGroup } from "@/components/ui/input-group"
import { PasswordInput } from "@/components/ui/password-input"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"
import { passwordRules, usernamePattern } from "../utils"
import "@fontsource/fira-code/700.css"

export const Route = createFileRoute("/login")({
  component: Login,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
})

function Login() {
  const { loginMutation, error, resetError } = useAuth()
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AccessToken>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  })

  const onSubmit: SubmitHandler<AccessToken> = async (data) => {
    if (isSubmitting) return

    resetError()

    try {
      await loginMutation.mutateAsync(data)
    } catch {
      // error is handled by useAuth hook
    }
  }

  return (
    <Container
      as="form"
      onSubmit={handleSubmit(onSubmit)}
      h="100vh"
      maxW="sm"
      alignItems="stretch"
      justifyContent="center"
      gap={4}
      centerContent
    >
      <Text
        fontFamily="'Fira Code', monospace"
        fontWeight="700"
        fontSize="4xl"
        alignSelf="center"
        p={2}
      >
        AceReStreamer
      </Text>
      <Field
        invalid={!!errors.username}
        errorText={errors.username?.message || !!error}
      >
        <InputGroup w="100%" startElement={<FiUser />}>
          <Input
            {...register("username", {
              required: "Username is required",
              pattern: usernamePattern,
            })}
            placeholder="Username"
            type="text"
          />
        </InputGroup>
      </Field>
      <PasswordInput
        type="password"
        startElement={<FiLock />}
        {...register("password", passwordRules())}
        placeholder="Password"
        errors={errors}
      />
      <Button variant="solid" type="submit" loading={isSubmitting} size="md">
        Log In
      </Button>
    </Container>
  )
}
