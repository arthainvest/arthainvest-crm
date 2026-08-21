export default function RecentActivities() {
  const activities = [
    { name: 'John Doe', action: 'New Lead', time: '2 hours ago' },
    { name: 'Jane Smith', action: 'Call Connected', time: '4 hours ago' },
    { name: 'Mike Johnson', action: 'Proposal Sent', time: '1 day ago' },
  ];

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold mb-4">Recent Activities</h3>
      <div className="space-y-4">
        {activities.map((activity, i) => (
          <div key={i} className="flex items-center justify-between border-b pb-3">
            <div>
              <p className="font-medium text-sm">{activity.name}</p>
              <p className="text-gray-500 text-xs">{activity.action}</p>
            </div>
            <span className="text-xs text-gray-400">{activity.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
