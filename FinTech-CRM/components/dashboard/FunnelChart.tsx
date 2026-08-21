export default function FunnelChart() {
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold mb-4">Sales Funnel</h3>
      <div className="space-y-3">
        <div><div className="text-sm font-medium">New Leads</div><div className="w-full bg-blue-600 h-8 rounded">100%</div></div>
        <div><div className="text-sm font-medium">Contacted</div><div className="w-3/4 bg-blue-500 h-8 rounded">75%</div></div>
        <div><div className="text-sm font-medium">Interested</div><div className="w-1/2 bg-blue-400 h-8 rounded">50%</div></div>
        <div><div className="text-sm font-medium">Proposal</div><div className="w-1/3 bg-blue-300 h-8 rounded">33%</div></div>
        <div><div className="text-sm font-medium">Converted</div><div className="w-1/4 bg-blue-200 h-8 rounded">25%</div></div>
      </div>
    </div>
  );
}
