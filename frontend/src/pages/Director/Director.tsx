import PagePlaceholder from '@/components/common/PagePlaceholder';

export default function Director(): JSX.Element {
  return (
    <PagePlaceholder
      title="Director Mode"
      description="Select between automated camera modes: Broadcast, Aggressive, Wide, Training, and Manual-Assist."
      bullets={[
        'Mode selector (broadcast / aggressive / wide / training / manual_assist)',
        'Latest director decision inspector (pan, tilt, zoom, reasoning)',
        'Confidence timeline',
        'Manual override override',
      ]}
    />
  );
}
