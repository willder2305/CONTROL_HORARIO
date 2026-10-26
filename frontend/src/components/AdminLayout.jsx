import SessionMonitor from './SessionMonitor';

export default function AdminLayout({ children }) {
  return (
    <>
      <SessionMonitor />
      {children}
    </>
  );
}
