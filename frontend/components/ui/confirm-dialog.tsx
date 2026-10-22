"use client";
import { useEffect, useRef, useState } from "react";
import { Button } from "./button";
type Request = { description: string; resolve: (value: boolean) => void };
function Confirmation({ request, close }: { request: Request; close: (value: boolean) => void }) {
 const dialog = useRef<HTMLDialogElement>(null);
 useEffect(() => { const element = dialog.current; element?.showModal(); return () => { element?.close(); }; }, [request]);
 return <dialog ref={dialog} aria-labelledby="confirm-title" aria-describedby="confirm-description" onCancel={event => { event.preventDefault(); close(false); }}><h2 id="confirm-title" className="text-xl font-semibold">Before you delete</h2><p id="confirm-description" className="mt-3 text-sm text-muted-foreground">{request.description}</p><div className="mt-6 flex flex-wrap justify-end gap-2"><Button autoFocus variant="outline" onClick={() => close(false)}>Keep it</Button><Button variant="destructive" onClick={() => close(true)}>Delete</Button></div></dialog>;
}
export function useConfirmDialog() {
 const [request, setRequest] = useState<Request | null>(null);
 function confirm(description: string) { return new Promise<boolean>(resolve => setRequest({ description, resolve })); }
 function close(value: boolean) { request?.resolve(value); setRequest(null); }
 return { confirm, dialog: request ? <Confirmation request={request} close={close} /> : null };
}
