type Tone = "success" | "warning" | "danger" | "info" | "muted";

const cls: Record<Tone, string> = {
  success: "badge-success",
  warning: "badge-warning",
  danger: "badge-danger",
  info: "badge-info",
  muted: "badge-muted",
};

export function Badge({ text, tone = "muted" }: { text: string; tone?: Tone }) {
  return <span className={cls[tone]}>{text}</span>;
}
