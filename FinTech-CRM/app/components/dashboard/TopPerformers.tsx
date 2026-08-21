export default function TopPerformers() {
  const performers = [
    { name: 'Artha', deals: 12, conversion: '85%' },
    { name: 'Employee 1', deals: 8, conversion: '72%' },
    { name: 'Employee 2', deals: 6, conversion: '65%' },
  ];

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold mb-4">Top Performers</h3>
      <div className="space-y-3">
        {performers.map((perf, i) => (
          <div key={i} className="flex items-center justify-between">
            <div>
              <p className="font-medium text-sm">{perf.name}</p>
              <p className="text-gray-500 text-xs">{perf.deals} deals</p>
            </div>
            <div className="text-right">
              <p className="font-semibold text-sm">{perf.conversion}</p>
              <p className="text-gray-500 text-xs">conversion</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
