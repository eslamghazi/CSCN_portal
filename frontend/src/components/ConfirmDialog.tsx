import { Modal } from "./Modal";

interface ConfirmProps {
  open: boolean;
  title?: string;
  message: string;
  danger?: boolean;
  confirmText?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open, title = "تأكيد", message, danger = true,
  confirmText = "تأكيد", onConfirm, onCancel,
}: ConfirmProps) {
  return (
    <Modal open={open} title={title} onClose={onCancel} width="max-w-md"
      footer={
        <>
          <button className={danger ? "btn-danger" : "btn-primary"} onClick={onConfirm}>{confirmText}</button>
          <button className="btn-secondary" onClick={onCancel}>إلغاء</button>
        </>
      }>
      <p className="text-sm leading-7 text-ink-secondary">{message}</p>
    </Modal>
  );
}
