import ComplaintCard from "./ComplaintCard";
import "../styles/ComplaintList.css";

export default function ComplaintList() {
  const complaints = [
    { id: 1, text: "Refund not received", category: "Billing", priority: "High" },
    { id: 2, text: "App crashes", category: "Technical", priority: "Medium" }
  ];

  return (
    <div className="complaint-list">
      <h2>Recent Complaints (Demo)</h2>
      {complaints.map(c => (
        <ComplaintCard key={c.id} complaint={c} />
      ))}
    </div>
  );
}
