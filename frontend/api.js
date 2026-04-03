const ATTENDANCE_API_BASE = '/kq/api';

function createAttendanceApi(currentUserRef) {
    return async function api(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }

        const response = await fetch(ATTENDANCE_API_BASE + endpoint, { ...options, headers });
        const data = await response.json();

        if (response.status === 401) {
            localStorage.removeItem('token');
            currentUserRef.value = null;
        }

        if (!response.ok) {
            throw new Error(data.detail || '请求失败');
        }

        return data;
    };
}
