import PagePlaceholder from '@/components/common/PagePlaceholder';

export default function Settings(): JSX.Element {
  return (
    <PagePlaceholder
      title="Settings"
      description="Adjust runtime configuration for camera, servo, network, stream, AI, and dashboard modules."
      bullets={[
        'Edit yaml configuration profiles',
        'Hot-reload config without restart',
        'Network & device discovery',
        'Theme preferences',
      ]}
    />
  );
}
