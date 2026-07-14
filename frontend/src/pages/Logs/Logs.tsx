import PagePlaceholder from '@/components/common/PagePlaceholder';

export default function Logs(): JSX.Element {
  return (
    <PagePlaceholder
      title="Logs"
      description="Inspect system, application, and event-bus logs with filtering by level and component."
      bullets={[
        'Live-tail log viewer',
        'Filter by level (DEBUG / INFO / WARNING / ERROR)',
        'Filter by component / service',
        'Download log bundles',
      ]}
    />
  );
}
