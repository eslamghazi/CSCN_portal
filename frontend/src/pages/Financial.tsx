import { PageHeader } from "../components/PageHeader";
import { Tabs } from "../components/Tabs";
import Transactions from "./financial/Transactions";
import Budget from "./financial/Budget";
import Partnerships from "./financial/Partnerships";

export default function Financial() {
  return (
    <div>
      <PageHeader title="المالية والشراكات" subtitle="المعاملات المالية والميزانية والشراكات والاتفاقيات." />
      <div className="card p-5">
        <Tabs tabs={[
          { key: "txn", label: "المعاملات المالية", content: <Transactions /> },
          { key: "budget", label: "الميزانية", content: <Budget /> },
          { key: "partners", label: "الشراكات", content: <Partnerships /> },
        ]} />
      </div>
    </div>
  );
}
