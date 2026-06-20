import * as React from "react";

import { cn } from "@/lib/utils";

const Separator = React.forwardRef<HTMLDivElement, React.ComponentProps<"div">>(
  ({ className, ...props }, ref) => (
    <div className={cn("h-px w-full bg-border", className)} ref={ref} role="separator" {...props} />
  ),
);
Separator.displayName = "Separator";

export { Separator };
