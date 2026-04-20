import axios from "axios";
import { clearToken, getToken } from "../utils/auth";

const client = axios.create({
    baseURL: "/api",
    timeout: 20000,
});

client.interceptors.request.use((config) => {
    const token = getToken();
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

client.interceptors.response.use(
    (res) => res,
    (err) => {
        const status = err.response?.status;
        if (status === 401) {
            clearToken();
        }
        return Promise.reject(err);
    }
);

export default client;
