import React from "react";
type Props = { open: boolean; onClose: () => void; title: string; children: React.ReactNode; footer?: React.ReactNode; };
export default function Modal({ open, onClose, title, children, footer }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative w-full max-w-lg mx-4 rounded-xl bg-white shadow-lg">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-semibold">{title}</h3>
          <button onClick={onClose} className="px-2 text-slate-500 hover:text-slate-900">✕</button>
        </div>
        <div className="p-4">{children}</div>
        {footer && <div className="p-4 border-t flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  );
}
