import { Loader2 } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type EntityTableColumn<T> = {
  key: string;
  header: string;
  className?: string;
  render: (item: T) => React.ReactNode;
};

type EntityTableProps<T> = {
  columns: EntityTableColumn<T>[];
  data: T[];
  emptyMessage: string;
  getRowKey: (item: T) => string | number;
  isLoading?: boolean;
};

export function EntityTable<T>({
  columns,
  data,
  emptyMessage,
  getRowKey,
  isLoading = false,
}: EntityTableProps<T>) {
  if (isLoading) {
    return (
      <Card className="flex min-h-56 items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Loading" />
      </Card>
    );
  }

  if (data.length === 0) {
    return (
      <Card className="flex min-h-56 items-center justify-center px-6 text-center text-sm text-muted-foreground">
        {emptyMessage}
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-muted/70 text-xs uppercase text-muted-foreground">
            <tr>
              {columns.map((column) => (
                <th className={cn("px-4 py-3 font-medium", column.className)} key={column.key}>
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {data.map((item) => (
              <tr className="bg-card transition-colors hover:bg-muted/40" key={getRowKey(item)}>
                {columns.map((column) => (
                  <td className={cn("px-4 py-3 align-top", column.className)} key={column.key}>
                    {column.render(item)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
