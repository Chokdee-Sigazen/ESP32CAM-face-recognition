import { useState, useEffect } from 'react';
import axios from 'axios';
import { Clock, Users, UserCheck, UserX } from 'lucide-react';

const SHEET_ID = '10FQFSd_EPppbvJK0ai4kUvCYLvANtKc5-S65T81RmGQ';
const API_KEY = 'AIzaSyCVyArQwGW5_7zkgT9d1ooemIQb15XDLuE';

export default function Dashboard() {
  const [data, setData] = useState({ employees: [], attendance: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uniqueEmployeeNames] = useState(new Map());

  const fetchSheetData = async () => {
    try {
      // Fetch Employees data
      const employeesResponse = await axios.get(
        `https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/Employees!A2:D?key=${API_KEY}`
      );

      // Fetch Attendance data
      const attendanceResponse = await axios.get(
        `https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/Attendance!A2:D?key=${API_KEY}`
      );

      const employees = employeesResponse.data.values?.map(row => ({
        id: row[0],
        name: row[1],
        department: row[2],
        status: row[3]
      })) || [];

      const attendance = attendanceResponse.data.values?.map(row => {
        const employeeId = row[2];
        const employeeName = row[3];
        if (!uniqueEmployeeNames.has(employeeName)) {
          uniqueEmployeeNames.set(employeeName, employeeId);
        }
        return {
          date: row[0],
          time: row[1],
          employeeId,
          name: employeeName
        };
      }) || [];

      setData({ employees, attendance });
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load data from Google Sheets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSheetData();
    const interval = setInterval(fetchSheetData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-red-600">{error}</div>
      </div>
    );
  }

  const today = new Date().toLocaleDateString();
  const todayAttendance = data.attendance.filter(record =>
    new Date(record.date).toLocaleDateString() === today
  );

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Attendance Dashboard</h1>
          <div className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-gray-500" />
            <span className="text-gray-600">{today}</span>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Users className="h-10 w-10 text-blue-500" />
              <div className="ml-4">
                <h3 className="text-gray-500 text-sm">Total Employees</h3>
                <p className="text-2xl font-bold">{data.employees.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <UserCheck className="h-10 w-10 text-green-500" />
              <div className="ml-4">
                <h3 className="text-gray-500 text-sm">Present Today</h3>
                <p className="text-2xl font-bold text-green-600">
                  {todayAttendance.filter(record => uniqueEmployeeNames.has(record.name)).length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <UserX className="h-10 w-10 text-red-500" />
              <div className="ml-4">
                <h3 className="text-gray-500 text-sm">Absent Today</h3>
                <p className="text-2xl font-bold text-red-600">
                  {data.employees.length - todayAttendance.filter(record => uniqueEmployeeNames.has(record.name)).length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Today's Attendance */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold">Today Attendance</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    TIME
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    EMPLOYEE ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    NAME
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {todayAttendance
                  .filter(record => uniqueEmployeeNames.has(record.name))
                  .map((record, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.time}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {uniqueEmployeeNames.get(record.name)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.name}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Employee List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold">Employee List</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Department
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.employees.map((employee) => (
                  <tr key={employee.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {employee.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {employee.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {employee.department}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        employee.status === 'Yes'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {employee.status === 'Yes' ? 'Present' : 'Absent'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}