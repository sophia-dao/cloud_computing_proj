
import {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";

import { ToastContext } from "../contexts/toastContext";
import ToastContainer from "../components/common/Toast/ToastContainer";

export default function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([]);
    const nextId = useRef(0);
    const timers = useRef(new Map());

    const removeToast = useCallback((id) => {
        const timer = timers.current.get(id);

        if (timer !== undefined) {
            clearTimeout(timer);
            timers.current.delete(id);
        }

        setToasts((current) =>
            current.filter((toast) => toast.id !== id)
        );
    }, []);

    const showToast = useCallback(
        ({
            type = "info",
            message,
            duration = 4000,
            dismissible = true,
        }) => {
            const id = ++nextId.current;

            setToasts((current) => [
                ...current,
                { id, type, message, dismissible },
            ]);

            if (duration > 0) {
                const timer = setTimeout(() => {
                    removeToast(id);
                }, duration);

                timers.current.set(id, timer);
            }

            return id;
        },
        [removeToast]
    );

    useEffect(() => {
        const activeTimers = timers.current;

        return () => {
            activeTimers.forEach(clearTimeout);
            activeTimers.clear();
        };
    }, []);

    const value = useMemo(
        () => ({ showToast, removeToast }),
        [showToast, removeToast]
    );

    return (
        <ToastContext.Provider value={value}>
            {children}

            <ToastContainer
                toasts={toasts}
                removeToast={removeToast}
            />
        </ToastContext.Provider>
    );
}
