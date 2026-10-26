"use client";

import Link from "next/link";
import { BookOpen, Loader2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { branding } from "@/lib/branding";
import { authFeedback, AccountCreatedError, passwordValidation } from "@/lib/auth-feedback";
import { ThemeControl } from "@/components/dashboard/theme-control";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import type { RegisterPayload } from "@/types/auth";

type SignupValues = RegisterPayload & { confirmPassword: string };

export default function RegisterPage() {
  const { register: createAccount } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState(false);
  const { formState: { errors, isSubmitting }, handleSubmit, register, getValues, resetField } = useForm<SignupValues>({
    defaultValues: { email: "", password: "", username: "", confirmPassword: "" },
  });
  const onSubmit = handleSubmit(async values => {
    setError(null);
    try {
      const redirectTo = new URLSearchParams(window.location.search).get("next") ?? "/dashboard";
      await createAccount({ username: values.username, email: values.email, password: values.password }, redirectTo);
    } catch (caught) {
      if (caught instanceof AccountCreatedError) {
        setCreated(true); resetField("password"); resetField("confirmPassword");
      } else setError(authFeedback(caught, "register"));
    }
  });
  return <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-4 py-10">
    <div className="flex w-full max-w-md items-center justify-between gap-4"><Link href="/" className="inline-flex min-h-11 items-center gap-2 font-semibold text-primary"><BookOpen aria-hidden="true" className="size-5" />Back to {branding.name}</Link><ThemeControl /></div>
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-3"><p className="text-xs font-semibold uppercase tracking-widest text-primary">A little learning, remembered</p><h1 className="text-3xl font-semibold">Create account</h1><CardDescription>{branding.name} · {branding.description}</CardDescription></CardHeader>
      <CardContent>
        <form className="space-y-5" onSubmit={onSubmit} noValidate aria-busy={isSubmitting}>
          {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
          {created ? <div role="status" className="space-y-3 rounded-xl border border-border bg-accent p-4"><p>Your account was created, but automatic sign-in did not finish. Please sign in to continue.</p><Button asChild><Link href="/login">Sign in to your new account</Link></Button></div> : <>
            <div className="space-y-2"><Label htmlFor="username">Username</Label><Input id="username" autoComplete="username" aria-invalid={!!errors.username} aria-describedby={errors.username ? "username-error" : undefined} {...register("username", { required: "Username is required.", setValueAs: value => value.trim(), minLength: { value: 3, message: "Use 3–50 characters." }, maxLength: { value: 50, message: "Use 3–50 characters." } })} />{errors.username && <p id="username-error" className="text-sm text-destructive">{errors.username.message}</p>}</div>
            <div className="space-y-2"><Label htmlFor="email">Email</Label><Input id="email" type="email" autoComplete="email" aria-invalid={!!errors.email} aria-describedby={errors.email ? "email-error" : undefined} {...register("email", { required: "Email is required.", setValueAs: value => value.trim(), maxLength: { value: 255, message: "Use at most 255 characters." }, pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Enter a valid email address." } })} />{errors.email && <p id="email-error" className="text-sm text-destructive">{errors.email.message}</p>}</div>
            <div className="space-y-2"><Label htmlFor="password">Password</Label><PasswordInput id="password" autoComplete="new-password" aria-invalid={!!errors.password} aria-describedby="password-help password-error" {...register("password", { required: "Password is required.", validate: passwordValidation, deps: ["confirmPassword"] })} /><p id="password-help" className="text-xs text-muted-foreground">At least 8 characters; at most 72 UTF-8 bytes. Symbols may use multiple bytes. No blank-only passwords or null characters.</p><p id="password-error" className="text-sm text-destructive">{errors.password?.message}</p></div>
            <div className="space-y-2"><Label htmlFor="confirmPassword">Confirm Password</Label><PasswordInput id="confirmPassword" visibilityLabel="confirm password" autoComplete="new-password" aria-invalid={!!errors.confirmPassword} aria-describedby={errors.confirmPassword ? "confirm-error" : undefined} {...register("confirmPassword", { required: "Please confirm your password.", validate: value => value === getValues("password") || "Passwords do not match." })} />{errors.confirmPassword && <p id="confirm-error" className="text-sm text-destructive">{errors.confirmPassword.message}</p>}</div>
            <Button className="w-full" disabled={isSubmitting} type="submit">{isSubmitting && <Loader2 className="size-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />}{isSubmitting ? "Creating account…" : "Create account"}</Button>
            <p className="text-xs text-muted-foreground">Already submitted this form? Try signing in before creating another account.</p></>}
          <p className="text-center text-sm text-muted-foreground">Already have an account? <Link className="inline-flex min-h-11 items-center font-medium text-primary hover:underline" href="/login">Sign in</Link></p>
        </form>
      </CardContent>
    </Card>
  </main>;
}
