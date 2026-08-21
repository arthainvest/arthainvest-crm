export default function DashboardStats({ stats, loading }: { stats: any; loading: boolean }) {
  if (loading) return <div className="text-center py-8">Loading...</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <p className="text-gray-500 text-sm">Total Contacts</p>
        <p className="text-3xl font-bold mt-2">{stats?.totalContacts || 0}</p>
      </div>
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <p className="text-gray-500 text-sm">Total Deals</p>
        <p className="text-3xl font-bold mt-2">{stats?.totalDeals || 0}</p>
      </div>
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <p className="text-gray-500 text-sm">This Month</p>
        <p className="text-3xl font-bold mt-2">{stats?.thisMonth || 0}</p>
      </div>
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <p className="text-gray-500 text-sm">Conversion Rate</p>
        <p className="text-3xl font-bold mt-2">{stats?.conversionRate || '0%'}</p>
      </div>
    </div>
  );
}
