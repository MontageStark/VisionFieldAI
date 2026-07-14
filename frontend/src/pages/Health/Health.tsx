import PagePlaceholder from '@/components/common/PagePlaceholder';

export default function Health(): JSX.Element {
  return (
    <PagePlaceholder
      title="System Health"
      description="Real-time monitoring of all FieldVision components (camera, vision, tracking, director, motion, servo)."
      bullets={[
        'Per-component status (green / yellow / red)',
        'CPU, GPU, and memory metrics',
        'Last-check timestamps',
        'Critical component alerts',
      ]}
    />
  );
}
