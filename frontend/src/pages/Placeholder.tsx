import { PageHeader } from "../components/PageHeader";

export default function Placeholder({ title }: { title: string }) {
  return (
    <div>
      <PageHeader title={title} subtitle="قيد الإنشاء" />
      <div className="card flex h-64 items-center justify-center text-ink-muted">
        هذه الصفحة قيد الإنشاء
      </div>
    </div>
  );
}
