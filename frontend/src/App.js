import React, { useState } from "react";
import axios from "axios";
import { ClipLoader } from "react-spinners";

function App() {
  const [devices, setDevices] = useState({});
  const [loading, setLoading] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [filterText, setFilterText] = useState('');

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const response = await axios.get("http://localhost:5005/api/get_devices");
      setDevices(response.data);
    } catch (error) {
      console.error("Error retrieve devices info:", error);
    }
    setLoading(false);
  };

  const updateDevices = async () => {
    setLoading(true);
    try {
      await axios.post("http://localhost:5005/api/update_devices");
      alert("Aggiornamento avviato!");
    } catch (error) {
      console.error("Error on sync:", error);
      alert("Error on sync.");
    }
    setLoading(false);
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedDevices = Object.entries(devices).sort((a, b) => {
  const [idA, dataA] = a;
  const [idB, dataB] = b;

  if (sortConfig.key === 'id') {
    // Ordina per ID
    if (idA < idB) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (idA > idB) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  } else if (sortConfig.key) {
    // Ordina per altre colonne
    const valueA = dataA[sortConfig.key] || '';
    const valueB = dataB[sortConfig.key] || '';
    if (valueA < valueB) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (valueA > valueB) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
  }
  return 0;
  });

  const filteredDevices = sortedDevices.filter(([id, data]) => {
    return Object.values(data).some(value =>
      String(value).toLowerCase().includes(filterText.toLowerCase())
    );
  });

  return (
    <div className="container mx-auto p-5">
      <h1 className="text-2xl font-bold mb-6">Show Devices</h1>

      <div className="my-6 flex space-x-4">
        <button
          onClick={fetchDevices}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors shadow-md"
        >
          Show devices (cache)
        </button>

        <button
          onClick={updateDevices}
          className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors shadow-md"
        >
          Sync Tuya devices
        </button>
      </div>

      <input
        type="text"
        placeholder="Filter..."
        value={filterText}
        onChange={(e) => setFilterText(e.target.value)}
        className="px-4 py-2 border border-gray-300 rounded-lg mb-4"
      />

      {loading && (
        <div className="flex justify-center items-center my-6">
          <ClipLoader color="#3B82F6" size={35} />
          <p className="ml-3 text-gray-600">Loading...</p>
        </div>
      )}

      {Object.keys(devices).length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-200 mt-4 shadow-lg rounded-lg overflow-hidden">
            <thead>
              <tr className="bg-gray-100">
                <th className="border p-3 text-left cursor-pointer" onClick={() => handleSort('custom_name')}>
                  Device name {sortConfig.key === 'custom_name' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}
                </th>
                <th className="border p-3 text-left cursor-pointer" onClick={() => handleSort('id')}>
                  ID {sortConfig.key === 'id' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}
                </th>
                <th className="border p-3 text-left cursor-pointer" onClick={() => handleSort('local_key')}>
                  Local Key {sortConfig.key === 'local_key' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}
                </th>
                <th className="border p-3 text-left cursor-pointer" onClick={() => handleSort('mac_address')}>
                  MAC Address {sortConfig.key === 'mac_address' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}
                </th>
                <th className="border p-3 text-left cursor-pointer" onClick={() => handleSort('private_ip')}>
                  Private IP {sortConfig.key === 'private_ip' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}
                </th>
                <th className="border p-3 text-left cursor-pointer" onClick={() => handleSort('last_updated')}>
                  Last update {sortConfig.key === 'last_updated' ? (sortConfig.direction === 'asc' ? '▲' : '▼') : ''}
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredDevices.map(([id, data]) => (
                <tr key={id} className="border hover:bg-gray-50 transition-colors">
                  <td className="border p-3">{data.custom_name || "N/A"}</td>
                  <td className="border p-3">{id}</td>
                  <td className="border p-3">{data.local_key}</td>
                  <td className="border p-3">{data.mac_address || "N/A"}</td>
                  <td className="border p-3">{data.private_ip || "N/A"}</td>
                  <td className="border p-3">{data.last_updated || "N/A"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default App;