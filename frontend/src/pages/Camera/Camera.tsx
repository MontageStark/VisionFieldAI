import PagePlaceholder from '@/components/common/PagePlaceholder';

export default function Camera(): JSX.Element {
  return (
    <PagePlaceholder
      title="Camera Control"
      description="Start/stop the camera module, configure exposure, and inspect the live feed preview."
      bullets={[
        'Start & stop the camera service',
        'View live MJPEG / WebRTC preview',
        'Adjust exposure and resolution',
        'Snapshot capture & download',
      ]}
    />
  );
}
