import { redirect } from "next/navigation";
import LoginPage from "@/components/auth/login-page";

export default function Page() {
  if (process.env.APP_EDITION === "demo") redirect("/dashboard");
  return <LoginPage />;
}
