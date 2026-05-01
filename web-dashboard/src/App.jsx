import { useState, useEffect } from 'react'
import { supabase } from './supabaseClient'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

// Daftar warna untuk garis grafik tiap device
const COLORS = ['#60a5fa', '#34d399', '#f472b6', '#fbbf24', '#a78bfa']

export default function App() {
  const [chartData, setChartData] = useState([])
  
  // PERBAIKAN: State ini sekarang menyimpan object berisi temp, cpu, dan ram
  const [latestData, setLatestData] = useState({}) 
  const [deviceList, setDeviceList] = useState([])

  useEffect(() => {
    fetchData()

    // Real-time listener Supabase
    const subscription = supabase
      .channel('public:temperature_logs')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'temperature_logs' }, payload => {
        const newData = payload.new
        
        // Update data terakhir untuk device tersebut (Suhu, CPU, RAM)
        setLatestData(prev => ({
          ...prev,
          [newData.device_name]: {
            temp: newData.temperature,
            cpu: newData.cpu_usage,
            ram: newData.ram_usage
          }
        }))

        // Update list device jika ada device baru yang belum terdaftar
        setDeviceList(prev => {
          if (!prev.includes(newData.device_name)) return [...prev, newData.device_name]
          return prev
        })

        // Fetch ulang data grafik
        fetchData()
      })
      .subscribe()

    return () => {
      supabase.removeChannel(subscription)
    }
  }, [])

  const fetchData = async () => {
    // Ambil 50 data terakhir dari semua device
    const { data, error } = await supabase
      .from('temperature_logs')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(50)

    if (error) {
      console.error('Error fetching data:', error)
      return
    }

    const reversedData = data.reverse()
    
    // Proses Data
    const groupedData = {}
    const latest = {}
    const devices = new Set()

    reversedData.forEach(log => {
      // Format jam:menit
      const date = new Date(log.created_at)
      const timeStr = `${date.getHours()}:${date.getMinutes() < 10 ? '0' : ''}${date.getMinutes()}`
      
      if (!groupedData[timeStr]) {
        groupedData[timeStr] = { time: timeStr }
      }
      
      // Data untuk grafik utama (Suhu)
      groupedData[timeStr][log.device_name] = log.temperature
      
      // Menyimpan data CPU dan RAM juga di grouping (berguna kalau mau bikin grafik CPU/RAM nanti)
      groupedData[timeStr][`${log.device_name}_cpu`] = log.cpu_usage
      groupedData[timeStr][`${log.device_name}_ram`] = log.ram_usage
      
      // Update data terakhir
      latest[log.device_name] = {
        temp: log.temperature,
        cpu: log.cpu_usage,
        ram: log.ram_usage
      }
      devices.add(log.device_name)
    })

    setChartData(Object.values(groupedData))
    setLatestData(latest)
    setDeviceList(Array.from(devices))
  }

  return (
    <div className="min-h-screen p-8 flex flex-col items-center">
      <h1 className="text-3xl font-bold mb-8 text-blue-400">System Resource Monitor</h1>
      
      {/* KARTU INDIKATOR (Suhu, CPU, RAM) */}
      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {deviceList.length === 0 && <p className="text-gray-400">Menunggu data masuk...</p>}
        
        {deviceList.map((device, index) => {
          // Mengambil data dari state latestData
          const current = latestData[device] || {}
          
          // Memastikan ada nilai, jika null/undefined maka tampilkan '--'
          const temp = current.temp !== undefined && current.temp !== null ? Number(current.temp).toFixed(1) : '--'
          const cpu = current.cpu !== undefined && current.cpu !== null ? Number(current.cpu).toFixed(1) : '--'
          const ram = current.ram !== undefined && current.ram !== null ? Number(current.ram).toFixed(1) : '--'

          return (
            <div key={device} className="bg-slate-800 p-6 rounded-2xl shadow-lg border border-slate-700 flex flex-col relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
              
              <h2 className="text-gray-400 text-sm uppercase tracking-wider mb-2">{device}</h2>
              
              {/* Grid 3 Kolom untuk Metrik */}
              <div className="grid grid-cols-3 gap-2 mt-2">
                 <div>
                    <p className="text-xs text-gray-500">TEMP</p>
                    <p className="text-2xl font-black text-white">{temp}°C</p>
                 </div>
                 <div>
                    <p className="text-xs text-gray-500">CPU</p>
                    <p className="text-2xl font-black text-blue-400">{cpu}%</p>
                 </div>
                 <div>
                    <p className="text-xs text-gray-500">RAM</p>
                    <p className="text-2xl font-black text-purple-400">{ram}%</p>
                 </div>
              </div>

              <p className="text-green-400 mt-4 text-xs flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                Online
              </p>
            </div>
          )
        })}
      </div>

      {/* GRAFIK SUHU */}
      <div className="bg-slate-800 p-6 rounded-2xl shadow-lg border border-slate-700 w-full max-w-5xl h-96">
        <h3 className="text-gray-400 text-sm mb-4">Temperature History</h3>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="time" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }}
            />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ paddingBottom: '10px' }}/>
            
            {deviceList.map((device, index) => (
              <Line 
                key={device}
                type="monotone" 
                dataKey={device} 
                name={`${device} Temp`}
                stroke={COLORS[index % COLORS.length]} 
                strokeWidth={3} 
                dot={{ r: 4, fill: COLORS[index % COLORS.length] }} 
                activeDot={{ r: 8 }}
                connectNulls={true} 
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}