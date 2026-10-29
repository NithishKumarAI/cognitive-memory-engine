import { redirect } from "next/navigation";
import RegisterPage from "@/components/auth/register-page";

export default function Page() {
  if (process.env.APP_EDITION === "demo") redirect("/dashboard");
  return <RegisterPage />;
}
