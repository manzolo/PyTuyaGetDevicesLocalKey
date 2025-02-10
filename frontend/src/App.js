import React, { useState } from "react";
import axios from "axios";
import { ClipLoader } from "react-spinners";

function App() {
  const [devices, setDevices] = useState({});
  const [loading, setLoading] = useState(false);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const response = await axios.get("http://localhost:5005/api/get_devices");
      setDevices(response.data);
    } catch (error) {
      console.error("Errore nel recupero dei dispositivi:", error);
    }
    setLoading(false);
  };

  const updateDevices = async () => {
    setLoading(true);
    try {
      await axios.post("http://localhost:5005/api/update_devices");
      alert("Aggiornamento avviato!");
    } catch (error) {
      console.error("Errore durante l'aggiornamento:", error);
      alert("Errore durante l'aggiornamento.");
    }
    setLoading(false);
  };

  return (
    <div className="container mx-auto p-5">
      <h1 className="text-2xl font-bold mb-6">Visualizza Dispositivi</h1>

      <div className="my-6 flex space-x-4">
        <button
          onClick={fetchDevices}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors shadow-md"
        >
          Visualizza Dispositivi in cache
        </button>

        <button
          onClick={updateDevices}
          className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors shadow-md"
        >
          Scarica Dispositivi da Tuya
        </button>
      </div>

      {loading && (
        <div className="flex justify-center items-center my-6">
          <ClipLoader color="#3B82F6" size={35} />
          <p className="ml-3 text-gray-600">Caricamento...</p>
        </div>
      )}

      {Object.keys(devices).length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-200 mt-4 shadow-lg rounded-lg overflow-hidden">
            <thead>
              <tr className="bg-gray-100">
                <th className="border p-3 text-left">ID</th>
                <th className="border p-3 text-left">Local Key</th>
                <th className="border p-3 text-left">Nome</th>
                <th className="border p-3 text-left">MAC Address</th>
                <th className="border p-3 text-left">IP Privato</th>
                <th className="border p-3 text-left">Ultimo aggiornamento</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(devices).map(([id, data]) => (
                <tr key={id} className="border hover:bg-gray-50 transition-colors">
                  <td className="border p-3">{id}</td>
                  <td className="border p-3">{data.local_key}</td>
                  <td className="border p-3">{data.custom_name || "N/A"}</td>
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