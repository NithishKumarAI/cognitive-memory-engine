"use client";

import Link from "next/link";
import { BookOpen, Loader2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { branding } from "@/lib/branding";
import { authFeedback } from "@/lib/auth-feedback";
import { ThemeControl } from "@/components/dashboard/theme-control";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import type { LoginPayload } from "@/types/auth";


export default function LoginPage() {
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const { formState: { errors, isSubmitting }, handleSubmit, register } = useForm<LoginPayload>({
    defaultValues: { email: "", password: "" },
  });
  const onSubmit = handleSubmit(async values => {
    setError(null);
    try {
      const redirectTo = new URLSearchParams(window.location.search).get("next") ?? "/dashboard";
      await login(values, redirectTo);
    } catch (caught) {
      setError(authFeedback(caught, "login"));
    }
  });
  return <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-4 py-10">
    <div className="flex w-full max-w-md items-center justify-between gap-4"><Link href="/" className="inline-flex min-h-11 items-center gap-2 font-semibold text-primary"><BookOpen aria-hidden="true" className="size-5" />Back to {branding.name}</Link><ThemeControl /></div>
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-3"><p className="text-xs font-semibold uppercase tracking-widest text-primary">Pick up your next chapter</p><h1 className="text-3xl font-semibold">Sign in</h1><CardDescription>{branding.name} · {branding.description}</CardDescription></CardHeader>
      <CardContent>
        <form className="space-y-5" onSubmit={onSubmit} noValidate aria-busy={isSubmitting}>
          {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}

            <div className="space-y-2"><Label htmlFor="email">Email</Label><Input id="email" type="email" autoComplete="email" aria-invalid={!!errors.email} aria-describedby={errors.email ? "email-error" : undefined} {...register("email", { required: "Email is required.", setValueAs: value => value.trim(), maxLength: { value: 255, message: "Use at most 255 characters." }, pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Enter a valid email address." } })} />{errors.email && <p id="email-error" className="text-sm text-destructive">{errors.email.message}</p>}</div>
            <div className="space-y-2"><Label htmlFor="password">Password</Label><PasswordInput id="password" autoComplete="current-password" aria-invalid={!!errors.password} aria-describedby="password-help password-error" {...register("password", { required: "Password is required." })} /><p id="password-help" className="text-xs text-muted-foreground">Use the password you created for this account.</p><p id="password-error" className="text-sm text-destructive">{errors.password?.message}</p></div>
            <Button className="w-full" disabled={isSubmitting} type="submit">{isSubmitting && <Loader2 className="size-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />}{isSubmitting ? "Signing in…" : "Sign in"}</Button>

          <p className="text-center text-sm text-muted-foreground">New here? <Link className="inline-flex min-h-11 items-center font-medium text-primary hover:underline" href="/register">Create an account</Link></p>
        </form>
      </CardContent>
    </Card>
  </main>;
}
