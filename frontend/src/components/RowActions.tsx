import { Icon } from "./icons";

type Variant = "default" | "primary" | "danger";

const cls: Record<Variant, string> = {
  default: "icon-btn",
  primary: "icon-btn hover:text-primary",
  danger: "icon-btn hover:border-danger hover:text-danger",
};

export function ActionButton({
  icon, title, onClick, variant = "default",
}: { icon: string; title: string; onClick: () => void; variant?: Variant }) {
  return (
    <button className={cls[variant]} title={title} aria-label={title} onClick={onClick}>
      <Icon name={icon} size={16} />
    </button>
  );
}
