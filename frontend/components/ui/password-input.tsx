"use client";

import { forwardRef, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export const PasswordInput = forwardRef<HTMLInputElement, React.ComponentProps<typeof Input> & { visibilityLabel?: string }>(
  ({ visibilityLabel = "password", className = "", ...props }, ref) => {
    const [visible, setVisible] = useState(false);
    return <div className="relative">
      <Input {...props} ref={ref} type={visible ? "text" : "password"} className={`pr-14 ${className}`} />
      <Button type="button" variant="ghost" size="icon" className="absolute right-0 top-0" aria-label={`${visible ? "Hide" : "Show"} ${visibilityLabel}`} aria-pressed={visible} aria-controls={props.id} disabled={props.disabled} onClick={() => setVisible(value => !value)}>
        {visible ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}
      </Button>
    </div>;
  },
);
PasswordInput.displayName = "PasswordInput";
