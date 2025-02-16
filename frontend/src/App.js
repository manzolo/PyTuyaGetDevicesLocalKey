import React, { useState, useEffect } from "react";
import axios from "axios";
import { ClipLoader } from "react-spinners";

// Componente per il messaggio di errore
const ErrorMessage = ({ message, onClose }) => {
  return (
    <div id="alert-border-2" className="flex items-center p-4 mb-4 text-red-800 border-t-4 border-red-300 bg-red-50 dark:text-red-400 dark:bg-gray-800 dark:border-red-800" role="alert">
      <svg className="shrink-0 w-4 h-4" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
        <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z"/>
      </svg>
      <div className="ms-3 text-sm font-medium">
        {message}
      </div>
      <button
        type="button"
        className="ms-auto -mx-1.5 -my-1.5 bg-red-50 text-red-500 rounded-lg focus:ring-2 focus:ring-red-400 p-1.5 hover:bg-red-200 inline-flex items-center justify-center h-8 w-8 dark:bg-gray-800 dark:text-red-400 dark:hover:bg-gray-700"
        onClick={onClose}
        aria-label="Close"
      >
        <span className="sr-only">Dismiss</span>
        <svg className="w-3 h-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
          <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"/>
        </svg>
      </button>
    </div>
  );
};
// Componente per il messaggio di errore
const InfoMessage = ({ message, onClose }) => {
  return (
    <div id="alert-border-1" class="flex items-center p-4 mb-4 text-blue-800 border-t-4 border-blue-300 bg-blue-50 dark:text-blue-400 dark:bg-gray-800 dark:border-blue-800" role="alert">
        <svg class="shrink-0 w-4 h-4" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z"/>
        </svg>
        <div class="ms-3 text-sm font-medium">
        {message}
      </div>
      <button
        type="button"
        className="ms-auto -mx-1.5 -my-1.5 bg-red-50 text-red-500 rounded-lg focus:ring-2 focus:ring-red-400 p-1.5 hover:bg-red-200 inline-flex items-center justify-center h-8 w-8 dark:bg-gray-800 dark:text-red-400 dark:hover:bg-gray-700"
        onClick={onClose}
        aria-label="Close"
      >
        <span className="sr-only">Dismiss</span>
        <svg className="w-3 h-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
          <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"/>
        </svg>
      </button>
    </div>
  );
};

function App() {
  const [devices, setDevices] = useState({});
  const [loading, setLoading] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [filterText, setFilterText] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [infoMessage, setInfoMessage] = useState('');

  // Timer per nascondere il messaggio di errore
  useEffect(() => {
    if (errorMessage) {
      const timer = setTimeout(() => {
        setErrorMessage('');
      }, 10000); // Nasconde il messaggio dopo 10 secondi

      return () => clearTimeout(timer); // Pulisci il timer se il componente viene smontato o se cambia il messaggio
    }
  }, [errorMessage]);
  
  // Timer per nascondere il messaggio di errore
  useEffect(() => {
    if (infoMessage) {
      const timer = setTimeout(() => {
        setInfoMessage('');
      }, 2000); // Nasconde il messaggio dopo 5 secondi

      return () => clearTimeout(timer); // Pulisci il timer se il componente viene smontato o se cambia il messaggio
    }
  }, [infoMessage]);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      setErrorMessage("");
      const response = await axios.get("/api/get_devices");
      setDevices(response.data);
    } catch (error) {
      console.error("Error retrieve devices info:", error);
      if (error.response) {
        setErrorMessage("Error retrieve devices info: " + error.response.data.error);
      } else if (error.request) {
        setErrorMessage("No response received: " + error.message);
      } else {
        setErrorMessage("Error: " + error.message);
      }
    }
    setLoading(false);
  };

    const updateDevices = async () => {
      setLoading(true); // Imposta lo stato di caricamento
      setErrorMessage(""); // Resetta il messaggio di errore
      setInfoMessage(""); // Resetta il messaggio informativo

      try {
        // Effettua la chiamata POST
        const response = await axios.post("/api/update_devices");

        // Verifica che la risposta sia valida
        if (response.status === 200) {
          setInfoMessage("Update is complete!"); // Mostra un messaggio di successo
        } else {
          // Se la risposta non è 200, gestisci l'errore
          setErrorMessage("Unexpected error: " + response.statusText);
        }
      } catch (error) {
        console.error("Sync error:", error);

        // Gestisci diversi tipi di errori
        if (error.response) {
          // Errore con risposta dal server (es. 4xx, 5xx)
          setErrorMessage("Sync error: " + error.response.data.error);
        } else if (error.request) {
          // Nessuna risposta ricevuta (es. problemi di rete)
          setErrorMessage("No server response: " + error.message);
        } else {
          // Errore generico (es. configurazione della richiesta)
          setErrorMessage("Error: " + error.message);
        }
      } finally {
        setLoading(false); // Disattiva lo stato di caricamento
      }
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
      if (idA < idB) return sortConfig.direction === 'asc' ? -1 : 1;
      if (idA > idB) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    } else if (sortConfig.key) {
      const valueA = dataA[sortConfig.key] || '';
      const valueB = dataB[sortConfig.key] || '';
      if (valueA < valueB) return sortConfig.direction === 'asc' ? -1 : 1;
      if (valueA > valueB) return sortConfig.direction === 'asc' ? 1 : -1;
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

      {errorMessage && (
        <ErrorMessage message={errorMessage} onClose={() => setErrorMessage('')} />
      )}
      
      {infoMessage && (
        <InfoMessage message={infoMessage} onClose={() => setInfoMessage('')} />
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