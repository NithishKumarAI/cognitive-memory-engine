import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type FormShellProps = {
  children: React.ReactNode;
  description: string;
  onCancel: () => void;
  title: string;
};

export function FormShell({ children, description, onCancel, title }: FormShellProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="space-y-1.5">
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
        <Button aria-label="Close form" onClick={onCancel} size="icon" type="button" variant="ghost">
          <X className="size-4" aria-hidden="true" />
        </Button>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
