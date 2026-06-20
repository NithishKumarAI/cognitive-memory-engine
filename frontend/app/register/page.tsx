"use client";

import Link from "next/link";
import { AxiosError } from "axios";
import { Brain, Loader2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import type { RegisterPayload } from "@/types/auth";

export default function RegisterPage() {
  const { register: createAccount } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
  } = useForm<RegisterPayload>({
    defaultValues: {
      email: "",
      password: "",
      username: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    setError(null);

    try {
      const redirectTo = new URLSearchParams(window.location.search).get("next") ?? "/dashboard";
      await createAccount(values, redirectTo);
    } catch (caughtError) {
      const message =
        caughtError instanceof AxiosError
          ? caughtError.response?.data?.detail ?? "Unable to create your account."
          : "Unable to create your account.";
      setError(message);
    }
  });

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted px-4 py-10">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-4">
          <div className="flex size-11 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Brain className="size-5" aria-hidden="true" />
          </div>
          <div>
            <CardTitle>Create account</CardTitle>
            <CardDescription>Start building your adaptive learning memory.</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form className="space-y-5" onSubmit={onSubmit}>
            {error ? (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                autoComplete="username"
                id="username"
                {...register("username", {
                  minLength: {
                    message: "Username must be at least 3 characters.",
                    value: 3,
                  },
                  required: "Username is required.",
                })}
              />
              {errors.username ? (
                <p className="text-sm text-destructive">{errors.username.message}</p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                autoComplete="email"
                id="email"
                type="email"
                {...register("email", {
                  pattern: {
                    message: "Enter a valid email address.",
                    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  },
                  required: "Email is required.",
                })}
              />
              {errors.email ? <p className="text-sm text-destructive">{errors.email.message}</p> : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                autoComplete="new-password"
                id="password"
                type="password"
                {...register("password", {
                  minLength: {
                    message: "Password must be at least 8 characters.",
                    value: 8,
                  },
                  required: "Password is required.",
                })}
              />
              {errors.password ? (
                <p className="text-sm text-destructive">{errors.password.message}</p>
              ) : null}
            </div>

            <Button className="w-full" disabled={isSubmitting} type="submit">
              {isSubmitting ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : null}
              Create account
            </Button>

            <p className="text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link className="font-medium text-primary hover:underline" href="/login">
                Sign in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
