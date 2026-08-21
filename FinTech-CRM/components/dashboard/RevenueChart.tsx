export default function RevenueChart() {
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold mb-4">Monthly Revenue</h3>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm">Jan</span>
          <div className="flex-1 ml-4 h-6 bg-gradient-to-r from-blue-400 to-blue-600 rounded" style={{width: '60%'}}></div>
          <span className="text-sm font-semibold ml-2">$45K</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm">Feb</span>
          <div className="flex-1 ml-4 h-6 bg-gradient-to-r from-blue-400 to-blue-600 rounded" style={{width: '75%'}}></div>
          <span className="text-sm font-semibold ml-2">$56K</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm">Mar</span>
          <div className="flex-1 ml-4 h-6 bg-gradient-to-r from-blue-400 to-blue-600 rounded" style={{width: '85%'}}></div>
          <span className="text-sm font-semibold ml-2">$64K</span>
        </div>
      </div>
    </div>
  );
}
